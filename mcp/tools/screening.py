# mcp/tools/screening.py
"""
Stock screening tools for MCP (Model Context Protocol).
Provides standardized tools for market screening and scanning.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from ..protocol import ToolDefinition, ToolParameter, ToolCategory

# Stock Screener Tool
SCREEN_STOCKS_TOOL = ToolDefinition(
    name="screen_stocks",
    category=ToolCategory.SCREENING,
    description="Screen stocks based on fundamental and technical criteria",
    parameters=[
        ToolParameter(
            name="market_cap_min",
            type=float,
            description="Minimum market cap (in millions)",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="market_cap_max",
            type=float,
            description="Maximum market cap (in millions)",
            required=False,
            default=None
        ),
        ToolParameter(
            name="pe_ratio_min",
            type=float,
            description="Minimum P/E ratio",
            required=False,
            default=None
        ),
        ToolParameter(
            name="pe_ratio_max",
            type=float,
            description="Maximum P/E ratio",
            required=False,
            default=None
        ),
        ToolParameter(
            name="dividend_yield_min",
            type=float,
            description="Minimum dividend yield (%)",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="volume_min",
            type=int,
            description="Minimum average volume",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="price_min",
            type=float,
            description="Minimum stock price",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="price_max",
            type=float,
            description="Maximum stock price",
            required=False,
            default=None
        ),
        ToolParameter(
            name="sectors",
            type=list,
            description="Filter by sectors",
            required=False,
            default=[]
        ),
        ToolParameter(
            name="industries",
            type=list,
            description="Filter by industries",
            required=False,
            default=[]
        ),
        ToolParameter(
            name="countries",
            type=list,
            description="Filter by countries",
            required=False,
            default=["US"]
        ),
        ToolParameter(
            name="sort_by",
            type=str,
            description="Sort results by",
            required=False,
            default="market_cap",
            choices=["market_cap", "volume", "price", "pe_ratio", "dividend_yield", "change_pct"]
        ),
        ToolParameter(
            name="order",
            type=str,
            description="Sort order",
            required=False,
            default="desc",
            choices=["asc", "desc"]
        ),
        ToolParameter(
            name="limit",
            type=int,
            description="Maximum results",
            required=False,
            default=50,
            min_value=1,
            max_value=500
        )
    ],
    returns={
        "results": [
            {
                "symbol": "string",
                "name": "string",
                "sector": "string",
                "industry": "string",
                "country": "string",
                "market_cap": "number",
                "price": "number",
                "change_pct": "number",
                "volume": "number",
                "pe_ratio": "number",
                "dividend_yield": "number",
                "eps": "number",
                "beta": "number",
                "52_week_high": "number",
                "52_week_low": "number"
            }
        ],
        "summary": {
            "total_results": "number",
            "average_market_cap": "number",
            "average_pe": "number",
            "sectors_distribution": {
                "SECTOR": "number (count)"
            }
        }
    },
    examples=[
        {
            "request": {
                "market_cap_min": 10000,
                "pe_ratio_max": 20,
                "dividend_yield_min": 2,
                "sectors": ["Technology", "Healthcare"],
                "sort_by": "dividend_yield",
                "limit": 10
            },
            "response": {
                "results": [
                    {
                        "symbol": "MSFT",
                        "name": "Microsoft Corporation",
                        "sector": "Technology",
                        "industry": "Software",
                        "country": "US",
                        "market_cap": 2800000,
                        "price": 380.50,
                        "change_pct": 1.25,
                        "volume": 25000000,
                        "pe_ratio": 18.5,
                        "dividend_yield": 2.1,
                        "eps": 20.54,
                        "beta": 0.93,
                        "52_week_high": 384.20,
                        "52_week_low": 310.15
                    }
                ],
                "summary": {
                    "total_results": 1,
                    "average_market_cap": 2800000,
                    "average_pe": 18.5,
                    "sectors_distribution": {
                        "Technology": 1
                    }
                }
            }
        }
    ],
    cache_timeout=300  # 5 minutes
)

# Technical Screener Tool
SCREEN_TECHNICAL_TOOL = ToolDefinition(
    name="screen_technical",
    category=ToolCategory.SCREENING,
    description="Screen stocks based on technical indicators and patterns",
    parameters=[
        ToolParameter(
            name="rsi_min",
            type=float,
            description="Minimum RSI value",
            required=False,
            default=None,
            min_value=0,
            max_value=100
        ),
        ToolParameter(
            name="rsi_max",
            type=float,
            description="Maximum RSI value",
            required=False,
            default=None,
            min_value=0,
            max_value=100
        ),
        ToolParameter(
            name="sma_cross",
            type=str,
            description="SMA crossover condition",
            required=False,
            default=None,
            choices=["golden_cross", "death_cross", "above_50", "below_50", "above_200", "below_200"]
        ),
        ToolParameter(
            name="volume_surge",
            type=float,
            description="Volume surge multiplier",
            required=False,
            default=None,
            min_value=1.0
        ),
        ToolParameter(
            name="price_change_min",
            type=float,
            description="Minimum price change %",
            required=False,
            default=None
        ),
        ToolParameter(
            name="price_change_max",
            type=float,
            description="Maximum price change %",
            required=False,
            default=None
        ),
        ToolParameter(
            name="patterns",
            type=list,
            description="Chart patterns to detect",
            required=False,
            default=[],
            choices=["breakout", "breakdown", "triangle", "flag", "head_shoulders", "double_top", "double_bottom"]
        ),
        ToolParameter(
            name="near_high_low",
            type=str,
            description="Near 52-week high/low",
            required=False,
            default=None,
            choices=["near_high", "near_low", "new_high", "new_low"]
        ),
        ToolParameter(
            name="momentum",
            type=str,
            description="Momentum condition",
            required=False,
            default=None,
            choices=["strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"]
        ),
        ToolParameter(
            name="limit",
            type=int,
            description="Maximum results",
            required=False,
            default=50,
            min_value=1,
            max_value=500
        )
    ],
    returns={
        "results": [
            {
                "symbol": "string",
                "name": "string",
                "price": "number",
                "change_pct": "number",
                "volume": "number",
                "volume_ratio": "number",
                "rsi": "number",
                "sma_20": "number",
                "sma_50": "number",
                "sma_200": "number",
                "macd": {
                    "value": "number",
                    "signal": "number",
                    "histogram": "number"
                },
                "patterns_detected": ["string"],
                "technical_rating": "string (strong_buy/buy/neutral/sell/strong_sell)"
            }
        ],
        "signals_summary": {
            "bullish_signals": "number",
            "bearish_signals": "number",
            "neutral_signals": "number",
            "strongest_patterns": ["string"]
        }
    },
    cache_timeout=300  # 5 minutes
)

# ETF Screener Tool
SCREEN_ETFS_TOOL = ToolDefinition(
    name="screen_etfs",
    category=ToolCategory.SCREENING,
    description="Screen ETFs based on various criteria",
    parameters=[
        ToolParameter(
            name="asset_class",
            type=str,
            description="Asset class filter",
            required=False,
            default="all",
            choices=["all", "equity", "fixed_income", "commodity", "currency", "real_estate", "mixed"]
        ),
        ToolParameter(
            name="region",
            type=str,
            description="Geographic region",
            required=False,
            default="all",
            choices=["all", "us", "international", "global", "emerging", "developed", "europe", "asia", "americas"]
        ),
        ToolParameter(
            name="expense_ratio_max",
            type=float,
            description="Maximum expense ratio (%)",
            required=False,
            default=None,
            min_value=0,
            max_value=5
        ),
        ToolParameter(
            name="aum_min",
            type=float,
            description="Minimum assets under management (millions)",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="volume_min",
            type=int,
            description="Minimum average volume",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="performance_period",
            type=str,
            description="Performance period for sorting",
            required=False,
            default="1y",
            choices=["1d", "1w", "1m", "3m", "6m", "1y", "3y", "5y"]
        ),
        ToolParameter(
            name="dividend_yield_min",
            type=float,
            description="Minimum dividend yield (%)",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="leveraged",
            type=bool,
            description="Include leveraged ETFs",
            required=False,
            default=False
        ),
        ToolParameter(
            name="inverse",
            type=bool,
            description="Include inverse ETFs",
            required=False,
            default=False
        ),
        ToolParameter(
            name="sort_by",
            type=str,
            description="Sort results by",
            required=False,
            default="aum",
            choices=["aum", "volume", "expense_ratio", "performance", "dividend_yield"]
        ),
        ToolParameter(
            name="limit",
            type=int,
            description="Maximum results",
            required=False,
            default=50,
            min_value=1,
            max_value=500
        )
    ],
    returns={
        "results": [
            {
                "symbol": "string",
                "name": "string",
                "asset_class": "string",
                "category": "string",
                "expense_ratio": "number",
                "aum": "number",
                "price": "number",
                "change_pct": "number",
                "volume": "number",
                "dividend_yield": "number",
                "performance": {
                    "1d": "number",
                    "1w": "number",
                    "1m": "number",
                    "3m": "number",
                    "6m": "number",
                    "1y": "number",
                    "3y": "number",
                    "5y": "number"
                },
                "holdings_count": "number",
                "top_holdings": [
                    {
                        "symbol": "string",
                        "weight": "number"
                    }
                ]
            }
        ],
        "summary": {
            "total_results": "number",
            "average_expense_ratio": "number",
            "total_aum": "number",
            "asset_class_distribution": {
                "CLASS": "number (count)"
            }
        }
    },
    cache_timeout=600  # 10 minutes
)

# Custom Screener Tool
CREATE_CUSTOM_SCREEN_TOOL = ToolDefinition(
    name="create_custom_screen",
    category=ToolCategory.SCREENING,
    description="Create a custom screening query with complex criteria",
    parameters=[
        ToolParameter(
            name="name",
            type=str,
            description="Screen name",
            required=True
        ),
        ToolParameter(
            name="criteria",
            type=list,
            description="List of screening criteria",
            required=True
        ),
        ToolParameter(
            name="logic",
            type=str,
            description="Criteria combination logic",
            required=False,
            default="AND",
            choices=["AND", "OR", "CUSTOM"]
        ),
        ToolParameter(
            name="custom_logic",
            type=str,
            description="Custom logic expression (if logic='CUSTOM')",
            required=False,
            default=""
        ),
        ToolParameter(
            name="save",
            type=bool,
            description="Save screen for future use",
            required=False,
            default=False
        )
    ],
    returns={
        "screen_id": "string (if saved)",
        "results": [
            {
                "symbol": "string",
                "name": "string",
                "matched_criteria": ["string"],
                "score": "number",
                "data": "object"
            }
        ],
        "execution_time": "number (ms)",
        "total_matches": "number"
    },
    examples=[
        {
            "request": {
                "name": "Value Growth Screen",
                "criteria": [
                    {
                        "field": "pe_ratio",
                        "operator": "<",
                        "value": 15
                    },
                    {
                        "field": "revenue_growth_yoy",
                        "operator": ">",
                        "value": 10
                    },
                    {
                        "field": "debt_to_equity",
                        "operator": "<",
                        "value": 0.5
                    }
                ],
                "logic": "AND",
                "save": true
            },
            "response": {
                "screen_id": "custom_screen_123",
                "results": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "matched_criteria": ["pe_ratio", "revenue_growth_yoy", "debt_to_equity"],
                        "score": 3.0,
                        "data": {
                            "pe_ratio": 14.5,
                            "revenue_growth_yoy": 12.3,
                            "debt_to_equity": 0.45
                        }
                    }
                ],
                "execution_time": 245,
                "total_matches": 1
            }
        }
    ],
    cache_timeout=0,  # Don't cache custom screens
    requires_auth=True
)

# Market Movers Tool
GET_MARKET_MOVERS_TOOL = ToolDefinition(
    name="get_market_movers",
    category=ToolCategory.SCREENING,
    description="Get top market movers by various metrics",
    parameters=[
        ToolParameter(
            name="mover_type",
            type=str,
            description="Type of movers to retrieve",
            required=True,
            choices=["gainers", "losers", "most_active", "unusual_volume", "new_highs", "new_lows"]
        ),
        ToolParameter(
            name="market",
            type=str,
            description="Market filter",
            required=False,
            default="all",
            choices=["all", "nasdaq", "nyse", "amex", "otc"]
        ),
        ToolParameter(
            name="market_cap",
            type=str,
            description="Market cap filter",
            required=False,
            default="all",
            choices=["all", "mega", "large", "mid", "small", "micro"]
        ),
        ToolParameter(
            name="min_price",
            type=float,
            description="Minimum stock price",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="min_volume",
            type=int,
            description="Minimum volume",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="limit",
            type=int,
            description="Number of results",
            required=False,
            default=20,
            min_value=1,
            max_value=100
        )
    ],
    returns={
        "mover_type": "string",
        "timestamp": "string",
        "movers": [
            {
                "rank": "number",
                "symbol": "string",
                "name": "string",
                "price": "number",
                "change": "number",
                "change_pct": "number",
                "volume": "number",
                "volume_ratio": "number",
                "market_cap": "number",
                "sector": "string"
            }
        ],
        "market_context": {
            "sp500_change": "number",
            "nasdaq_change": "number",
            "dow_change": "number",
            "vix": "number",
            "market_breadth": {
                "advances": "number",
                "declines": "number",
                "unchanged": "number"
            }
        }
    },
    cache_timeout=60  # 1 minute for market movers
)

# Sector Performance Tool
GET_SECTOR_PERFORMANCE_TOOL = ToolDefinition(
    name="get_sector_performance",
    category=ToolCategory.SCREENING,
    description="Get sector and industry performance data",
    parameters=[
        ToolParameter(
            name="period",
            type=str,
            description="Performance period",
            required=False,
            default="1d",
            choices=["1d", "1w", "1m", "3m", "6m", "1y", "ytd"]
        ),
        ToolParameter(
            name="view",
            type=str,
            description="Level of detail",
            required=False,
            default="sectors",
            choices=["sectors", "industries", "both"]
        ),
        ToolParameter(
            name="include_etfs",
            type=bool,
            description="Include sector ETF performance",
            required=False,
            default=True
        )
    ],
    returns={
        "period": "string",
        "sectors": [
            {
                "name": "string",
                "performance": "number",
                "volume": "number",
                "market_cap": "number",
                "pe_ratio": "number",
                "top_gainers": [
                    {
                        "symbol": "string",
                        "name": "string",
                        "change_pct": "number"
                    }
                ],
                "top_losers": [
                    {
                        "symbol": "string",
                        "name": "string",
                        "change_pct": "number"
                    }
                ],
                "sector_etf": {
                    "symbol": "string",
                    "performance": "number"
                }
            }
        ],
        "industries": [
            {
                "name": "string",
                "sector": "string",
                "performance": "number",
                "stock_count": "number"
            }
        ],
        "market_overview": {
            "best_sector": "string",
            "worst_sector": "string",
            "sector_rotation": "string (risk-on/risk-off/neutral)"
        }
    },
    cache_timeout=300  # 5 minutes
)

# IPO Screener Tool
SCREEN_IPOS_TOOL = ToolDefinition(
    name="screen_ipos",
    category=ToolCategory.SCREENING,
    description="Screen recent and upcoming IPOs",
    parameters=[
        ToolParameter(
            name="status",
            type=str,
            description="IPO status",
            required=False,
            default="all",
            choices=["all", "upcoming", "recent", "filed"]
        ),
        ToolParameter(
            name="days_range",
            type=int,
            description="Days to look back/forward",
            required=False,
            default=30,
            min_value=1,
            max_value=365
        ),
        ToolParameter(
            name="min_offering_size",
            type=float,
            description="Minimum offering size (millions)",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="sectors",
            type=list,
            description="Filter by sectors",
            required=False,
            default=[]
        ),
        ToolParameter(
            name="sort_by",
            type=str,
            description="Sort results by",
            required=False,
            default="ipo_date",
            choices=["ipo_date", "offering_size", "performance", "market_cap"]
        )
    ],
    returns={
        "ipos": [
            {
                "symbol": "string",
                "name": "string",
                "ipo_date": "string",
                "status": "string",
                "offering_price": "number",
                "offering_shares": "number",
                "offering_size": "number",
                "current_price": "number (if trading)",
                "performance": "number (if trading)",
                "market_cap": "number",
                "sector": "string",
                "industry": "string",
                "underwriters": ["string"],
                "description": "string"
            }
        ],
        "summary": {
            "total_ipos": "number",
            "total_offering_size": "number",
            "average_performance": "number",
            "sector_distribution": {
                "SECTOR": "number"
            }
        }
    },
    cache_timeout=3600  # 1 hour for IPO data
)