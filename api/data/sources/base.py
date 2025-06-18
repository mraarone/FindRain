# api/data/sources/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class DataSourceStatus(Enum):
    """Data source health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class BaseDataSource(ABC):
    """Base class for all data sources"""
    
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority
        self.status = DataSourceStatus.HEALTHY
        self.last_health_check = datetime.utcnow()
        self.error_count = 0
        self.success_count = 0
        
    @abstractmethod
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a symbol"""
        pass
    
    @abstractmethod
    async def get_historical(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical price data"""
        pass
    
    @abstractmethod
    async def get_options_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get options chain for a symbol"""
        pass
    
    @abstractmethod
    async def get_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cryptocurrency data"""
        pass
    
    async def health_check(self) -> DataSourceStatus:
        """Check health of the data source"""
        try:
            # Try to get a quote for a common symbol
            result = await self.get_quote("AAPL")
            if result:
                self.status = DataSourceStatus.HEALTHY
                self.error_count = 0
            else:
                self.status = DataSourceStatus.DEGRADED
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            self.error_count += 1
            if self.error_count >= 3:
                self.status = DataSourceStatus.UNHEALTHY
            else:
                self.status = DataSourceStatus.DEGRADED
        
        self.last_health_check = datetime.utcnow()
        return self.status
    
    def record_success(self):
        """Record successful operation"""
        self.success_count += 1
        if self.success_count > 10 and self.status != DataSourceStatus.HEALTHY:
            self.status = DataSourceStatus.HEALTHY
            self.error_count = 0
    
    def record_error(self):
        """Record failed operation"""
        self.error_count += 1
        if self.error_count >= 3:
            self.status = DataSourceStatus.UNHEALTHY
        elif self.error_count >= 1:
            self.status = DataSourceStatus.DEGRADED


