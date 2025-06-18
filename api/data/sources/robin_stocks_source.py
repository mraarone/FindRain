# api/data/sources/robin_stocks_source.py
import robin_stocks.robinhood as rh
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from .base import BaseDataSource

class RobinStocksSource(BaseDataSource):
    """Robin Stocks (Robinhood) data source implementation"""
    
    def __init__(self, username: str = None, password: str = None):
        super().__init__("robin_stocks", priority=2)
        self.username = username
        self.password = password
        self.logged_in = False
        
    async def _ensure_login(self):
        """Ensure we're logged in to Robinhood"""
        if not self.logged_in and self.username and self.password:
            try:
                rh.login(self.username, self.password)
                self.logged_in = True
            except Exception as e:
                logger.error(f"Robin Stocks login error: {e}")
                self.record_error()
                
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from Robinhood"""
        try:
            await self._ensure_login()
            
            # Get quote data
            quote_data = rh.stocks.get_latest_price(symbol)
            if not quote_data or not quote_data[0]:
                return None
                
            # Get additional info
            fundamentals = rh.stocks.get_fundamentals(symbol)
            if fundamentals and fundamentals[0]:
                fund = fundamentals[0]
            else:
                fund = {}
            
            quote = {
                'symbol': symbol,
                'price': float(quote_data[0]),
                'open': float(fund.get('open', 0)),
                'high': float(fund.get('high', 0)),
                'low': float(fund.get('low', 0)),
                'volume': int(fund.get('volume', 0)),
                'previousClose': float(fund.get('previous_close', 0)),
                'marketCap': float(fund.get('market_cap', 0)),
                'pe': float(fund.get('pe_ratio', 0)) if fund.get('pe_ratio') else None,
                'timestamp': datetime.utcnow().isoformat(),
                'source': self.name
            }
            
            self.record_success()
            return quote
            
        except Exception as e:
            logger.error(f"Robin Stocks quote error for {symbol}: {e}")
            self.record_error()
            return None
    
    async def get_historical(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical data from Robinhood"""
        try:
            await self._ensure_login()
            
            # Map intervals
            interval_map = {
                "1m": "5minute",
                "5m": "5minute",
                "10m": "10minute",
                "1h": "hour",
                "1d": "day",
                "1w": "week"
            }
            
            rh_interval = interval_map.get(interval, "day")
            
            # Calculate span
            delta = end_date - start_date
            if delta.days <= 1:
                span = "day"
            elif delta.days <= 7:
                span = "week"
            elif delta.days <= 31:
                span = "month"
            elif delta.days <= 93:
                span = "3month"
            elif delta.days <= 365:
                span = "year"
            else:
                span = "5year"
            
            # Get historical data
            historicals = rh.stocks.get_stock_historicals(
                symbol,
                interval=rh_interval,
                span=span,
                bounds="extended"  # Include extended hours
            )
            
            if not historicals:
                return None
            
            # Convert to standard format
            data = []
            for point in historicals:
                data.append({
                    'timestamp': point['begins_at'],
                    'open': float(point['open_price']),
                    'high': float(point['high_price']),
                    'low': float(point['low_price']),
                    'close': float(point['close_price']),
                    'volume': int(point['volume']),
                    'symbol': symbol,
                    'source': self.name
                })
            
            self.record_success()
            return data
            
        except Exception as e:
            logger.error(f"Robin Stocks historical error for {symbol}: {e}")
            self.record_error()
            return None
    
    async def get_options_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get options chain from Robinhood"""
        try:
            await self._ensure_login()
            
            # Get options chains
            chains = rh.options.find_tradable_options(symbol)
            if not chains:
                return None
            
            options_data = {
                'symbol': symbol,
                'chains': {}
            }
            
            # Group by expiration
            for option in chains[:100]:  # Limit to first 100
                exp_date = option['expiration_date']
                if exp_date not in options_data['chains']:
                    options_data['chains'][exp_date] = {
                        'calls': [],
                        'puts': []
                    }
                
                option_type = 'calls' if option['type'] == 'call' else 'puts'
                options_data['chains'][exp_date][option_type].append({
                    'strike': float(option['strike_price']),
                    'bid': float(option.get('bid_price', 0)),
                    'ask': float(option.get('ask_price', 0)),
                    'volume': int(option.get('volume', 0)),
                    'openInterest': int(option.get('open_interest', 0)),
                    'impliedVolatility': float(option.get('implied_volatility', 0))
                })
            
            self.record_success()
            return options_data
            
        except Exception as e:
            logger.error(f"Robin Stocks options error for {symbol}: {e}")
            self.record_error()
            return None
    
    async def get_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cryptocurrency data from Robinhood"""
        try:
            await self._ensure_login()
            
            # Get crypto quote
            crypto_info = rh.crypto.get_crypto_quote(symbol)
            if not crypto_info:
                return None
            
            quote = {
                'symbol': symbol,
                'price': float(crypto_info['mark_price']),
                'bid': float(crypto_info['bid_price']),
                'ask': float(crypto_info['ask_price']),
                'high': float(crypto_info['high_price']),
                'low': float(crypto_info['low_price']),
                'volume': float(crypto_info['volume']),
                'timestamp': datetime.utcnow().isoformat(),
                'source': self.name
            }
            
            self.record_success()
            return quote
            
        except Exception as e:
            logger.error(f"Robin Stocks crypto error for {symbol}: {e}")
            self.record_error()
            return None


