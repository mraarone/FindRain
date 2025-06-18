# mcp/tools/crypto.py
"""
Cryptocurrency tools for MCP (Model Context Protocol).
Provides standardized tools for crypto data and analysis.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from ..protocol import ToolDefinition, ToolParameter, ToolCategory

# Get Crypto Quote Tool
GET_CRYPTO_QUOTE_TOOL = ToolDefinition(
    name="get_crypto_quote",
    category=ToolCategory.CRYPTO,
    description="Get real-time cryptocurrency quote data",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Crypto symbol (e.g., BTC, ETH, BTC-USD)",
            required=True
        ),
        ToolParameter(
            name="convert",
            type=str,
            description="Convert to currency",
            required=False,
            default="USD",
            choices=["USD", "EUR", "GBP", "JPY", "BTC", "ETH"]
        ),
        ToolParameter(
            name="exchange",
            type=str,
            description="Specific exchange for pricing",
            required=False,
            default=None
        )
    ],
    returns={
        "symbol": "string",
        "name": "string",
        "price": "number",
        "price_btc": "number",
        "market_cap": "number",
        "volume_24h": "number",
        "volume_change_24h": "number",
        "percent_change_1h": "number",
        "percent_change_24h": "number",
        "percent_change_7d": "number",
        "percent_change_30d": "number",
        "circulating_supply": "number",
        "total_supply": "number",
        "max_supply": "number",
        "ath": "number (all-time high)",
        "ath_date": "string",
        "atl": "number (all-time low)",
        "atl_date": "string",
        "roi": "number",
        "last_updated": "string (ISO 8601)"
    },
    examples=[
        {
            "request": {"symbol": "BTC", "convert": "USD"},
            "response": {
                "symbol": "BTC",
                "name": "Bitcoin",
                "price": 45250.75,
                "price_btc": 1.0,
                "market_cap": 884521000000,
                "volume_24h": 28450000000,
                "volume_change_24h": 15.3,
                "percent_change_1h": 0.52,
                "percent_change_24h": 2.34,
                "percent_change_7d": -1.25,
                "percent_change_30d": 12.45,
                "circulating_supply": 19550000,
                "total_supply": 19550000,
                "max_supply": 21000000,
                "ath": 69000,
                "ath_date": "2021-11-10",
                "atl": 67.81,
                "atl_date": "2013-07-06",
                "roi": 45250,
                "last_updated": "2024-01-15T16:00:00Z"
            }
        }
    ],
    cache_timeout=30  # 30 seconds for real-time data
)

# Get Crypto Historical Data Tool
GET_CRYPTO_HISTORICAL_TOOL = ToolDefinition(
    name="get_crypto_historical",
    category=ToolCategory.CRYPTO,
    description="Get historical cryptocurrency price data",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Crypto symbol",
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
            description="Time interval",
            required=False,
            default="1d",
            choices=["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        ),
        ToolParameter(
            name="convert",
            type=str,
            description="Convert to currency",
            required=False,
            default="USD"
        )
    ],
    returns={
        "symbol": "string",
        "interval": "string",
        "data": [
            {
                "timestamp": "string (ISO 8601)",
                "open": "number",
                "high": "number",
                "low": "number",
                "close": "number",
                "volume": "number",
                "market_cap": "number"
            }
        ],
        "aggregated_stats": {
            "period_return": "number",
            "volatility": "number",
            "average_volume": "number",
            "high": "number",
            "low": "number"
        }
    },
    cache_timeout=3600  # 1 hour for historical data
)

# Get DeFi Metrics Tool
GET_DEFI_METRICS_TOOL = ToolDefinition(
    name="get_defi_metrics",
    category=ToolCategory.CRYPTO,
    description="Get DeFi protocol metrics and analytics",
    parameters=[
        ToolParameter(
            name="protocol",
            type=str,
            description="DeFi protocol name or symbol",
            required=True
        ),
        ToolParameter(
            name="chain",
            type=str,
            description="Blockchain network",
            required=False,
            default="all",
            choices=["all", "ethereum", "bsc", "polygon", "avalanche", "arbitrum", "optimism"]
        )
    ],
    returns={
        "protocol": "string",
        "chain": "string",
        "tvl": "number (Total Value Locked)",
        "tvl_change_24h": "number",
        "tvl_change_7d": "number",
        "market_cap": "number",
        "price": "number",
        "price_change_24h": "number",
        "revenue_24h": "number",
        "revenue_7d": "number",
        "revenue_30d": "number",
        "users_24h": "number",
        "transactions_24h": "number",
        "fees_24h": "number",
        "apy": {
            "lending": "number",
            "borrowing": "number",
            "staking": "number"
        },
        "risk_metrics": {
            "audit_score": "number",
            "code_review_score": "number",
            "time_since_launch": "number (days)",
            "oracle_risk": "string"
        }
    },
    cache_timeout=300  # 5 minutes
)

# Get Blockchain Data Tool
GET_BLOCKCHAIN_DATA_TOOL = ToolDefinition(
    name="get_blockchain_data",
    category=ToolCategory.CRYPTO,
    description="Get blockchain network statistics and metrics",
    parameters=[
        ToolParameter(
            name="blockchain",
            type=str,
            description="Blockchain name",
            required=True,
            choices=["bitcoin", "ethereum", "bnb", "polygon", "avalanche", "solana", "cardano"]
        ),
        ToolParameter(
            name="metrics",
            type=list,
            description="Specific metrics to retrieve",
            required=False,
            default=["all"]
        )
    ],
    returns={
        "blockchain": "string",
        "network_stats": {
            "block_height": "number",
            "block_time": "number (seconds)",
            "difficulty": "number",
            "hashrate": "number",
            "total_addresses": "number",
            "active_addresses_24h": "number",
            "transactions_24h": "number",
            "average_tx_fee": "number",
            "median_tx_fee": "number",
            "mempool_size": "number"
        },
        "economic_data": {
            "market_cap": "number",
            "circulating_supply": "number",
            "inflation_rate": "number",
            "staking_ratio": "number",
            "staking_yield": "number"
        },
        "developer_activity": {
            "github_commits_30d": "number",
            "github_contributors": "number",
            "dapps_count": "number",
            "smart_contracts_deployed_24h": "number"
        }
    },
    cache_timeout=600  # 10 minutes
)

# Crypto Market Overview Tool
GET_CRYPTO_MARKET_OVERVIEW_TOOL = ToolDefinition(
    name="get_crypto_market_overview",
    category=ToolCategory.CRYPTO,
    description="Get overall cryptocurrency market statistics",
    parameters=[
        ToolParameter(
            name="limit",
            type=int,
            description="Number of top cryptocurrencies to include",
            required=False,
            default=10,
            min_value=1,
            max_value=100
        ),
        ToolParameter(
            name="category",
            type=str,
            description="Filter by category",
            required=False,
            default="all",
            choices=["all", "defi", "nft", "metaverse", "gaming", "privacy", "exchange-tokens", "stablecoins"]
        )
    ],
    returns={
        "global_metrics": {
            "total_market_cap": "number",
            "total_volume_24h": "number",
            "bitcoin_dominance": "number",
            "ethereum_dominance": "number",
            "defi_market_cap": "number",
            "stablecoin_market_cap": "number",
            "altcoin_market_cap": "number",
            "market_cap_change_24h": "number",
            "volume_change_24h": "number",
            "fear_greed_index": {
                "value": "number",
                "classification": "string"
            }
        },
        "top_cryptocurrencies": [
            {
                "rank": "number",
                "symbol": "string",
                "name": "string",
                "price": "number",
                "market_cap": "number",
                "volume_24h": "number",
                "percent_change_24h": "number",
                "percent_change_7d": "number"
            }
        ],
        "trending": {
            "gainers_24h": [
                {
                    "symbol": "string",
                    "price_change_24h": "number"
                }
            ],
            "losers_24h": [
                {
                    "symbol": "string",
                    "price_change_24h": "number"
                }
            ],
            "most_visited": ["string"],
            "recently_added": ["string"]
        }
    },
    cache_timeout=300  # 5 minutes
)

# Crypto Technical Indicators Tool
GET_CRYPTO_TECHNICALS_TOOL = ToolDefinition(
    name="get_crypto_technicals",
    category=ToolCategory.CRYPTO,
    description="Get technical analysis indicators for cryptocurrencies",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Crypto symbol",
            required=True
        ),
        ToolParameter(
            name="interval",
            type=str,
            description="Time interval for analysis",
            required=False,
            default="4h",
            choices=["15m", "30m", "1h", "4h", "1d", "1w"]
        ),
        ToolParameter(
            name="indicators",
            type=list,
            description="Specific indicators to calculate",
            required=False,
            default=["all"]
        )
    ],
    returns={
        "symbol": "string",
        "interval": "string",
        "price": "number",
        "indicators": {
            "moving_averages": {
                "sma_20": "number",
                "sma_50": "number",
                "sma_200": "number",
                "ema_20": "number",
                "ema_50": "number"
            },
            "oscillators": {
                "rsi": "number",
                "stochastic_k": "number",
                "stochastic_d": "number",
                "macd": "number",
                "macd_signal": "number",
                "macd_histogram": "number"
            },
            "volatility": {
                "bollinger_upper": "number",
                "bollinger_middle": "number",
                "bollinger_lower": "number",
                "atr": "number"
            },
            "support_resistance": {
                "support_levels": ["number"],
                "resistance_levels": ["number"],
                "pivot_point": "number"
            }
        },
        "signals": {
            "overall": "string (buy/sell/neutral)",
            "moving_averages": "string",
            "oscillators": "string",
            "summary": {
                "buy_signals": "number",
                "sell_signals": "number",
                "neutral_signals": "number"
            }
        }
    },
    cache_timeout=300  # 5 minutes
)

# Crypto News Tool
GET_CRYPTO_NEWS_TOOL = ToolDefinition(
    name="get_crypto_news",
    category=ToolCategory.CRYPTO,
    description="Get latest cryptocurrency news and analysis",
    parameters=[
        ToolParameter(
            name="symbols",
            type=list,
            description="Filter news by crypto symbols",
            required=False,
            default=[]
        ),
        ToolParameter(
            name="categories",
            type=list,
            description="News categories",
            required=False,
            default=["all"],
            choices=["all", "analysis", "blockchain", "regulation", "defi", "nft", "mining", "exchanges"]
        ),
        ToolParameter(
            name="limit",
            type=int,
            description="Number of articles",
            required=False,
            default=10,
            min_value=1,
            max_value=50
        ),
        ToolParameter(
            name="hours_back",
            type=int,
            description="Hours to look back",
            required=False,
            default=24,
            min_value=1,
            max_value=168
        )
    ],
    returns={
        "articles": [
            {
                "title": "string",
                "summary": "string",
                "url": "string",
                "source": "string",
                "author": "string",
                "published_at": "string",
                "symbols": ["string"],
                "categories": ["string"],
                "sentiment": "number (-1 to 1)",
                "importance": "string (high/medium/low)"
            }
        ],
        "sentiment_summary": {
            "overall": "number",
            "by_symbol": {
                "SYMBOL": "number"
            }
        },
        "top_topics": ["string"]
    },
    cache_timeout=300  # 5 minutes
)