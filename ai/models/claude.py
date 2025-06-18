# ai/models/claude.py
import anthropic
from typing import Dict, List, Any, Optional
import json

from ..assistant import BaseAIAssistant, Message, AIResponse
from ...mcp.protocol import ToolDefinition

class ClaudeAssistant(BaseAIAssistant):
    """Claude AI assistant implementation"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__("Claude", api_key, config)
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = config.get('model', 'claude-3-opus-20240229')
        self.max_tokens = config.get('max_tokens', 4096)
        
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> AIResponse:
        """Generate response using Claude API"""
        try:
            # Convert messages to Claude format
            claude_messages = []
            for msg in messages:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Prepare tools if available
            if tools:
                tools_description = self._prepare_tools_for_claude(tools)
                # Add tool descriptions to system message
                system_message = (
                    "You are a financial analysis assistant with access to the following tools:\n\n" +
                    tools_description + "\n\n" +
                    "Use these tools when needed to provide accurate financial data and analysis."
                )
                claude_messages.insert(0, {"role": "system", "content": system_message})
            
            # Call Claude API
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                messages=claude_messages,
                max_tokens=self.max_tokens,
                temperature=kwargs.get('temperature', 0.7)
            )
            
            # Extract tool usage if any
            tools_used = self._extract_tool_usage(response.content)
            
            self.record_success()
            
            return AIResponse(
                content=response.content[0].text,
                model=self.model,
                usage={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                },
                tools_used=tools_used,
                confidence=0.95  # Claude typically has high confidence
            )
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            self.record_error()
            raise
    
    def _prepare_tools_for_claude(self, tools: List[ToolDefinition]) -> str:
        """Prepare tool descriptions for Claude"""
        descriptions = []
        for tool in tools:
            desc = f"- **{tool.name}**: {tool.description}\n"
            if tool.parameters:
                desc += "  Parameters:\n"
                for param in tool.parameters:
                    desc += f"    - {param.name} ({param.type.__name__}): {param.description}"
                    if param.required:
                        desc += " [required]"
                    desc += "\n"
            descriptions.append(desc)
        return "\n".join(descriptions)
    
    def _extract_tool_usage(self, content: str) -> List[str]:
        """Extract tool usage from response content"""
        # Simple extraction based on tool call patterns
        tools_used = []
        # Implementation would parse the response for tool calls
        return tools_used
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Claude's capabilities"""
        return {
            'strengths': [
                'long_form_analysis',
                'complex_reasoning',
                'technical_analysis',
                'report_generation',
                'code_generation'
            ],
            'context_window': 200000,
            'supports_vision': True,
            'supports_tools': True,
            'best_for': 'detailed_financial_analysis'
        }


# ai/models/chatgpt.py
import openai
from typing import Dict, List, Any, Optional
import json

from ..assistant import BaseAIAssistant, Message, AIResponse
from ...mcp.protocol import ToolDefinition

class ChatGPTAssistant(BaseAIAssistant):
    """ChatGPT/OpenAI assistant implementation"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__("ChatGPT", api_key, config)
        openai.api_key = api_key
        self.model = config.get('model', 'gpt-4-turbo-preview')
        self.max_tokens = config.get('max_tokens', 4096)
        
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> AIResponse:
        """Generate response using OpenAI API"""
        try:
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Prepare function calling if tools available
            functions = None
            if tools:
                functions = self._convert_tools_to_functions(tools)
            
            # Call OpenAI API
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=openai_messages,
                functions=functions,
                function_call="auto" if functions else None,
                max_tokens=self.max_tokens,
                temperature=kwargs.get('temperature', 0.7)
            )
            
            # Handle function calls
            tools_used = []
            content = response.choices[0].message.content
            
            if response.choices[0].message.get('function_call'):
                function_call = response.choices[0].message.function_call
                tools_used.append(function_call.name)
                # Here you would execute the function and get results
                
            self.record_success()
            
            return AIResponse(
                content=content,
                model=self.model,
                usage=response.usage.to_dict(),
                tools_used=tools_used,
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            self.record_error()
            raise
    
    def _convert_tools_to_functions(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function format"""
        functions = []
        for tool in tools:
            function = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            for param in tool.parameters:
                param_def = {
                    "type": self._get_openai_type(param.type),
                    "description": param.description
                }
                if param.choices:
                    param_def["enum"] = param.choices
                
                function["parameters"]["properties"][param.name] = param_def
                
                if param.required:
                    function["parameters"]["required"].append(param.name)
            
            functions.append(function)
        
        return functions
    
    def _get_openai_type(self, python_type) -> str:
        """Convert Python type to OpenAI parameter type"""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        return type_map.get(python_type, "string")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get ChatGPT's capabilities"""
        return {
            'strengths': [
                'balanced_analysis',
                'function_calling',
                'general_knowledge',
                'conversational',
                'quick_responses'
            ],
            'context_window': 128000,
            'supports_vision': True,
            'supports_tools': True,
            'best_for': 'general_financial_queries'
        }


