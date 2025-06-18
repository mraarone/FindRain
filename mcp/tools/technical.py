# mcp/tools/technical.py

CALCULATE_SMA_TOOL = ToolDefinition(
    name="calculate_sma",
    category=ToolCategory.TECHNICAL_ANALYSIS,
    description="Calculate Simple Moving Average",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Stock symbol",
            required=True
        ),
        ToolParameter(
            name="period",
            type=int,
            description="Number of periods for SMA",
            required=True,
            min_value=2,
            max_value=500
        ),
        ToolParameter(
            name="price_type",
            type=str,
            description="Price type to use",
            required=False,
            default="close",
            choices=["open", "high", "low", "close"]
        )
    ],
    returns={
        "symbol": "string",
        "period": "number",
        "values": [
            {
                "timestamp": "string",
                "sma": "number"
            }
        ]
    },
    cache_timeout=300
)

CALCULATE_RSI_TOOL = ToolDefinition(
    name="calculate_rsi",
    category=ToolCategory.TECHNICAL_ANALYSIS,
    description="Calculate Relative Strength Index",
    parameters=[
        ToolParameter(
            name="symbol",
            type=str,
            description="Stock symbol",
            required=True
        ),
        ToolParameter(
            name="period",
            type=int,
            description="Number of periods for RSI",
            required=False,
            default=14,
            min_value=2,
            max_value=100
        )
    ],
    returns={
        "symbol": "string",
        "period": "number",
        "values": [
            {
                "timestamp": "string",
                "rsi": "number"
            }
        ],
        "overbought": "number (typically 70)",
        "oversold": "number (typically 30)"
    },
    cache_timeout=300
)


