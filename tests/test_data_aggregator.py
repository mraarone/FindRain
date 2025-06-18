# tests/test_data_aggregator.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from api.data.aggregator import DataAggregator
from api.data.sources.base import DataSourceStatus

@pytest.mark.asyncio
async def test_data_aggregator_failover():
    """Test failover between data sources"""
    # Create mock sources
    source1 = Mock()
    source1.name = "source1"
    source1.priority = 1
    source1.status = DataSourceStatus.UNHEALTHY
    source1.get_quote = AsyncMock(return_value=None)
    
    source2 = Mock()
    source2.name = "source2"
    source2.priority = 2
    source2.status = DataSourceStatus.HEALTHY
    source2.get_quote = AsyncMock(return_value={'price': 150.0})
    
    # Create aggregator
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    
    config = {'DATA_SOURCES': {}, 'CACHE_STRATEGIES': {'quotes': {'timeout': 30}}}
    aggregator = DataAggregator(cache, config)
    aggregator.sources = [source1, source2]
    
    # Test failover
    result = await aggregator.get_quote('AAPL')
    
    assert result == {'price': 150.0}
    source1.get_quote.assert_called_once()
    source2.get_quote.assert_called_once()
