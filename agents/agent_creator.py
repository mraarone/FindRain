# agents/agent_creator.py
from typing import Dict, List, Any, Optional
import inspect
import importlib.util

from .base_agent import BaseAgent, AgentMessage

class AgentCreatorAgent(BaseAgent):
    """Agent responsible for creating new agents"""
    
    def __init__(self):
        super().__init__(
            name="AgentCreator",
            description="Creates new agents, generates features, and manages agent lifecycle"
        )
        self.capabilities = [
            "create_agent",
            "update_agent",
            "delete_agent",
            "generate_agent_code",
            "test_agent"
        ]
        self.agent_templates = self._load_agent_templates()
        
    async def initialize(self):
        """Initialize the agent creator"""
        logger.info("Agent Creator initialized")
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process agent creation requests"""
        msg_type = message.content.get('type')
        
        if msg_type == 'create_agent':
            return await self._handle_create_agent(message)
        elif msg_type == 'update_agent':
            return await self._handle_update_agent(message)
        elif msg_type == 'test_agent':
            return await self._handle_test_agent(message)
        else:
            return None
    
    async def _handle_create_agent(self, message: AgentMessage) -> AgentMessage:
        """Handle agent creation request"""
        try:
            spec = message.content.get('spec', {})
            
            # Check for conflicts
            conflicts = await self._check_conflicts(spec)
            if conflicts:
                return AgentMessage(
                    sender=self.id,
                    recipient=message.sender,
                    content={
                        'type': 'agent_creation_failed',
                        'conflicts': conflicts,
                        'status': 'error'
                    }
                )
            
            # Generate agent code
            agent_code = await self._generate_agent_code(spec)
            
            # Create and test agent
            agent_instance = await self._create_agent_instance(agent_code)
            
            # Register with orchestrator
            if self.orchestrator:
                await self.orchestrator.register_agent(agent_instance)
            
            return AgentMessage(
                sender=self.id,
                recipient=message.sender,
                content={
                    'type': 'agent_created',
                    'agent_id': agent_instance.id,
                    'agent_name': agent_instance.name,
                    'capabilities': agent_instance.get_capabilities(),
                    'status': 'success'
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return AgentMessage(
                sender=self.id,
                recipient=message.sender,
                content={
                    'type': 'error',
                    'error': str(e),
                    'status': 'error'
                }
            )
    
    async def _check_conflicts(self, spec: Dict[str, Any]) -> List[str]:
        """Check for conflicts with existing agents"""
        conflicts = []
        
        if self.orchestrator:
            existing_agents = await self.orchestrator.get_all_agents()
            
            # Check name conflicts
            for agent in existing_agents:
                if agent.name.lower() == spec.get('name', '').lower():
                    conflicts.append(f"Agent with name '{spec['name']}' already exists")
                
                # Check capability conflicts
                new_capabilities = set(spec.get('capabilities', []))
                existing_capabilities = set(agent.get_capabilities())
                
                overlapping = new_capabilities.intersection(existing_capabilities)
                if len(overlapping) > 3:  # Allow some overlap
                    conflicts.append(
                        f"Significant capability overlap with {agent.name}: {overlapping}"
                    )
        
        return conflicts
    
    async def _generate_agent_code(self, spec: Dict[str, Any]) -> str:
        """Generate Python code for new agent"""
        name = spec.get('name', 'CustomAgent')
        description = spec.get('description', 'Custom agent')
        capabilities = spec.get('capabilities', [])
        
        code = f'''
from typing import Dict, List, Any, Optional
from agents.base_agent import BaseAgent, AgentMessage
import logging

logger = logging.getLogger(__name__)

class {name}Agent(BaseAgent):
    """
    {description}
    """
    
    def __init__(self):
        super().__init__(
            name="{name}",
            description="""{description}"""
        )
        self.capabilities = {capabilities}
        
    async def initialize(self):
        """Initialize the agent"""
        logger.info(f"{{self.name}} agent initialized")
        
        # Register message handlers
        {self._generate_handler_registrations(spec)}
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming messages"""
        msg_type = message.content.get('type')
        
        if msg_type in self.handlers:
            return await self.handlers[msg_type](message)
        else:
            logger.warning(f"Unknown message type: {{msg_type}}")
            return None
    
    {self._generate_handler_methods(spec)}
    
    def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return self.capabilities
'''
        return code
    
    def _generate_handler_registrations(self, spec: Dict[str, Any]) -> str:
        """Generate handler registration code"""
        handlers = spec.get('handlers', {})
        registrations = []
        
        for msg_type in handlers:
            method_name = f"_handle_{msg_type}"
            registrations.append(
                f"self.register_handler('{msg_type}', self.{method_name})"
            )
        
        return "\n        ".join(registrations)
    
    def _generate_handler_methods(self, spec: Dict[str, Any]) -> str:
        """Generate handler method implementations"""
        handlers = spec.get('handlers', {})
        methods = []
        
        for msg_type, handler_spec in handlers.items():
            method_name = f"_handle_{msg_type}"
            method_code = f'''
    async def {method_name}(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle {msg_type} messages"""
        try:
            # Extract message content
            content = message.content
            
            # TODO: Implement {msg_type} logic
            result = {{
                'type': '{msg_type}_response',
                'status': 'success'
            }}
            
            return AgentMessage(
                sender=self.id,
                recipient=message.sender,
                content=result
            )
            
        except Exception as e:
            logger.error(f"Error handling {msg_type}: {{e}}")
            return AgentMessage(
                sender=self.id,
                recipient=message.sender,
                content={{
                    'type': 'error',
                    'error': str(e),
                    'status': 'error'
                }}
            )'''
            methods.append(method_code)
        
        return "\n".join(methods)
    
    async def _create_agent_instance(self, agent_code: str) -> BaseAgent:
        """Create agent instance from code"""
        # Write code to temporary module
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(agent_code)
            temp_file = f.name
        
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location("custom_agent", temp_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the agent class
            agent_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseAgent) and 
                    obj != BaseAgent):
                    agent_class = obj
                    break
            
            if not agent_class:
                raise ValueError("No agent class found in generated code")
            
            # Create instance
            agent = agent_class()
            return agent
            
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def _load_agent_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined agent templates"""
        return {
            'data_analyzer': {
                'name': 'DataAnalyzer',
                'description': 'Analyzes financial data and generates insights',
                'capabilities': ['analyze_data', 'generate_report', 'detect_patterns'],
                'handlers': {
                    'analyze_request': {},
                    'generate_report': {}
                }
            },
            'alert_monitor': {
                'name': 'AlertMonitor',
                'description': 'Monitors conditions and triggers alerts',
                'capabilities': ['monitor_conditions', 'send_alerts', 'manage_rules'],
                'handlers': {
                    'add_alert': {},
                    'remove_alert': {},
                    'check_conditions': {}
                }
            },
            'portfolio_optimizer': {
                'name': 'PortfolioOptimizer',
                'description': 'Optimizes portfolio allocation',
                'capabilities': ['optimize_allocation', 'risk_analysis', 'rebalance'],
                'handlers': {
                    'optimize': {},
                    'analyze_risk': {}
                }
            }
        }
    
    def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return self.capabilities


