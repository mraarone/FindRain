# api/data/sources/options_source.py
"""
Options data source implementation for comprehensive options data.
Supports multiple providers including CBOE, OCC, and broker APIs.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.stats import norm
import logging
import json

from .base import BaseDataSource, DataSourceStatus

logger = logging.getLogger(__name__)

class OptionsDataSource(BaseDataSource):
    """Base class for options data sources"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, priority=config.get('priority', 1))
        self.config = config
        self.session = None
        
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def get_options_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get complete options chain for a symbol"""
        raise NotImplementedError
    
    async def get_historical_options(
        self,
        contract: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical options data for a specific contract"""
        raise NotImplementedError
    
    async def get_greeks(self, contracts: List[str]) -> Optional[Dict[str, Any]]:
        """Get real-time Greeks for option contracts"""
        raise NotImplementedError
    
    async def get_iv_surface(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get implied volatility surface data"""
        raise NotImplementedError


class CBOEOptionsSource(OptionsDataSource):
    """CBOE options data source implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("CBOE", config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.cboe.com/v1')
        
    async def get_options_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get options chain from CBOE"""
        try:
            await self._ensure_session()
            
            # Get current spot price first
            spot_price = await self._get_spot_price(symbol)
            if not spot_price:
                return None
            
            # Get all expirations
            expirations = await self._get_expirations(symbol)
            if not expirations:
                return None
            
            # Get options data for each expiration
            chains = {}
            for exp in expirations:
                chain_data = await self._get_chain_for_expiration(symbol, exp)
                if chain_data:
                    chains[exp] = chain_data
            
            self.record_success()
            
            return {
                'symbol': symbol,
                'spot_price': spot_price,
                'expirations': expirations,
                'chains': chains,
                'source': self.name,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"CBOE options chain error for {symbol}: {e}")
            self.record_error()
            return None
    
    async def _get_spot_price(self, symbol: str) -> Optional[float]:
        """Get current spot price"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            async with self.session.get(
                f"{self.base_url}/quotes/{symbol}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('last', 0)
        except Exception as e:
            logger.error(f"Error getting spot price: {e}")
            return None
    
    async def _get_expirations(self, symbol: str) -> Optional[List[str]]:
        """Get available expiration dates"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            async with self.session.get(
                f"{self.base_url}/options/expirations/{symbol}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('expirations', [])
        except Exception as e:
            logger.error(f"Error getting expirations: {e}")
            return None
    
    async def _get_chain_for_expiration(self, symbol: str, expiration: str) -> Optional[Dict[str, Any]]:
        """Get options chain for specific expiration"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            params = {'expiration': expiration}
            
            async with self.session.get(
                f"{self.base_url}/options/chain/{symbol}",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process and calculate Greeks
                    calls = []
                    puts = []
                    
                    for option in data.get('options', []):
                        processed = self._process_option_data(option)
                        if processed['type'] == 'call':
                            calls.append(processed)
                        else:
                            puts.append(processed)
                    
                    return {
                        'calls': sorted(calls, key=lambda x: x['strike']),
                        'puts': sorted(puts, key=lambda x: x['strike'])
                    }
        except Exception as e:
            logger.error(f"Error getting chain for expiration: {e}")
            return None
    
    def _process_option_data(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw option data and calculate Greeks"""
        # Extract basic data
        processed = {
            'strike': option['strike'],
            'type': option['type'].lower(),
            'bid': option.get('bid', 0),
            'ask': option.get('ask', 0),
            'last': option.get('last', 0),
            'volume': option.get('volume', 0),
            'open_interest': option.get('openInterest', 0),
            'implied_volatility': option.get('impliedVolatility', 0)
        }
        
        # Calculate mid price
        if processed['bid'] > 0 and processed['ask'] > 0:
            processed['mid'] = (processed['bid'] + processed['ask']) / 2
        else:
            processed['mid'] = processed['last']
        
        # Greeks will be calculated separately if needed
        processed['delta'] = option.get('delta', 0)
        processed['gamma'] = option.get('gamma', 0)
        processed['theta'] = option.get('theta', 0)
        processed['vega'] = option.get('vega', 0)
        processed['rho'] = option.get('rho', 0)
        
        # Moneyness
        processed['in_the_money'] = option.get('inTheMoney', False)
        
        return processed
    
    async def get_historical_options(
        self,
        contract: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical options data"""
        try:
            await self._ensure_session()
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            params = {
                'contract': contract,
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
            
            async with self.session.get(
                f"{self.base_url}/options/historical",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process historical data
                    historical = []
                    for point in data.get('data', []):
                        historical.append({
                            'timestamp': point['timestamp'],
                            'open': point.get('open', 0),
                            'high': point.get('high', 0),
                            'low': point.get('low', 0),
                            'close': point.get('close', 0),
                            'volume': point.get('volume', 0),
                            'open_interest': point.get('openInterest', 0),
                            'implied_volatility': point.get('impliedVolatility', 0)
                        })
                    
                    self.record_success()
                    return historical
                    
        except Exception as e:
            logger.error(f"Error getting historical options: {e}")
            self.record_error()
            return None


class TDAOptionsSource(OptionsDataSource):
    """TD Ameritrade options data source"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("TDA", config)
        self.api_key = config.get('api_key')
        self.base_url = 'https://api.tdameritrade.com/v1'
        self.access_token = None
        
    async def get_options_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get options chain from TD Ameritrade"""
        try:
            await self._ensure_session()
            await self._ensure_auth()
            
            headers = {'Authorization': f'Bearer {self.access_token}'}
            params = {
                'symbol': symbol,
                'includeQuotes': 'TRUE',
                'strategy': 'SINGLE',
                'range': 'ALL'
            }
            
            async with self.session.get(
                f"{self.base_url}/marketdata/chains",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_tda_chain(data)
                    
        except Exception as e:
            logger.error(f"TDA options chain error: {e}")
            self.record_error()
            return None
    
    async def _ensure_auth(self):
        """Ensure we have valid access token"""
        # Implementation would handle OAuth2 flow
        # For now, assume token is provided in config
        if not self.access_token:
            self.access_token = self.config.get('access_token')
    
    def _process_tda_chain(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process TD Ameritrade chain format"""
        if 'status' in data and data['status'] != 'SUCCESS':
            return None
        
        result = {
            'symbol': data.get('symbol'),
            'spot_price': data.get('underlyingPrice', 0),
            'expirations': [],
            'chains': {},
            'source': self.name,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Process calls
        call_exp_map = data.get('callExpDateMap', {})
        for exp_date, strikes in call_exp_map.items():
            if exp_date not in result['chains']:
                result['chains'][exp_date] = {'calls': [], 'puts': []}
                result['expirations'].append(exp_date)
            
            for strike, options in strikes.items():
                for option in options:
                    result['chains'][exp_date]['calls'].append(
                        self._process_tda_option(option)
                    )
        
        # Process puts
        put_exp_map = data.get('putExpDateMap', {})
        for exp_date, strikes in put_exp_map.items():
            if exp_date not in result['chains']:
                result['chains'][exp_date] = {'calls': [], 'puts': []}
                result['expirations'].append(exp_date)
            
            for strike, options in strikes.items():
                for option in options:
                    result['chains'][exp_date]['puts'].append(
                        self._process_tda_option(option)
                    )
        
        return result
    
    def _process_tda_option(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual TD Ameritrade option"""
        return {
            'strike': option.get('strikePrice', 0),
            'bid': option.get('bid', 0),
            'ask': option.get('ask', 0),
            'last': option.get('last', 0),
            'volume': option.get('totalVolume', 0),
            'open_interest': option.get('openInterest', 0),
            'implied_volatility': option.get('volatility', 0) / 100,  # Convert to decimal
            'delta': option.get('delta', 0),
            'gamma': option.get('gamma', 0),
            'theta': option.get('theta', 0),
            'vega': option.get('vega', 0),
            'rho': option.get('rho', 0),
            'in_the_money': option.get('inTheMoney', False)
        }


class OptionsAggregator:
    """Aggregates options data from multiple sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.sources: List[OptionsDataSource] = []
        self._initialize_sources(config)
        
    def _initialize_sources(self, config: Dict[str, Any]):
        """Initialize configured options data sources"""
        source_classes = {
            'cboe': CBOEOptionsSource,
            'tda': TDAOptionsSource,
            # Add more sources as needed
        }
        
        for source_name, source_config in config.get('OPTION_SOURCES', {}).items():
            if source_config.get('enabled') and source_name in source_classes:
                try:
                    source_class = source_classes[source_name]
                    source = source_class(source_config)
                    self.sources.append(source)
                    logger.info(f"Initialized options source: {source_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize {source_name}: {e}")
        
        # Sort by priority
        self.sources.sort(key=lambda x: x.priority)
    
    async def get_options_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get options chain with failover"""
        for source in self.sources:
            if source.status == DataSourceStatus.UNHEALTHY:
                continue
                
            try:
                logger.info(f"Trying {source.name} for options chain {symbol}")
                result = await source.get_options_chain(symbol)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error getting options from {source.name}: {e}")
                source.record_error()
        
        return None
    
    async def get_historical_options(
        self,
        contract: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical options data with failover"""
        for source in self.sources:
            if source.status == DataSourceStatus.UNHEALTHY:
                continue
                
            try:
                result = await source.get_historical_options(contract, start_date, end_date)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error getting historical from {source.name}: {e}")
                source.record_error()
        
        return None
    
    def calculate_implied_volatility(
        self,
        option_price: float,
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        risk_free_rate: float,
        dividend_yield: float,
        option_type: str
    ) -> float:
        """Calculate implied volatility using Newton-Raphson method"""
        
        # Initial guess
        vol = 0.3
        tolerance = 1e-5
        max_iterations = 100
        
        for i in range(max_iterations):
            # Calculate option price and vega
            d1 = (np.log(spot_price / strike_price) + 
                  (risk_free_rate - dividend_yield + 0.5 * vol ** 2) * time_to_expiry) / (vol * np.sqrt(time_to_expiry))
            
            d2 = d1 - vol * np.sqrt(time_to_expiry)
            
            if option_type == 'call':
                theoretical_price = (spot_price * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(d1) - 
                                   strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2))
            else:
                theoretical_price = (strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - 
                                   spot_price * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1))
            
            # Vega
            vega = spot_price * norm.pdf(d1) * np.sqrt(time_to_expiry) * np.exp(-dividend_yield * time_to_expiry) / 100
            
            # Price difference
            price_diff = theoretical_price - option_price
            
            # Check convergence
            if abs(price_diff) < tolerance:
                return vol
            
            # Newton-Raphson update
            if vega != 0:
                vol = vol - price_diff / vega
            else:
                break
            
            # Ensure vol stays positive
            vol = max(vol, 0.001)
        
        return vol