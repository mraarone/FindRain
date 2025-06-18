# mcp/protocol.py
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import inspect
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    """Categories for organizing tools"""
    MARKET_DATA = "market_data"
    TECHNICAL_ANALYSIS = "technical_analysis"
    PORTFOLIO = "portfolio"
    NEWS = "news"
    CRYPTO = "crypto"
    OPTIONS = "options"
    SCREENING = "screening"
    SENTIMENT = "sentiment"

@dataclass
class ToolParameter:
    """Definition of a tool parameter"""
    name: str
    type: Type
    description: str
    required: bool = True
    default: Any = None
    choices: Optional[List[Any]] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None

@dataclass
class ToolDefinition:
    """Complete tool definition for MCP"""
    name: str
    category: ToolCategory
    description: str
    parameters: List[ToolParameter]
    returns: Dict[str, Any]
    examples: List[Dict[str, Any]] = field(default_factory=list)
    rate_limit: Optional[str] = None
    cache_timeout: Optional[int] = None
    requires_auth: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'parameters': [
                {
                    'name': p.name,
                    'type': p.type.__name__,
                    'description': p.description,
                    'required': p.required,
                    'default': p.default,
                    'choices': p.choices,
                    'min_value': p.min_value,
                    'max_value': p.max_value
                }
                for p in self.parameters
            ],
            'returns': self.returns,
            'examples': self.examples,
            'rate_limit': self.rate_limit,
            'cache_timeout': self.cache_timeout,
            'requires_auth': self.requires_auth
        }
    
    def generate_documentation(self) -> str:
        """Generate markdown documentation for the tool"""
        doc = f"## {self.name}\n\n"
        doc += f"**Category:** {self.category.value}\n\n"
        doc += f"**Description:** {self.description}\n\n"
        
        if self.parameters:
            doc += "### Parameters\n\n"
            for param in self.parameters:
                doc += f"- **{param.name}** ({param.type.__name__})"
                if param.required:
                    doc += " *[required]*"
                doc += f": {param.description}"
                if param.default is not None:
                    doc += f" (default: {param.default})"
                if param.choices:
                    doc += f" (choices: {', '.join(map(str, param.choices))})"
                doc += "\n"
        
        doc += f"\n### Returns\n\n```json\n{json.dumps(self.returns, indent=2)}\n```\n"
        
        if self.examples:
            doc += "\n### Examples\n\n"
            for i, example in enumerate(self.examples):
                doc += f"#### Example {i+1}\n\n"
                doc += f"**Request:**\n```json\n{json.dumps(example['request'], indent=2)}\n```\n\n"
                doc += f"**Response:**\n```json\n{json.dumps(example['response'], indent=2)}\n```\n\n"
        
        return doc

class ToolRegistry:
    """Registry for all available tools"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.handlers: Dict[str, Callable] = {}
        
    def register(self, definition: ToolDefinition, handler: Callable):
        """Register a new tool"""
        self.tools[definition.name] = definition
        self.handlers[definition.name] = handler
        logger.info(f"Registered tool: {definition.name}")
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name"""
        return self.tools.get(name)
    
    def get_handler(self, name: str) -> Optional[Callable]:
        """Get tool handler by name"""
        return self.handlers.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
        """List all tools, optionally filtered by category"""
        tools = list(self.tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    def search_tools(self, query: str) -> List[ToolDefinition]:
        """Search tools by name or description"""
        query_lower = query.lower()
        return [
            tool for tool in self.tools.values()
            if query_lower in tool.name.lower() or query_lower in tool.description.lower()
        ]
    
    def generate_all_documentation(self) -> str:
        """Generate documentation for all tools"""
        doc = "# MCP Tool Documentation\n\n"
        
        # Group by category
        categories = {}
        for tool in self.tools.values():
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool)
        
        # Generate docs for each category
        for category, tools in sorted(categories.items(), key=lambda x: x[0].value):
            doc += f"\n# {category.value.replace('_', ' ').title()}\n\n"
            for tool in sorted(tools, key=lambda x: x.name):
                doc += tool.generate_documentation() + "\n---\n\n"
        
        return doc
