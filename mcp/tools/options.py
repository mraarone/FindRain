# mcp/tools/options.py
"""
Options trading tools for MCP (Model Context Protocol).
Provides standardized tools for options data and analysis.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from ..protocol import ToolDefinition, ToolParameter, ToolCategory

# Get Options Chain Tool
GET_OPTIONS_CHAIN_TOOL = ToolDefinition(
    name="get_options_chain",
    category=ToolCategory.OPTIONS,
    description="Get options chain data for a symbol",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Underlying symbol",
            required=True
        ),
        ToolParameter(
            name="expiration",
            type=str,
            description="Expiration date (YYYY-MM-DD) or 'all'",
            required=False,
            default="all"
        ),
        ToolParameter(
            name="strike_range",
            type=str,
            description="Strike price range",
            required=False,
            default="atm",
            choices=["all", "itm", "atm", "otm", "near"]
        ),
        ToolParameter(
            name="option_type",
            type=str,
            description="Option type filter",
            required=False,
            default="both",
            choices=["both", "call", "put"]
        )
    ],
    returns={
        "symbol": "string",
        "spot_price": "number",
        "expirations": ["string"],
        "chain": {
            "EXPIRATION_DATE": {
                "calls": [
                    {
                        "strike": "number",
                        "bid": "number",
                        "ask": "number",
                        "last": "number",
                        "volume": "number",
                        "open_interest": "number",
                        "implied_volatility": "number",
                        "delta": "number",
                        "gamma": "number",
                        "theta": "number",
                        "vega": "number",
                        "rho": "number",
                        "in_the_money": "boolean"
                    }
                ],
                "puts": [
                    {
                        "strike": "number",
                        "bid": "number",
                        "ask": "number",
                        "last": "number",
                        "volume": "number",
                        "open_interest": "number",
                        "implied_volatility": "number",
                        "delta": "number",
                        "gamma": "number",
                        "theta": "number",
                        "vega": "number",
                        "rho": "number",
                        "in_the_money": "boolean"
                    }
                ]
            }
        }
    },
    examples=[
        {
            "request": {
                "symbol": "AAPL",
                "expiration": "2024-02-16",
                "strike_range": "near"
            },
            "response": {
                "symbol": "AAPL",
                "spot_price": 185.50,
                "expirations": ["2024-02-16"],
                "chain": {
                    "2024-02-16": {
                        "calls": [
                            {
                                "strike": 185,
                                "bid": 3.45,
                                "ask": 3.50,
                                "last": 3.48,
                                "volume": 1250,
                                "open_interest": 5420,
                                "implied_volatility": 0.285,
                                "delta": 0.55,
                                "gamma": 0.025,
                                "theta": -0.085,
                                "vega": 0.125,
                                "rho": 0.082,
                                "in_the_money": true
                            }
                        ],
                        "puts": []
                    }
                }
            }
        }
    ],
    cache_timeout=60  # 1 minute for options data
)

# Calculate Greeks Tool
CALCULATE_GREEKS_TOOL = ToolDefinition(
    name="calculate_greeks",
    category=ToolCategory.OPTIONS,
    description="Calculate option Greeks for a given contract",
    parameters=[
        ToolParameter(
            name="underlying_price",
            type=float,
            description="Current price of underlying",
            required=True,
            min_value=0.01
        ),
        ToolParameter(
            name="strike_price",
            type=float,
            description="Strike price of option",
            required=True,
            min_value=0.01
        ),
        ToolParameter(
            name="time_to_expiry",
            type=float,
            description="Time to expiration in years",
            required=True,
            min_value=0.0,
            max_value=10.0
        ),
        ToolParameter(
            name="volatility",
            type=float,
            description="Implied volatility (decimal)",
            required=True,
            min_value=0.01,
            max_value=5.0
        ),
        ToolParameter(
            name="risk_free_rate",
            type=float,
            description="Risk-free interest rate (decimal)",
            required=False,
            default=0.05,
            min_value=0.0,
            max_value=0.5
        ),
        ToolParameter(
            name="dividend_yield",
            type=float,
            description="Dividend yield (decimal)",
            required=False,
            default=0.0,
            min_value=0.0,
            max_value=0.5
        ),
        ToolParameter(
            name="option_type",
            type=str,
            description="Option type",
            required=True,
            choices=["call", "put"]
        )
    ],
    returns={
        "theoretical_value": "number",
        "greeks": {
            "delta": "number",
            "gamma": "number",
            "theta": "number",
            "vega": "number",
            "rho": "number"
        },
        "additional_metrics": {
            "lambda": "number (leverage)",
            "charm": "number (delta decay)",
            "vanna": "number (delta/vega sensitivity)",
            "vomma": "number (vega convexity)"
        }
    },
    cache_timeout=300  # 5 minutes
)

# Options Strategy Analyzer Tool
ANALYZE_OPTIONS_STRATEGY_TOOL = ToolDefinition(
    name="analyze_options_strategy",
    category=ToolCategory.OPTIONS,
    description="Analyze complex options strategies",
    parameters=[
        ToolParameter(
            name="strategy_type",
            type=str,
            description="Type of options strategy",
            required=True,
            choices=[
                "long_call", "long_put", "short_call", "short_put",
                "bull_call_spread", "bear_put_spread", "bull_put_spread", "bear_call_spread",
                "long_straddle", "short_straddle", "long_strangle", "short_strangle",
                "iron_condor", "iron_butterfly", "collar", "protective_put",
                "covered_call", "cash_secured_put", "custom"
            ]
        ),
        ToolParameter(
            name="legs",
            type=list,
            description="Strategy legs (for custom strategies)",
            required=False,
            default=[]
        ),
        ToolParameter(
            name="underlying_symbol",
            type=str,
            description="Underlying symbol",
            required=True
        ),
        ToolParameter(
            name="analysis_date",
            type=str,
            description="Analysis date (YYYY-MM-DD)",
            required=False,
            default=None
        )
    ],
    returns={
        "strategy": {
            "name": "string",
            "type": "string",
            "legs": [
                {
                    "type": "string (call/put)",
                    "action": "string (buy/sell)",
                    "strike": "number",
                    "expiration": "string",
                    "quantity": "number",
                    "premium": "number"
                }
            ]
        },
        "risk_profile": {
            "max_profit": "number",
            "max_loss": "number",
            "breakeven_points": ["number"],
            "profit_probability": "number",
            "expected_value": "number"
        },
        "greeks": {
            "net_delta": "number",
            "net_gamma": "number",
            "net_theta": "number",
            "net_vega": "number",
            "net_rho": "number"
        },
        "payoff_diagram": {
            "underlying_prices": ["number"],
            "payoff_values": ["number"],
            "current_price": "number"
        },
        "scenario_analysis": [
            {
                "scenario": "string",
                "underlying_price": "number",
                "profit_loss": "number",
                "probability": "number"
            }
        ]
    },
    cache_timeout=600  # 10 minutes
)

# Options Screener Tool
SCREEN_OPTIONS_TOOL = ToolDefinition(
    name="screen_options",
    category=ToolCategory.OPTIONS,
    description="Screen options based on various criteria",
    parameters=[
        ToolParameter(
            name="underlying_symbols",
            type=list,
            description="List of underlying symbols to screen",
            required=False,
            default=[]
        ),
        ToolParameter(
            name="option_type",
            type=str,
            description="Option type",
            required=False,
            default="both",
            choices=["both", "call", "put"]
        ),
        ToolParameter(
            name="min_volume",
            type=int,
            description="Minimum daily volume",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="min_open_interest",
            type=int,
            description="Minimum open interest",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="min_iv",
            type=float,
            description="Minimum implied volatility",
            required=False,
            default=0.0,
            min_value=0.0
        ),
        ToolParameter(
            name="max_iv",
            type=float,
            description="Maximum implied volatility",
            required=False,
            default=5.0,
            max_value=10.0
        ),
        ToolParameter(
            name="days_to_expiry_min",
            type=int,
            description="Minimum days to expiration",
            required=False,
            default=0,
            min_value=0
        ),
        ToolParameter(
            name="days_to_expiry_max",
            type=int,
            description="Maximum days to expiration",
            required=False,
            default=365,
            max_value=730
        ),
        ToolParameter(
            name="moneyness",
            type=str,
            description="Moneyness filter",
            required=False,
            default="all",
            choices=["all", "itm", "atm", "otm", "deep_itm", "deep_otm"]
        ),
        ToolParameter(
            name="sort_by",
            type=str,
            description="Sort results by",
            required=False,
            default="volume",
            choices=["volume", "open_interest", "iv", "premium", "delta"]
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
                "underlying_price": "number",
                "option_type": "string",
                "strike": "number",
                "expiration": "string",
                "days_to_expiry": "number",
                "bid": "number",
                "ask": "number",
                "last": "number",
                "volume": "number",
                "open_interest": "number",
                "implied_volatility": "number",
                "delta": "number",
                "moneyness": "string",
                "premium_to_strike": "number"
            }
        ],
        "summary": {
            "total_results": "number",
            "average_iv": "number",
            "total_volume": "number",
            "total_open_interest": "number"
        }
    },
    cache_timeout=300  # 5 minutes
)

# IV Surface Tool
GET_IV_SURFACE_TOOL = ToolDefinition(
    name="get_iv_surface",
    category=ToolCategory.OPTIONS,
    description="Get implied volatility surface data",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Underlying symbol",
            required=True
        ),
        ToolParameter(
            name="surface_type",
            type=str,
            description="Type of surface data",
            required=False,
            default="full",
            choices=["full", "term_structure", "smile", "skew"]
        )
    ],
    returns={
        "symbol": "string",
        "spot_price": "number",
        "surface_data": {
            "expirations": ["string"],
            "strikes": ["number"],
            "iv_matrix": {
                "calls": [[{"strike": "number", "expiry": "string", "iv": "number"}]],
                "puts": [[{"strike": "number", "expiry": "string", "iv": "number"}]]
            }
        },
        "term_structure": {
            "atm_ivs": [
                {
                    "expiration": "string",
                    "days_to_expiry": "number",
                    "iv": "number"
                }
            ]
        },
        "smile_data": {
            "expiration": "string",
            "strikes": ["number"],
            "call_ivs": ["number"],
            "put_ivs": ["number"]
        },
        "skew_metrics": {
            "25_delta_skew": "number",
            "10_delta_skew": "number",
            "risk_reversal": "number"
        }
    },
    cache_timeout=600  # 10 minutes
)

# Options Flow Tool
GET_OPTIONS_FLOW_TOOL = ToolDefinition(
    name="get_options_flow",
    category=ToolCategory.OPTIONS,
    description="Get unusual options activity and flow data",
    parameters=[
        ToolParameter(
            name="symbols",
            type=list,
            description="Filter by symbols (empty for all)",
            required=False,
            default=[]
        ),
        ToolParameter(
            name="min_premium",
            type=float,
            description="Minimum trade premium",
            required=False,
            default=25000,
            min_value=0
        ),
        ToolParameter(
            name="trade_types",
            type=list,
            description="Types of trades to include",
            required=False,
            default=["all"],
            choices=["all", "sweep", "block", "split", "unusual"]
        ),
        ToolParameter(
            name="sentiment",
            type=str,
            description="Trade sentiment filter",
            required=False,
            default="all",
            choices=["all", "bullish", "bearish", "neutral"]
        ),
        ToolParameter(
            name="hours_back",
            type=int,
            description="Hours to look back",
            required=False,
            default=24,
            min_value=1,
            max_value=720
        )
    ],
    returns={
        "flow_data": [
            {
                "timestamp": "string",
                "symbol": "string",
                "option_type": "string",
                "strike": "number",
                "expiration": "string",
                "trade_type": "string",
                "sentiment": "string",
                "premium": "number",
                "volume": "number",
                "open_interest": "number",
                "spot_price": "number",
                "iv": "number",
                "delta": "number",
                "unusual_score": "number"
            }
        ],
        "summary": {
            "total_premium": "number",
            "bullish_premium": "number",
            "bearish_premium": "number",
            "put_call_ratio": "number",
            "most_active_symbols": [
                {
                    "symbol": "string",
                    "total_premium": "number",
                    "trade_count": "number"
                }
            ]
        }
    },
    cache_timeout=60  # 1 minute for flow data
)