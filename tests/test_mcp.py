# tests/test_mcp.py
import pytest
from mcp.protocol import ToolDefinition, ToolParameter, ToolCategory, ToolRegistry
from mcp.validators import ParameterValidator, ValidationError

def test_tool_definition():
    """Test tool definition creation"""
    tool = ToolDefinition(
        name="test_tool",
        category=ToolCategory.MARKET_DATA,
        description="Test tool",
        parameters=[
            ToolParameter(
                name="symbol",
                type=str,
                description="Stock symbol",
                required=True
            )
        ],
        returns={"result": "string"}
    )
    
    assert tool.name == "test_tool"
    assert tool.category == ToolCategory.MARKET_DATA
    assert len(tool.parameters) == 1

def test_parameter_validation():
    """Test parameter validation"""
    # Valid symbol
    assert ParameterValidator.validate_symbol("AAPL") == "AAPL"
    
    # Invalid symbol
    with pytest.raises(ValidationError):
        ParameterValidator.validate_symbol("invalid@symbol")
    
    # Valid date
    date = ParameterValidator.validate_date("2024-01-01")
    assert date.year == 2024
    
    # Invalid date
    with pytest.raises(ValidationError):
        ParameterValidator.validate_date("invalid-date")
