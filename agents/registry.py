# agents/registry.py
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Registry for managing all agents in the system"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_history: List[Dict[str, Any]] = []
        
    async def register_agent(self, agent: BaseAgent) -> bool:
        """Register a new agent"""
        try:
            if agent.id in self.agents:
                logger.warning(f"Agent {agent.name} already registered")
                return False
            
            self.agents[agent.id] = agent
            
            # Record registration
            self.agent_history.append({
                'action': 'registered',
                'agent_id': agent.id,
                'agent_name': agent.name,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Registered agent: {agent.name} ({agent.id})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found")
                return False
            
            agent = self.agents[agent_id]
            await agent.stop()
            
            del self.agents[agent_id]
            
            # Record unregistration
            self.agent_history.append({
                'action': 'unregistered',
                'agent_id': agent_id,
                'agent_name': agent.name,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Unregistered agent: {agent.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering agent: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        for agent in self.agents.values():
            if agent.name == name:
                return agent
        return None
    
    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents"""
        return list(self.agents.values())
    
    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Get agents with specific capability"""
        matching_agents = []
        for agent in self.agents.values():
            if capability in agent.get_capabilities():
                matching_agents.append(agent)
        return matching_agents
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status and statistics"""
        return {
            'total_agents': len(self.agents),
            'agents': {
                agent_id: {
                    'name': agent.name,
                    'status': agent.status.value,
                    'capabilities': agent.get_capabilities()
                }
                for agent_id, agent in self.agents.items()
            },
            'history_entries': len(self.agent_history)
        }


