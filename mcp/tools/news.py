# mcp/tools/news.py

GET_NEWS_TOOL = ToolDefinition(
    name="get_news",
    category=ToolCategory.NEWS,
    description="Get latest news articles for a symbol or topic",
    parameters=[
        ToolParameter(
            name="query",
            type=str,
            description="Symbol or search query",
            required=True
        ),
        ToolParameter(
            name="limit",
            type=int,
            description="Maximum number of articles",
            required=False,
            default=10,
            min_value=1,
            max_value=100
        ),
        ToolParameter(
            name="hours_back",
            type=int,
            description="How many hours back to search",
            required=False,
            default=24,
            min_value=1,
            max_value=720
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
                "published_at": "string (ISO 8601)",
                "retrieved_at": "string (ISO 8601)",
                "symbols": ["string"],
                "sentiment": "number (-1 to 1)",
                "categories": ["string"]
            }
        ],
        "query": "string",
        "count": "number"
    },
    cache_timeout=300
)

ANALYZE_SENTIMENT_TOOL = ToolDefinition(
    name="analyze_sentiment",
    category=ToolCategory.SENTIMENT,
    description="Analyze sentiment for a stock based on news and social media",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Stock symbol",
            required=True
        ),
        ToolParameter(
            name="sources",
            type=list,
            description="Data sources to analyze",
            required=False,
            default=["news", "social"],
            choices=["news", "social", "analyst", "sec"]
        )
    ],
    returns={
        "symbol": "string",
        "overall_sentiment": "number (-1 to 1)",
        "sentiment_breakdown": {
            "positive": "number (percentage)",
            "neutral": "number (percentage)", 
            "negative": "number (percentage)"
        },
        "sources_analyzed": "number",
        "top_mentions": [
            {
                "text": "string",
                "sentiment": "number",
                "source": "string"
            }
        ],
        "timestamp": "string (ISO 8601)"
    },
    cache_timeout=600
)