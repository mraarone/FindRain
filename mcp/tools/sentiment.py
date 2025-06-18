# mcp/tools/sentiment.py
"""
Sentiment analysis tools for MCP (Model Context Protocol).
Provides standardized tools for market sentiment and social analysis.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from ..protocol import ToolDefinition, ToolParameter, ToolCategory

# Analyze News Sentiment Tool
ANALYZE_NEWS_SENTIMENT_TOOL = ToolDefinition(
    name="analyze_news_sentiment",
    category=ToolCategory.SENTIMENT,
    description="Analyze sentiment from news articles for a symbol or topic",
    parameters=[
        ToolParameter(
            name="query",
            type=str,
            description="Symbol, company name, or topic to analyze",
            required=True
        ),
        ToolParameter(
            name="sources",
            type=list,
            description="News sources to include",
            required=False,
            default=["all"],
            choices=["all", "mainstream", "financial", "social", "blogs", "press_releases"]
        ),
        ToolParameter(
            name="time_period",
            type=str,
            description="Time period to analyze",
            required=False,
            default="24h",
            choices=["1h", "4h", "24h", "3d", "7d", "30d"]
        ),
        ToolParameter(
            name="languages",
            type=list,
            description="Languages to include",
            required=False,
            default=["en"],
            choices=["en", "es", "fr", "de", "ja", "zh"]
        )
    ],
    returns={
        "query": "string",
        "overall_sentiment": {
            "score": "number (-1 to 1)",
            "classification": "string (very_negative/negative/neutral/positive/very_positive)",
            "confidence": "number (0 to 1)"
        },
        "sentiment_timeline": [
            {
                "timestamp": "string",
                "sentiment": "number",
                "article_count": "number"
            }
        ],
        "sentiment_by_source": {
            "SOURCE": {
                "sentiment": "number",
                "article_count": "number"
            }
        },
        "key_topics": [
            {
                "topic": "string",
                "sentiment": "number",
                "frequency": "number"
            }
        ],
        "influential_articles": [
            {
                "title": "string",
                "source": "string",
                "published_at": "string",
                "sentiment": "number",
                "reach": "number",
                "url": "string"
            }
        ],
        "summary": {
            "total_articles": "number",
            "positive_articles": "number",
            "negative_articles": "number",
            "neutral_articles": "number",
            "sentiment_trend": "string (improving/stable/declining)"
        }
    },
    examples=[
        {
            "request": {
                "query": "AAPL",
                "sources": ["financial", "mainstream"],
                "time_period": "24h"
            },
            "response": {
                "query": "AAPL",
                "overall_sentiment": {
                    "score": 0.42,
                    "classification": "positive",
                    "confidence": 0.85
                },
                "sentiment_timeline": [
                    {
                        "timestamp": "2024-01-15T12:00:00Z",
                        "sentiment": 0.35,
                        "article_count": 15
                    }
                ],
                "sentiment_by_source": {
                    "Bloomberg": {
                        "sentiment": 0.45,
                        "article_count": 8
                    },
                    "Reuters": {
                        "sentiment": 0.38,
                        "article_count": 7
                    }
                },
                "key_topics": [
                    {
                        "topic": "earnings beat",
                        "sentiment": 0.75,
                        "frequency": 12
                    }
                ],
                "influential_articles": [
                    {
                        "title": "Apple Reports Record Q1 Earnings",
                        "source": "Bloomberg",
                        "published_at": "2024-01-15T09:30:00Z",
                        "sentiment": 0.82,
                        "reach": 1500000,
                        "url": "https://example.com/article"
                    }
                ],
                "summary": {
                    "total_articles": 45,
                    "positive_articles": 28,
                    "negative_articles": 5,
                    "neutral_articles": 12,
                    "sentiment_trend": "improving"
                }
            }
        }
    ],
    cache_timeout=300  # 5 minutes
)

# Social Media Sentiment Tool
ANALYZE_SOCIAL_SENTIMENT_TOOL = ToolDefinition(
    name="analyze_social_sentiment",
    category=ToolCategory.SENTIMENT,
    description="Analyze sentiment from social media platforms",
    parameters=[
        ToolParameter(
            name="query",
            type=str,
            description="Symbol, $cashtag, or topic",
            required=True
        ),
        ToolParameter(
            name="platforms",
            type=list,
            description="Social platforms to analyze",
            required=False,
            default=["all"],
            choices=["all", "twitter", "reddit", "stocktwits", "youtube", "tiktok"]
        ),
        ToolParameter(
            name="influencer_only",
            type=bool,
            description="Only analyze posts from verified/influential accounts",
            required=False,
            default=False
        ),
        ToolParameter(
            name="time_period",
            type=str,
            description="Time period to analyze",
            required=False,
            default="24h",
            choices=["1h", "4h", "24h", "3d", "7d"]
        )
    ],
    returns={
        "query": "string",
        "overall_sentiment": {
            "score": "number (-1 to 1)",
            "classification": "string",
            "confidence": "number"
        },
        "platform_breakdown": {
            "PLATFORM": {
                "sentiment": "number",
                "post_count": "number",
                "engagement": "number",
                "reach": "number"
            }
        },
        "trending_topics": [
            {
                "topic": "string",
                "mentions": "number",
                "sentiment": "number",
                "growth_rate": "number"
            }
        ],
        "influential_posts": [
            {
                "platform": "string",
                "author": "string",
                "content": "string (truncated)",
                "sentiment": "number",
                "engagement": "number",
                "timestamp": "string"
            }
        ],
        "emoji_sentiment": {
            "bullish_emojis": ["string"],
            "bearish_emojis": ["string"],
            "neutral_emojis": ["string"]
        },
        "retail_vs_institutional": {
            "retail_sentiment": "number",
            "institutional_sentiment": "number",
            "divergence": "number"
        }
    },
    cache_timeout=60  # 1 minute for real-time social data
)

# Market Sentiment Indicators Tool
GET_MARKET_SENTIMENT_INDICATORS_TOOL = ToolDefinition(
    name="get_market_sentiment_indicators",
    category=ToolCategory.SENTIMENT,
    description="Get various market sentiment indicators",
    parameters=[
        ToolParameter(
            name="indicators",
            type=list,
            description="Specific indicators to retrieve",
            required=False,
            default=["all"],
            choices=["all", "fear_greed", "put_call", "vix", "breadth", "bull_bear", "margin_debt", "short_interest"]
        ),
        ToolParameter(
            name="lookback_days",
            type=int,
            description="Days of historical data",
            required=False,
            default=30,
            min_value=1,
            max_value=365
        )
    ],
    returns={
        "timestamp": "string",
        "indicators": {
            "fear_greed_index": {
                "value": "number (0-100)",
                "classification": "string",
                "components": {
                    "market_momentum": "number",
                    "stock_strength": "number",
                    "stock_breadth": "number",
                    "put_call_ratio": "number",
                    "market_volatility": "number",
                    "safe_haven_demand": "number",
                    "junk_bond_demand": "number"
                }
            },
            "put_call_ratio": {
                "total": "number",
                "equity": "number",
                "index": "number",
                "vix_calls": "number"
            },
            "vix": {
                "current": "number",
                "change": "number",
                "percentile": "number",
                "term_structure": {
                    "vix9d": "number",
                    "vix30d": "number",
                    "vix90d": "number"
                }
            },
            "market_breadth": {
                "advances": "number",
                "declines": "number",
                "advance_decline_line": "number",
                "new_highs": "number",
                "new_lows": "number",
                "mcclellan_oscillator": "number"
            },
            "bull_bear_sentiment": {
                "aaii_bulls": "number",
                "aaii_bears": "number",
                "aaii_neutral": "number",
                "investors_intelligence_bulls": "number",
                "investors_intelligence_bears": "number"
            },
            "positioning": {
                "margin_debt": "number",
                "short_interest": "number",
                "cot_positioning": "number"
            }
        },
        "historical_data": [
            {
                "date": "string",
                "fear_greed": "number",
                "put_call": "number",
                "vix": "number"
            }
        ],
        "sentiment_signals": {
            "extreme_fear": "boolean",
            "extreme_greed": "boolean",
            "divergence_detected": "boolean",
            "sentiment_shift": "string"
        }
    },
    cache_timeout=300  # 5 minutes
)

# Analyst Sentiment Tool
GET_ANALYST_SENTIMENT_TOOL = ToolDefinition(
    name="get_analyst_sentiment",
    category=ToolCategory.SENTIMENT,
    description="Get analyst ratings and sentiment for stocks",
    parameters=[
        ToolParameter(
            name="symbols",
            type=list,
            description="Stock symbols to analyze",
            required=True
        ),
        ToolParameter(
            name="include_targets",
            type=bool,
            description="Include price targets",
            required=False,
            default=True
        ),
        ToolParameter(
            name="changes_only",
            type=bool,
            description="Only show recent rating changes",
            required=False,
            default=False
        ),
        ToolParameter(
            name="days_back",
            type=int,
            description="Days to look back for changes",
            required=False,
            default=30,
            min_value=1,
            max_value=365
        )
    ],
    returns={
        "results": {
            "SYMBOL": {
                "consensus_rating": "string (strong_buy/buy/hold/sell/strong_sell)",
                "consensus_score": "number (1-5)",
                "total_analysts": "number",
                "rating_distribution": {
                    "strong_buy": "number",
                    "buy": "number",
                    "hold": "number",
                    "sell": "number",
                    "strong_sell": "number"
                },
                "price_targets": {
                    "average": "number",
                    "high": "number",
                    "low": "number",
                    "median": "number",
                    "current_price": "number",
                    "upside_potential": "number"
                },
                "recent_changes": [
                    {
                        "analyst": "string",
                        "firm": "string",
                        "action": "string (upgrade/downgrade/initiate/reiterate)",
                        "old_rating": "string",
                        "new_rating": "string",
                        "old_target": "number",
                        "new_target": "number",
                        "date": "string"
                    }
                ],
                "sentiment_trend": "string (improving/stable/deteriorating)"
            }
        },
        "market_sentiment": {
            "bullish_percentage": "number",
            "average_upside": "number",
            "upgrade_downgrade_ratio": "number"
        }
    },
    cache_timeout=3600  # 1 hour
)

# Options Sentiment Tool
ANALYZE_OPTIONS_SENTIMENT_TOOL = ToolDefinition(
    name="analyze_options_sentiment",
    category=ToolCategory.SENTIMENT,
    description="Analyze sentiment from options flow and positioning",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Stock symbol",
            required=True
        ),
        ToolParameter(
            name="metrics",
            type=list,
            description="Sentiment metrics to calculate",
            required=False,
            default=["all"],
            choices=["all", "put_call", "skew", "term_structure", "flow", "open_interest", "gamma"]
        ),
        ToolParameter(
            name="expiry_range",
            type=str,
            description="Expiration range to analyze",
            required=False,
            default="all",
            choices=["all", "weekly", "monthly", "leaps"]
        )
    ],
    returns={
        "symbol": "string",
        "options_sentiment": {
            "put_call_ratio": {
                "current": "number",
                "20_day_avg": "number",
                "percentile": "number",
                "signal": "string (bullish/neutral/bearish)"
            },
            "volatility_skew": {
                "25_delta_skew": "number",
                "risk_reversal": "number",
                "skew_percentile": "number",
                "signal": "string"
            },
            "term_structure": {
                "contango_backwardation": "string",
                "near_term_iv": "number",
                "far_term_iv": "number",
                "iv_term_slope": "number"
            },
            "smart_money_flow": {
                "large_trades_sentiment": "number",
                "sweep_sentiment": "number",
                "institutional_positioning": "string"
            },
            "gamma_exposure": {
                "total_gamma": "number",
                "call_gamma": "number",
                "put_gamma": "number",
                "gamma_flip_level": "number"
            }
        },
        "unusual_activity": [
            {
                "type": "string",
                "strike": "number",
                "expiry": "string",
                "volume_oi_ratio": "number",
                "sentiment": "string"
            }
        ],
        "overall_signal": {
            "sentiment": "string",
            "confidence": "number",
            "key_levels": {
                "support": "number",
                "resistance": "number"
            }
        }
    },
    cache_timeout=300  # 5 minutes
)

# Insider Sentiment Tool
GET_INSIDER_SENTIMENT_TOOL = ToolDefinition(
    name="get_insider_sentiment",
    category=ToolCategory.SENTIMENT,
    description="Get insider trading sentiment and activity",
    parameters=[
        ToolParameter(
            name="symbols",
            type=list,
            description="Stock symbols",
            required=True
        ),
        ToolParameter(
            name="transaction_types",
            type=list,
            description="Types of transactions",
            required=False,
            default=["all"],
            choices=["all", "purchase", "sale", "option_exercise", "gift"]
        ),
        ToolParameter(
            name="days_back",
            type=int,
            description="Days to look back",
            required=False,
            default=90,
            min_value=1,
            max_value=365
        ),
        ToolParameter(
            name="min_value",
            type=float,
            description="Minimum transaction value",
            required=False,
            default=0,
            min_value=0
        )
    ],
    returns={
        "results": {
            "SYMBOL": {
                "buy_sell_ratio": "number",
                "net_shares_traded": "number",
                "net_value_traded": "number",
                "unique_insiders": "number",
                "sentiment_score": "number (-1 to 1)",
                "recent_transactions": [
                    {
                        "insider_name": "string",
                        "title": "string",
                        "transaction_type": "string",
                        "shares": "number",
                        "price": "number",
                        "value": "number",
                        "date": "string",
                        "ownership_change": "number"
                    }
                ],
                "cluster_detected": "boolean",
                "signal": "string (bullish/neutral/bearish)"
            }
        },
        "market_comparison": {
            "sector_avg_sentiment": "number",
            "percentile_rank": "number"
        }
    },
    cache_timeout=3600  # 1 hour
)