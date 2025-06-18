# mcp/tools/market_data.py
from datetime import datetime
from ..protocol import ToolDefinition, ToolParameter, ToolCategory
from ..validators import ParameterValidator

# Tool Definitions

GET_QUOTE_TOOL = ToolDefinition(
    name="get_quote",
    category=ToolCategory.MARKET_DATA,
    description="Get real-time quote data for a stock or ETF",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Stock or ETF symbol (e.g., AAPL, SPY)",
            required=True
        ),
        ToolParameter(
            name="extended_hours",
            type=bool,
            description="Include extended hours data",
            required=False,
            default=False
        )
    ],
    returns={
        "symbol": "string",
        "price": "number",
        "open": "number",
        "high": "number", 
        "low": "number",
        "volume": "number",
        "previousClose": "number",
        "change": "number",
        "changePercent": "number",
        "bid": "number",
        "ask": "number",
        "bidSize": "number",
        "askSize": "number",
        "marketCap": "number",
        "pe": "number",
        "eps": "number",
        "timestamp": "string (ISO 8601)",
        "source": "string"
    },
    examples=[
        {
            "request": {"symbol": "AAPL"},
            "response": {
                "symbol": "AAPL",
                "price": 185.52,
                "open": 184.20,
                "high": 186.10,
                "low": 183.90,
                "volume": 52341892,
                "previousClose": 184.15,
                "change": 1.37,
                "changePercent": 0.74,
                "bid": 185.51,
                "ask": 185.53,
                "bidSize": 100,
                "askSize": 200,
                "marketCap": 2950000000000,
                "pe": 29.85,
                "eps": 6.22,
                "timestamp": "2024-01-15T16:00:00Z",
                "source": "yfinance"
            }
        }
    ],
    cache_timeout=30
)

GET_HISTORICAL_TOOL = ToolDefinition(
    name="get_historical",
    category=ToolCategory.MARKET_DATA,
    description="Get historical price data for a stock or ETF",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Stock or ETF symbol",
            required=True
        ),
        ToolParameter(
            name="start_date",
            type=str,
            description="Start date (YYYY-MM-DD)",
            required=True
        ),
        ToolParameter(
            name="end_date",
            type=str,
            description="End date (YYYY-MM-DD)",
            required=True
        ),
        ToolParameter(
            name="interval",
            type=str,
            description="Time interval for data points",
            required=False,
            default="1d",
            choices=["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"]
        )
    ],
    returns={
        "data": [
            {
                "timestamp": "string (ISO 8601)",
                "open": "number",
                "high": "number",
                "low": "number", 
                "close": "number",
                "volume": "number"
            }
        ],
        "symbol": "string",
        "interval": "string",
        "source": "string"
    },
    cache_timeout=3600
)

BATCH_QUOTES_TOOL = ToolDefinition(
    name="batch_quotes",
    category=ToolCategory.MARKET_DATA,
    description="Get quotes for multiple symbols at once",
    parameters=[
        ToolParameter(
            name="symbols",
            type=list,
            description="List of stock symbols",
            required=True
        )
    ],
    returns={
        "quotes": {
            "SYMBOL": {
                "price": "number",
                "change": "number",
                "changePercent": "number",
                "volume": "number"
            }
        },
        "timestamp": "string (ISO 8601)"
    },
    cache_timeout=30,
    rate_limit="100/minute"
)


