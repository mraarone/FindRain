# agents/tool_creator.py
import ast
import textwrap
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent, AgentMessage, AgentStatus
from ..mcp.protocol import ToolDefinition, ToolParameter, ToolCategory
from ..ai.assistant import Message

class ToolCreatorAgent(BaseAgent):
    """Agent responsible for creating new MCP tools"""
    
    def __init__(self):
        super().__init__(
            name="ToolCreator",
            description="Creates, develops, and debugs MCP tools as needed"
        )
        self.capabilities = [
            "create_tool",
            "update_tool",
            "debug_tool",
            "generate_tool_code",
            "validate_tool"
        ]
        self.ai_assistant = None
        
    async def initialize(self):
        """Initialize the tool creator agent"""
        logger.info("Tool Creator Agent initialized")
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process tool creation requests"""
        msg_type = message.content.get('type')
        
        if msg_type == 'create_tool':
            return await self._handle_create_tool(message)
        elif msg_type == 'update_tool':
            return await self._handle_update_tool(message)
        elif msg_type == 'debug_tool':
            return await self._handle_debug_tool(message)
        else:
            logger.warning(f"Unknown message type: {msg_type}")
            return None
    
    async def _handle_create_tool(self, message: AgentMessage) -> AgentMessage:
        """Handle tool creation request"""
        try:
            tool_spec = message.content.get('spec', {})
            
            # Extract tool details
            tool_name = tool_spec.get('name')
            description = tool_spec.get('description')
            category = tool_spec.get('category', 'MARKET_DATA')
            parameters = tool_spec.get('parameters', [])
            
            # Generate tool definition
            tool_def = await self._generate_tool_definition(
                tool_name, description, category, parameters
            )
            
            # Generate implementation code
            implementation = await self._generate_tool_implementation(tool_def)
            
            # Validate the tool
            validation_result = await self._validate_tool(tool_def, implementation)
            
            if validation_result['valid']:
                # Register the tool
                if self.tools_registry:
                    self.tools_registry.register(tool_def, implementation['handler'])
                
                return AgentMessage(
                    sender=self.id,
                    recipient=message.sender,
                    content={
                        'type': 'tool_created',
                        'tool': tool_def.to_dict(),
                        'implementation': implementation['code'],
                        'status': 'success'
                    }
                )
            else:
                return AgentMessage(
                    sender=self.id,
                    recipient=message.sender,
                    content={
                        'type': 'tool_creation_failed',
                        'errors': validation_result['errors'],
                        'status': 'error'
                    }
                )
                
        except Exception as e:
            logger.error(f"Error creating tool: {e}")
            return AgentMessage(
                sender=self.id,
                recipient=message.sender,
                content={
                    'type': 'error',
                    'error': str(e),
                    'status': 'error'
                }
            )
    
    async def _generate_tool_definition(
        self,
        name: str,
        description: str,
        category: str,
        parameters: List[Dict[str, Any]]
    ) -> ToolDefinition:
        """Generate a tool definition"""
        
        # Convert parameters to ToolParameter objects
        tool_params = []
        for param in parameters:
            tool_param = ToolParameter(
                name=param['name'],
                type=self._get_python_type(param['type']),
                description=param['description'],
                required=param.get('required', True),
                default=param.get('default'),
                choices=param.get('choices'),
                min_value=param.get('min_value'),
                max_value=param.get('max_value')
            )
            tool_params.append(tool_param)
        
        # Create tool definition
        tool_def = ToolDefinition(
            name=name,
            category=ToolCategory[category.upper()],
            description=description,
            parameters=tool_params,
            returns=self._generate_return_schema(name),
            examples=self._generate_examples(name, tool_params),
            cache_timeout=300
        )
        
        return tool_def
    
    async def _generate_tool_implementation(
        self, 
        tool_def: ToolDefinition
    ) -> Dict[str, Any]:
        """Generate tool implementation code"""
        
        # Generate function signature
        params_str = ", ".join([
            f"{p.name}: {p.type.__name__}" + 
            (f" = {repr(p.default)}" if p.default is not None else "")
            for p in tool_def.parameters
        ])
        
        # Generate implementation code
        code = f"""
async def {tool_def.name}({params_str}) -> Dict[str, Any]:
    '''
    {tool_def.description}
    
    Parameters:
{self._generate_param_docs(tool_def.parameters)}
    
    Returns:
        Dict containing {', '.join(tool_def.returns.keys())}
    '''
    try:
        # Implementation logic here
        result = {{}}
        
        # TODO: Add actual implementation based on tool type
        # This is a placeholder that should be replaced with actual logic
        
        return result
        
    except Exception as e:
        logger.error(f"Error in {tool_def.name}: {{e}}")
        raise
"""
        
        # Create the function object
        exec_globals = {'Dict': Dict, 'Any': Any, 'logger': logger}
        exec(textwrap.dedent(code), exec_globals)
        handler = exec_globals[tool_def.name]
        
        return {
            'code': code,
            'handler': handler
        }
    
    def _generate_param_docs(self, parameters: List[ToolParameter]) -> str:
        """Generate parameter documentation"""
        docs = []
        for param in parameters:
            doc = f"        {param.name} ({param.type.__name__}): {param.description}"
            if not param.required:
                doc += f" (optional, default: {param.default})"
            docs.append(doc)
        return "\n".join(docs)
    
    def _get_python_type(self, type_str: str) -> type:
        """Convert string type to Python type"""
        type_map = {
            'str': str,
            'string': str,
            'int': int,
            'integer': int,
            'float': float,
            'number': float,
            'bool': bool,
            'boolean': bool,
            'list': list,
            'array': list,
            'dict': dict,
            'object': dict
        }
        return type_map.get(type_str.lower(), str)
    
    def _generate_return_schema(self, tool_name: str) -> Dict[str, Any]:
        """Generate return schema based on tool name"""
        # Basic schemas for common tool types
        if 'quote' in tool_name.lower():
            return {
                'symbol': 'string',
                'price': 'number',
                'timestamp': 'string'
            }
        elif 'historical' in tool_name.lower():
            return {
                'data': 'array',
                'symbol': 'string',
                'period': 'string'
            }
        else:
            return {
                'result': 'any',
                'timestamp': 'string'
            }
    
    def _generate_examples(
        self, 
        tool_name: str, 
        parameters: List[ToolParameter]
    ) -> List[Dict[str, Any]]:
        """Generate usage examples"""
        example_params = {}
        for param in parameters:
            if param.type == str:
                example_params[param.name] = "AAPL" if 'symbol' in param.name else "example"
            elif param.type == int:
                example_params[param.name] = 10
            elif param.type == float:
                example_params[param.name] = 100.0
            elif param.type == bool:
                example_params[param.name] = True
        
        return [{
            'request': example_params,
            'response': self._generate_return_schema(tool_name)
        }]
    
    async def _validate_tool(
        self, 
        tool_def: ToolDefinition, 
        implementation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate tool implementation"""
        errors = []
        
        try:
            # Check if handler is callable
            if not callable(implementation['handler']):
                errors.append("Handler is not callable")
            
            # Check if handler is async
            if not asyncio.iscoroutinefunction(implementation['handler']):
                errors.append("Handler must be async")
            
            # Validate code syntax
            try:
                ast.parse(implementation['code'])
            except SyntaxError as e:
                errors.append(f"Syntax error in code: {e}")
            
            # TODO: Add more validation checks
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return self.capabilities


