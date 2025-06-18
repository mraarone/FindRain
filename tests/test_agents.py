# tests/test_agents.py
import pytest
import asyncio
from agents.base_agent import BaseAgent, AgentMessage, MessagePriority
from agents.orchestrator import OrchestratorAgent
from agents.registry import AgentRegistry

class TestAgent(BaseAgent):
    """Test agent implementation"""
    
    def __init__(self):
        super().__init__("TestAgent", "Test agent")
        self.processed_messages = []
        
    async def initialize(self):
        pass
        
    async def process_message(self, message):
        self.processed_messages.append(message)
        return None
        
    def get_capabilities(self):
        return ["test_capability"]

@pytest.mark.asyncio
async def test_agent_messaging():
    """Test agent messaging system"""
    agent = TestAgent()
    await agent.start()
    
    # Send message
    message = AgentMessage(
        sender="test",
        content={"type": "test"},
        priority=MessagePriority.NORMAL
    )
    
    await agent.message_queue.put(message)
    await asyncio.sleep(0.1)  # Let message process
    
    assert len(agent.processed_messages) == 1
    assert agent.processed_messages[0].content["type"] == "test"
    
    await agent.stop()

@pytest.mark.asyncio
async def test_orchestrator_routing():
    """Test orchestrator message routing"""
    # Create registry and orchestrator
    agent_registry = AgentRegistry()
    tool_registry = Mock()
    orchestrator = OrchestratorAgent(agent_registry, tool_registry)
    
    # Create and register test agent
    test_agent = TestAgent()
    await agent_registry.register_agent(test_agent)
    await orchestrator.initialize()
    
    # Test routing
    message = AgentMessage(
        sender="user",
        recipient=test_agent.id,
        content={"test": "data"}
    )
    
    await orchestrator.route_message(message)
    await asyncio.sleep(0.1)
    
    assert test_agent.message_queue.qsize() == 1