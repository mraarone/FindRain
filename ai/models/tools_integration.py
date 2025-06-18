# ai/tools_integration.py
from typing import Dict, List, Any, Optional
import json
import asyncio

from ..assistant import Message, AIResponse
from ...mcp.protocol import ToolDefinition, ToolRegistry
from ...mcp.validators import ParameterValidator

class ToolAwareAssistant:
    """Wrapper for AI assistants with tool execution capabilities"""
    
    def __init__(self, assistant: BaseAIAssistant, tool_registry: ToolRegistry):
        self.assistant = assistant
        self.tool_registry = tool_registry
        self.assistant.set_tool_registry(tool_registry)
        
    async def process_query(
        self,
        query: str,
        context: Optional[List[Message]] = None,
        auto_execute_tools: bool = True
    ) -> AIResponse:
        """Process a query with automatic tool selection and execution"""
        
        # Determine relevant tools for the query
        relevant_tools = self._select_relevant_tools(query)
        
        # Prepare messages
        messages = context or []
        messages.append(Message(role="user", content=query))
        
        # Get initial response from AI
        response = await self.assistant.generate_response(
            messages,
            tools=relevant_tools
        )
        
        # Execute tools if requested
        if auto_execute_tools and response.tools_used:
            tool_results = await self._execute_tools(response.tools_used)
            
            # Add tool results to context and get final response
            messages.append(Message(role="assistant", content=response.content))
            messages.append(Message(
                role="system",
                content=f"Tool execution results: {json.dumps(tool_results)}"
            ))
            
            response = await self.assistant.generate_response(messages)
        
        return response
    
    def _select_relevant_tools(self, query: str) -> List[ToolDefinition]:
        """Select tools relevant to the query"""
        # Simple keyword-based selection, can be made more sophisticated
        relevant_tools = []
        
        query_lower = query.lower()
        
        # Map keywords to tool categories
        keyword_map = {
            'quote': ['get_quote', 'batch_quotes'],
            'price': ['get_quote', 'get_historical'],
            'historical': ['get_historical'],
            'chart': ['get_historical', 'calculate_sma', 'calculate_rsi'],
            'technical': ['calculate_sma', 'calculate_rsi'],
            'news': ['get_news'],
            'sentiment': ['analyze_sentiment'],
            'option': ['get_options_chain'],
            'crypto': ['get_crypto_data']
        }
        
        # Find matching tools
        for keyword, tool_names in keyword_map.items():
            if keyword in query_lower:
                for tool_name in tool_names:
                    tool = self.tool_registry.get_tool(tool_name)
                    if tool and tool not in relevant_tools:
                        relevant_tools.append(tool)
        
        # If no specific tools found, provide basic market data tools
        if not relevant_tools:
            default_tools = ['get_quote', 'get_news']
            for tool_name in default_tools:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    relevant_tools.append(tool)
        
        return relevant_tools
    
    async def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute requested tools"""
        results = {}
        
        for tool_call in tool_calls:
            tool_name = tool_call.get('name')
            parameters = tool_call.get('parameters', {})
            
            tool_def = self.tool_registry.get_tool(tool_name)
            handler = self.tool_registry.get_handler(tool_name)
            
            if not tool_def or not handler:
                results[tool_name] = {'error': f'Tool {tool_name} not found'}
                continue
            
            try:
                # Validate parameters
                validated_params = ParameterValidator.validate_parameters(
                    tool_def, parameters
                )
                
                # Execute tool
                result = await handler(**validated_params)
                results[tool_name] = result
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                results[tool_name] = {'error': str(e)}
        
        return results