# api/data/sources/yfinance_source.py
import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import pandas as pd
from .base import BaseDataSource

class YFinanceSource(BaseDataSource):
    """Yahoo Finance data source implementation"""
    
    def __init__(self):
        super().__init__("yfinance", priority=1)
        
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                self.record_error()
                return None
                
            quote = {
                'symbol': symbol,
                'price': info.get('regularMarketPrice', info.get('price')),
                'open': info.get('regularMarketOpen', info.get('open')),
                'high': info.get('regularMarketDayHigh', info.get('dayHigh')),
                'low': info.get('regularMarketDayLow', info.get('dayLow')),
                'volume': info.get('regularMarketVolume', info.get('volume')),
                'previousClose': info.get('regularMarketPreviousClose', info.get('previousClose')),
                'change': info.get('regularMarketChange'),
                'changePercent': info.get('regularMarketChangePercent'),
                'bid': info.get('bid'),
                'ask': info.get('ask'),
                'bidSize': info.get('bidSize'),
                'askSize': info.get('askSize'),
                'marketCap': info.get('marketCap'),
                'pe': info.get('trailingPE'),
                'eps': info.get('trailingEps'),
                'timestamp': datetime.utcnow().isoformat(),
                'source': self.name
            }
            
            self.record_success()
            return quote
            
        except Exception as e:
            logger.error(f"YFinance quote error for {symbol}: {e}")
            self.record_error()
            return None
    
    async def get_historical(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical data with maximum granularity"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Convert interval to yfinance format
            yf_interval_map = {
                "1s": "1m",  # yfinance doesn't support 1s, use 1m as minimum
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "1d": "1d",
                "1w": "1wk",
                "1M": "1mo"
            }
            
            yf_interval = yf_interval_map.get(interval, interval)
            
            # Download data
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                prepost=True,  # Include pre and post market data
                repair=True    # Repair data
            )
            
            if df.empty:
                self.record_error()
                return None
            
            # Convert to list of dicts
            data = []
            for index, row in df.iterrows():
                data.append({
                    'timestamp': index.isoformat(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                    'symbol': symbol,
                    'source': self.name
                })
            
            self.record_success()
            return data
            
        except Exception as e:
            logger.error(f"YFinance historical error for {symbol}: {e}")
            self.record_error()
            return None
    
    async def get_options_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get options chain data"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get expiration dates
            expirations = ticker.options
            if not expirations:
                return None
            
            options_data = {
                'symbol': symbol,
                'expirations': expirations,
                'chains': {}
            }
            
            # Get options for each expiration
            for exp in expirations[:5]:  # Limit to first 5 expirations
                opt = ticker.option_chain(exp)
                
                options_data['chains'][exp] = {
                    'calls': opt.calls.to_dict('records'),
                    'puts': opt.puts.to_dict('records')
                }
            
            self.record_success()
            return options_data
            
        except Exception as e:
            logger.error(f"YFinance options error for {symbol}: {e}")
            self.record_error()
            return None
    
    async def get_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cryptocurrency data"""
        try:
            # Append -USD if not present
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"
                
            return await self.get_quote(symbol)
            
        except Exception as e:
            logger.error(f"YFinance crypto error for {symbol}: {e}")
            self.record_error()
            return None


