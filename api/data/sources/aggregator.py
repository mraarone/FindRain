# api/data/aggregator.py
import asyncio
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
import logging
from collections import defaultdict

from .sources.base import BaseDataSource, DataSourceStatus
from .sources.yfinance_source import YFinanceSource
from .sources.robin_stocks_source import RobinStocksSource
from ..utils.cache import CacheManager
from ..database.models import DataDownload, MarketData, db

logger = logging.getLogger(__name__)

class DataAggregator:
    """Aggregates data from multiple sources with intelligent failover"""
    
    def __init__(self, cache_manager: CacheManager, config: Dict[str, Any]):
        self.cache = cache_manager
        self.config = config
        self.sources: List[BaseDataSource] = []
        self._initialize_sources()
        self.health_check_interval = 300  # 5 minutes
        self._start_health_monitoring()
        
    def _initialize_sources(self):
        """Initialize configured data sources"""
        source_classes = {
            'yfinance': YFinanceSource,
            'robin_stocks': RobinStocksSource,
            # Add other sources here
        }
        
        for source_name, source_config in self.config['DATA_SOURCES'].items():
            if source_config.get('enabled') and source_name in source_classes:
                try:
                    source_class = source_classes[source_name]
                    source = source_class()
                    source.priority = source_config.get('priority', 999)
                    self.sources.append(source)
                    logger.info(f"Initialized data source: {source_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize {source_name}: {e}")
        
        # Sort sources by priority
        self.sources.sort(key=lambda x: x.priority)
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        asyncio.create_task(self._health_monitor())
    
    async def _health_monitor(self):
        """Monitor health of all data sources"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                for source in self.sources:
                    await source.health_check()
                    logger.info(f"Health check for {source.name}: {source.status.value}")
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    def _get_healthy_sources(self) -> List[BaseDataSource]:
        """Get list of healthy sources sorted by priority"""
        return [
            source for source in self.sources
            if source.status != DataSourceStatus.UNHEALTHY
        ]
    
    async def get_quote(self, symbol: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get quote with failover across sources"""
        # Check cache first
        if use_cache:
            cached = await self.cache.get(f"quote:{symbol}")
            if cached:
                return cached
        
        # Try each healthy source
        for source in self._get_healthy_sources():
            try:
                logger.info(f"Trying {source.name} for quote {symbol}")
                result = await source.get_quote(symbol)
                if result:
                    # Cache the result
                    await self.cache.set(
                        f"quote:{symbol}",
                        result,
                        timeout=self.config['CACHE_STRATEGIES']['quotes']['timeout']
                    )
                    return result
            except Exception as e:
                logger.error(f"Error getting quote from {source.name}: {e}")
                source.record_error()
        
        logger.warning(f"Failed to get quote for {symbol} from all sources")
        return None
    
    async def get_historical(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
        use_cache: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical data with smart downloading and caching"""
        
        # Check if we already have this data
        if use_cache:
            existing = await self._check_existing_data(symbol, start_date, end_date, interval)
            if existing:
                logger.info(f"Using cached data for {symbol}")
                return existing
        
        # Download from sources
        for source in self._get_healthy_sources():
            try:
                logger.info(f"Downloading historical data from {source.name} for {symbol}")
                
                # Get maximum granularity
                download_interval = self._get_download_interval(interval)
                
                result = await source.get_historical(
                    symbol, start_date, end_date, download_interval
                )
                
                if result:
                    # Save to database
                    await self._save_historical_data(result, symbol, source.name)
                    
                    # Record download
                    await self._record_download(
                        symbol, source.name, start_date, end_date, download_interval
                    )
                    
                    # Aggregate to requested interval if needed
                    if download_interval != interval:
                        result = self._aggregate_data(result, interval)
                    
                    return result
                    
            except Exception as e:
                logger.error(f"Error getting historical from {source.name}: {e}")
                source.record_error()
        
        return None
    
    async def _check_existing_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Check if we already have the requested data"""
        try:
            # Query TimescaleDB for existing data
            query = db.session.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.time >= start_date,
                MarketData.time <= end_date
            ).order_by(MarketData.time)
            
            data = query.all()
            if not data:
                return None
            
            # Convert to dict format
            result = []
            for row in data:
                result.append({
                    'timestamp': row.time.isoformat(),
                    'open': float(row.open),
                    'high': float(row.high),
                    'low': float(row.low),
                    'close': float(row.close),
                    'volume': int(row.volume),
                    'symbol': row.symbol,
                    'source': row.source
                })
            
            # Aggregate if needed
            if interval != "1m":  # Assuming data is stored at 1m granularity
                result = self._aggregate_data(result, interval)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking existing data: {e}")
            return None
    
    def _get_download_interval(self, requested_interval: str) -> str:
        """Get the best download interval (maximum granularity)"""
        # Always try to download at highest granularity
        interval_priority = ["1s", "1m", "5m", "15m", "30m", "1h", "1d"]
        
        # Find the index of requested interval
        try:
            requested_idx = interval_priority.index(requested_interval)
        except ValueError:
            requested_idx = len(interval_priority) - 1
        
        # Return the finest granularity available
        return interval_priority[0] if requested_idx > 0 else requested_interval
    
    def _aggregate_data(self, data: List[Dict[str, Any]], target_interval: str) -> List[Dict[str, Any]]:
        """Aggregate data to target interval"""
        if not data:
            return data
        
        # Define interval mappings in minutes
        interval_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "1d": 1440
        }
        
        target_minutes = interval_minutes.get(target_interval, 1440)
        
        # Group data by time periods
        aggregated = defaultdict(list)
        for point in data:
            timestamp = datetime.fromisoformat(point['timestamp'])
            # Round down to target interval
            period = timestamp.replace(
                minute=(timestamp.minute // target_minutes) * target_minutes,
                second=0,
                microsecond=0
            )
            aggregated[period].append(point)
        
        # Aggregate each period
        result = []
        for period, points in sorted(aggregated.items()):
            if not points:
                continue
                
            agg_point = {
                'timestamp': period.isoformat(),
                'open': points[0]['open'],
                'high': max(p['high'] for p in points),
                'low': min(p['low'] for p in points),
                'close': points[-1]['close'],
                'volume': sum(p['volume'] for p in points),
                'symbol': points[0]['symbol'],
                'source': points[0]['source']
            }
            result.append(agg_point)
        
        return result
    
    async def _save_historical_data(self, data: List[Dict[str, Any]], symbol: str, source: str):
        """Save historical data to TimescaleDB"""
        try:
            for point in data:
                market_data = MarketData(
                    time=datetime.fromisoformat(point['timestamp']),
                    symbol=symbol,
                    open=point['open'],
                    high=point['high'],
                    low=point['low'],
                    close=point['close'],
                    volume=point['volume'],
                    source=source
                )
                db.session.add(market_data)
            
            db.session.commit()
            logger.info(f"Saved {len(data)} data points for {symbol}")
            
        except Exception as e:
            logger.error(f"Error saving historical data: {e}")
            db.session.rollback()
    
    async def _record_download(
        self,
        symbol: str,
        source: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str
    ):
        """Record data download for tracking"""
        try:
            download = DataDownload(
                symbol=symbol,
                source=source,
                start_time=start_date,
                end_time=end_date,
                granularity=granularity
            )
            db.session.add(download)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error recording download: {e}")
            db.session.rollback()
    
    async def get_options_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get options chain with failover"""
        for source in self._get_healthy_sources():
            try:
                result = await source.get_options_chain(symbol)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error getting options from {source.name}: {e}")
                source.record_error()
        
        return None
    
    async def get_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get crypto data with failover"""
        for source in self._get_healthy_sources():
            try:
                result = await source.get_crypto_data(symbol)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error getting crypto from {source.name}: {e}")
                source.record_error()
        
        return None