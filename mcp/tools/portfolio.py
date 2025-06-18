# mcp/tools/portfolio.py
"""
Portfolio management tools for MCP (Model Context Protocol).
Provides standardized tools for portfolio operations.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from ..protocol import ToolDefinition, ToolParameter, ToolCategory
from ..validators import ParameterValidator

# Portfolio Creation Tool
CREATE_PORTFOLIO_TOOL = ToolDefinition(
    name="create_portfolio",
    category=ToolCategory.PORTFOLIO,
    description="Create a new investment portfolio",
    parameters=[
        ToolParameter(
            name="name",
            type=str,
            description="Portfolio name",
            required=True
        ),
        ToolParameter(
            name="description",
            type=str,
            description="Portfolio description",
            required=False,
            default=""
        ),
        ToolParameter(
            name="initial_cash",
            type=float,
            description="Initial cash balance",
            required=False,
            default=0.0,
            min_value=0.0
        ),
        ToolParameter(
            name="currency",
            type=str,
            description="Portfolio currency",
            required=False,
            default="USD",
            choices=["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]
        )
    ],
    returns={
        "portfolio_id": "string",
        "name": "string",
        "description": "string",
        "currency": "string",
        "cash_balance": "number",
        "created_at": "string (ISO 8601)"
    },
    examples=[
        {
            "request": {
                "name": "Tech Growth Portfolio",
                "description": "Focus on technology growth stocks",
                "initial_cash": 100000,
                "currency": "USD"
            },
            "response": {
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Tech Growth Portfolio",
                "description": "Focus on technology growth stocks",
                "currency": "USD",
                "cash_balance": 100000,
                "created_at": "2024-01-15T10:00:00Z"
            }
        }
    ],
    requires_auth=True
)

# Add Holding Tool
ADD_HOLDING_TOOL = ToolDefinition(
    name="add_holding",
    category=ToolCategory.PORTFOLIO,
    description="Add a holding to a portfolio",
    parameters=[
        ToolParameter(
            name="portfolio_id",
            type=str,
            description="Portfolio ID",
            required=True
        ),
        ToolParameter(
            name="symbol",
            type=str,
            description="Stock or asset symbol",
            required=True
        ),
        ToolParameter(
            name="quantity",
            type=float,
            description="Number of shares/units",
            required=True,
            min_value=0.0001
        ),
        ToolParameter(
            name="purchase_price",
            type=float,
            description="Price per share/unit",
            required=True,
            min_value=0.01
        ),
        ToolParameter(
            name="purchase_date",
            type=str,
            description="Purchase date (YYYY-MM-DD)",
            required=False,
            default=None
        ),
        ToolParameter(
            name="commission",
            type=float,
            description="Transaction commission",
            required=False,
            default=0.0,
            min_value=0.0
        )
    ],
    returns={
        "holding_id": "string",
        "portfolio_id": "string",
        "symbol": "string",
        "quantity": "number",
        "purchase_price": "number",
        "purchase_date": "string",
        "total_cost": "number",
        "commission": "number"
    },
    cache_timeout=0,  # Don't cache write operations
    requires_auth=True
)

# Get Portfolio Performance Tool
GET_PORTFOLIO_PERFORMANCE_TOOL = ToolDefinition(
    name="get_portfolio_performance",
    category=ToolCategory.PORTFOLIO,
    description="Get portfolio performance metrics and analytics",
    parameters=[
        ToolParameter(
            name="portfolio_id",
            type=str,
            description="Portfolio ID",
            required=True
        ),
        ToolParameter(
            name="period",
            type=str,
            description="Performance period",
            required=False,
            default="all",
            choices=["1d", "1w", "1m", "3m", "6m", "1y", "ytd", "all"]
        ),
        ToolParameter(
            name="benchmark",
            type=str,
            description="Benchmark symbol for comparison",
            required=False,
            default="SPY"
        )
    ],
    returns={
        "portfolio_id": "string",
        "period": "string",
        "performance": {
            "total_value": "number",
            "total_cost": "number",
            "total_return": "number",
            "total_return_pct": "number",
            "daily_return": "number",
            "daily_return_pct": "number",
            "unrealized_pnl": "number",
            "realized_pnl": "number"
        },
        "risk_metrics": {
            "volatility": "number",
            "sharpe_ratio": "number",
            "max_drawdown": "number",
            "beta": "number",
            "alpha": "number"
        },
        "holdings": [
            {
                "symbol": "string",
                "quantity": "number",
                "current_value": "number",
                "cost_basis": "number",
                "gain_loss": "number",
                "gain_loss_pct": "number",
                "weight": "number"
            }
        ],
        "benchmark_comparison": {
            "benchmark_return": "number",
            "excess_return": "number",
            "tracking_error": "number",
            "information_ratio": "number"
        }
    },
    cache_timeout=60,  # Cache for 1 minute
    requires_auth=True
)

# Portfolio Rebalancing Tool
REBALANCE_PORTFOLIO_TOOL = ToolDefinition(
    name="rebalance_portfolio",
    category=ToolCategory.PORTFOLIO,
    description="Calculate portfolio rebalancing recommendations",
    parameters=[
        ToolParameter(
            name="portfolio_id",
            type=str,
            description="Portfolio ID",
            required=True
        ),
        ToolParameter(
            name="target_allocations",
            type=dict,
            description="Target allocations by symbol (percentages)",
            required=True
        ),
        ToolParameter(
            name="rebalance_threshold",
            type=float,
            description="Minimum deviation to trigger rebalancing (%)",
            required=False,
            default=5.0,
            min_value=0.1,
            max_value=50.0
        ),
        ToolParameter(
            name="max_trade_impact",
            type=float,
            description="Maximum portfolio % to trade",
            required=False,
            default=20.0,
            min_value=1.0,
            max_value=100.0
        )
    ],
    returns={
        "portfolio_id": "string",
        "current_allocations": {
            "SYMBOL": {
                "weight": "number",
                "value": "number"
            }
        },
        "target_allocations": {
            "SYMBOL": {
                "weight": "number",
                "value": "number"
            }
        },
        "trades_required": [
            {
                "symbol": "string",
                "action": "string (buy/sell)",
                "quantity": "number",
                "estimated_price": "number",
                "estimated_value": "number"
            }
        ],
        "rebalancing_cost": "number",
        "post_rebalance_allocations": {
            "SYMBOL": {
                "weight": "number",
                "value": "number"
            }
        }
    },
    cache_timeout=300,  # Cache for 5 minutes
    requires_auth=True
)

# Portfolio Risk Analysis Tool
ANALYZE_PORTFOLIO_RISK_TOOL = ToolDefinition(
    name="analyze_portfolio_risk",
    category=ToolCategory.PORTFOLIO,
    description="Comprehensive portfolio risk analysis",
    parameters=[
        ToolParameter(
            name="portfolio_id",
            type=str,
            description="Portfolio ID",
            required=True
        ),
        ToolParameter(
            name="var_confidence",
            type=float,
            description="Value at Risk confidence level",
            required=False,
            default=0.95,
            choices=[0.90, 0.95, 0.99]
        ),
        ToolParameter(
            name="time_horizon",
            type=int,
            description="Risk assessment time horizon (days)",
            required=False,
            default=1,
            min_value=1,
            max_value=252
        )
    ],
    returns={
        "portfolio_id": "string",
        "risk_metrics": {
            "portfolio_volatility": "number",
            "portfolio_beta": "number",
            "value_at_risk": {
                "confidence": "number",
                "var_amount": "number",
                "var_percentage": "number"
            },
            "expected_shortfall": "number",
            "downside_deviation": "number",
            "sortino_ratio": "number"
        },
        "concentration_risk": {
            "herfindahl_index": "number",
            "top_5_concentration": "number",
            "single_stock_limit_breaches": ["string"]
        },
        "correlation_analysis": {
            "average_correlation": "number",
            "correlation_matrix": "object",
            "highly_correlated_pairs": [
                {
                    "pair": ["string", "string"],
                    "correlation": "number"
                }
            ]
        },
        "sector_exposure": {
            "SECTOR": "number (percentage)"
        },
        "risk_factors": {
            "market_risk": "number",
            "specific_risk": "number",
            "currency_risk": "number"
        },
        "recommendations": ["string"]
    },
    cache_timeout=600,  # Cache for 10 minutes
    requires_auth=True
)

# Portfolio Optimization Tool
OPTIMIZE_PORTFOLIO_TOOL = ToolDefinition(
    name="optimize_portfolio",
    category=ToolCategory.PORTFOLIO,
    description="Optimize portfolio allocation using modern portfolio theory",
    parameters=[
        ToolParameter(
            name="symbols",
            type=list,
            description="List of symbols to include in optimization",
            required=True
        ),
        ToolParameter(
            name="optimization_method",
            type=str,
            description="Optimization method to use",
            required=False,
            default="max_sharpe",
            choices=["max_sharpe", "min_volatility", "max_return", "risk_parity", "equal_weight"]
        ),
        ToolParameter(
            name="constraints",
            type=dict,
            description="Optimization constraints",
            required=False,
            default={
                "min_weight": 0.0,
                "max_weight": 1.0,
                "target_return": None,
                "max_volatility": None
            }
        ),
        ToolParameter(
            name="lookback_period",
            type=int,
            description="Historical data lookback period (days)",
            required=False,
            default=252,
            min_value=30,
            max_value=1260
        )
    ],
    returns={
        "optimal_weights": {
            "SYMBOL": "number"
        },
        "expected_metrics": {
            "annual_return": "number",
            "annual_volatility": "number",
            "sharpe_ratio": "number",
            "max_drawdown": "number"
        },
        "efficient_frontier": [
            {
                "return": "number",
                "volatility": "number",
                "sharpe_ratio": "number"
            }
        ],
        "optimization_details": {
            "method": "string",
            "constraints_satisfied": "boolean",
            "iterations": "number"
        }
    },
    cache_timeout=3600,  # Cache for 1 hour
    requires_auth=True
)

# List Portfolios Tool
LIST_PORTFOLIOS_TOOL = ToolDefinition(
    name="list_portfolios",
    category=ToolCategory.PORTFOLIO,
    description="List all portfolios for the authenticated user",
    parameters=[
        ToolParameter(
            name="include_performance",
            type=bool,
            description="Include performance metrics",
            required=False,
            default=False
        ),
        ToolParameter(
            name="sort_by",
            type=str,
            description="Sort portfolios by field",
            required=False,
            default="created_at",
            choices=["name", "total_value", "return", "created_at", "updated_at"]
        )
    ],
    returns={
        "portfolios": [
            {
                "portfolio_id": "string",
                "name": "string",
                "description": "string",
                "currency": "string",
                "created_at": "string",
                "holdings_count": "number",
                "total_value": "number (if include_performance)",
                "total_return": "number (if include_performance)",
                "total_return_pct": "number (if include_performance)"
            }
        ],
        "count": "number"
    },
    cache_timeout=300,  # Cache for 5 minutes
    requires_auth=True
)