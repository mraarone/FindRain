# agents/orchestrator.py
from typing import Dict, List, Any, Optional, Set
import asyncio
from collections import defaultdict
import logging

from .base_agent import BaseAgent, AgentMessage, AgentStatus, MessagePriority
from .registry import AgentRegistry, ToolRegistry

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
    """Orchestrator agent that coordinates all other agents"""
    
    def __init__(self, agent_registry: AgentRegistry, tool_registry: ToolRegistry):
        super().__init__(
            name="Orchestrator",
            description="Coordinates agent activities and routes messages"
        )
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.routing_table: Dict[str, str] = {}  # capability -> agent_id
        self.message_buffer: Dict[str, List[AgentMessage]] = defaultdict(list)
        self.capabilities = [
            "route_message",
            "broadcast_message",
            "coordinate_agents",
            "manage_workflows",
            "monitor_agents"
        ]
        
    async def initialize(self):
        """Initialize the orchestrator"""
        logger.info("Orchestrator initialized")
        
        # Build routing table
        await self._build_routing_table()
        
        # Start monitoring
        asyncio.create_task(self._monitor_agents())
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process orchestrator-specific messages"""
        msg_type = message.content.get('type')
        
        if msg_type == 'user_query':
            return await self._handle_user_query(message)
        elif msg_type == 'workflow_request':
            return await self._handle_workflow_request(message)
        elif msg_type == 'status_request':
            return await self._handle_status_request(message)
        else:
            # Route to appropriate agent
            return await self.route_message(message)
    
    async def route_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Route message to appropriate agent"""
        try:
            # Priority routing
            if message.priority == MessagePriority.CRITICAL:
                return await self._handle_critical_message(message)
            
            # Find target agent
            if message.recipient:
                # Direct routing
                agent = self.agent_registry.get_agent(message.recipient)
                if agent:
                    await agent.message_queue.put(message)
                    logger.debug(f"Routed message to {agent.name}")
                else:
                    logger.warning(f"Agent {message.recipient} not found")
                    return None
            else:
                # Capability-based routing
                capability = message.content.get('required_capability')
                if capability:
                    agent_id = self.routing_table.get(capability)
                    if agent_id:
                        agent = self.agent_registry.get_agent(agent_id)
                        if agent:
                            await agent.message_queue.put(message)
                            logger.debug(f"Routed to {agent.name} for {capability}")
                        else:
                            logger.warning(f"No agent found for capability {capability}")
                else:
                    # Broadcast to relevant agents
                    await self._broadcast_to_relevant_agents(message)
            
            return None
            
        except Exception as e:
            logger.error(f"Error routing message: {e}")
            return None
    
    async def broadcast_message(
        self,
        sender: str,
        content: Dict[str, Any],
        agent_type: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ):
        """Broadcast message to multiple agents"""
        message = AgentMessage(
            sender=sender,
            content=content,
            priority=priority
        )
        
        agents = self.agent_registry.get_all_agents()
        
        for agent in agents:
            if agent.id == sender:  # Don't send to self
                continue
                
            if agent_type and agent_type not in agent.__class__.__name__:
                continue
            
            await agent.message_queue.put(message)
        
        logger.info(f"Broadcasted message from {sender} to {len(agents)} agents")
    
    async def _handle_user_query(self, message: AgentMessage) -> AgentMessage:
        """Handle user queries by coordinating multiple agents"""
        query = message.content.get('query', '')
        
        # Analyze query to determine required capabilities
        required_capabilities = self._analyze_query(query)
        
        # Create workflow
        workflow = await self._create_workflow(required_capabilities)
        
        # Execute workflow
        results = await self._execute_workflow(workflow, message)
        
        # Aggregate results
        response = self._aggregate_results(results)
        
        return AgentMessage(
            sender=self.id,
            recipient=message.sender,
            content={
                'type': 'query_response',
                'response': response,
                'agents_used': [r['agent'] for r in results],
                'status': 'success'
            }
        )
    
    def _analyze_query(self, query: str) -> List[str]:
        """Analyze query to determine required capabilities"""
        query_lower = query.lower()
        required = []
        
        # Map keywords to capabilities
        capability_keywords = {
            'quote': ['get_quote', 'market_data'],
            'price': ['get_quote', 'market_data'],
            'news': ['get_news', 'analyze_sentiment'],
            'technical': ['technical_analysis'],
            'portfolio': ['portfolio_analysis'],
            'create': ['create_tool', 'create_agent'],
            'analyze': ['analyze_data', 'generate_report']
        }
        
        for keyword, capabilities in capability_keywords.items():
            if keyword in query_lower:
                required.extend(capabilities)
        
        return list(set(required))  # Remove duplicates
    
    async def _create_workflow(self, capabilities: List[str]) -> List[Dict[str, Any]]:
        """Create workflow based on required capabilities"""
        workflow = []
        
        for capability in capabilities:
            agent_id = self.routing_table.get(capability)
            if agent_id:
                workflow.append({
                    'agent_id': agent_id,
                    'capability': capability,
                    'dependencies': []  # Could add dependency analysis
                })
        
        return workflow
    
    async def _execute_workflow(
        self, 
        workflow: List[Dict[str, Any]], 
        original_message: AgentMessage
    ) -> List[Dict[str, Any]]:
        """Execute workflow steps"""
        results = []
        
        # Execute in parallel where possible
        tasks = []
        for step in workflow:
            agent_id = step['agent_id']
            capability = step['capability']
            
            # Create task message
            task_message = AgentMessage(
                sender=self.id,
                recipient=agent_id,
                content={
                    'type': capability,
                    'original_query': original_message.content.get('query'),
                    'context': original_message.content.get('context', {})
                },
                requires_response=True
            )
            
            # Send and collect response
            task = asyncio.create_task(self._execute_task(agent_id, task_message))
            tasks.append((agent_id, task))
        
        # Wait for all tasks
        for agent_id, task in tasks:
            try:
                response = await task
                if response:
                    results.append({
                        'agent': agent_id,
                        'response': response.content
                    })
            except Exception as e:
                logger.error(f"Task execution error for {agent_id}: {e}")
        
        return results
    
    async def _execute_task(
        self, 
        agent_id: str, 
        message: AgentMessage
    ) -> Optional[AgentMessage]:
        """Execute a single task and wait for response"""
        agent = self.agent_registry.get_agent(agent_id)
        if not agent:
            return None
        
        # Send message
        await agent.message_queue.put(message)
        
        # Wait for response (with timeout)
        try:
            # Simple response collection - in production would use correlation IDs
            response = await asyncio.wait_for(
                self._wait_for_response(message.id),
                timeout=30.0
            )
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for response from {agent_id}")
            return None
    
    async def _wait_for_response(self, correlation_id: str) -> Optional[AgentMessage]:
        """Wait for a response with specific correlation ID"""
        # This is simplified - in production would use proper response tracking
        await asyncio.sleep(1)  # Simulate processing
        return None
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple agents"""
        aggregated = {
            'summary': '',
            'data': {},
            'insights': []
        }
        
        for result in results:
            response = result['response']
            
            # Aggregate based on response type
            if 'data' in response:
                aggregated['data'].update(response['data'])
            
            if 'insights' in response:
                aggregated['insights'].extend(response['insights'])
            
            if 'summary' in response:
                aggregated['summary'] += response['summary'] + '\n'
        
        return aggregated
    
    async def _build_routing_table(self):
        """Build capability to agent routing table"""
        agents = self.agent_registry.get_all_agents()
        
        for agent in agents:
            capabilities = agent.get_capabilities()
            for capability in capabilities:
                # For now, first agent wins for a capability
                # Could implement more sophisticated routing
                if capability not in self.routing_table:
                    self.routing_table[capability] = agent.id
        
        logger.info(f"Built routing table with {len(self.routing_table)} entries")
    
    async def _monitor_agents(self):
        """Monitor agent health and performance"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                agents = self.agent_registry.get_all_agents()
                unhealthy = []
                
                for agent in agents:
                    if agent.status == AgentStatus.ERROR:
                        unhealthy.append(agent.name)
                    
                    # Check message queue size
                    if agent.message_queue.qsize() > 100:
                        logger.warning(
                            f"Agent {agent.name} has {agent.message_queue.qsize()} pending messages"
                        )
                
                if unhealthy:
                    logger.warning(f"Unhealthy agents: {unhealthy}")
                    
            except Exception as e:
                logger.error(f"Error in agent monitoring: {e}")
    
    async def _handle_critical_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle critical priority messages"""
        logger.info(f"Handling critical message: {message.content.get('type')}")
        
        # Critical messages get processed immediately
        # Could implement special handling like bypassing queues
        return await self.route_message(message)
    
    async def _broadcast_to_relevant_agents(self, message: AgentMessage):
        """Broadcast to agents that might be interested"""
        msg_type = message.content.get('type')
        
        # Determine relevant agents based on message type
        relevant_agents = []
        
        for agent in self.agent_registry.get_all_agents():
            # Simple relevance check - could be more sophisticated
            if any(capability in msg_type for capability in agent.get_capabilities()):
                relevant_agents.append(agent)
        
        # Send to relevant agents
        for agent in relevant_agents:
            await agent.message_queue.put(message)
        
        logger.debug(f"Broadcasted to {len(relevant_agents)} relevant agents")
    
    def get_capabilities(self) -> List[str]:
        """Return orchestrator capabilities"""
        return self.capabilities
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        agents = self.agent_registry.get_all_agents()
        
        status = {
            'orchestrator': self.get_status(),
            'agents': {
                agent.name: agent.get_status() 
                for agent in agents
            },
            'routing_table_size': len(self.routing_table),
            'total_agents': len(agents),
            'healthy_agents': sum(
                1 for agent in agents 
                if agent.status != AgentStatus.ERROR
            )
        }
        
        return status


