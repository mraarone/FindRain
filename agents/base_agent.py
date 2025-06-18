# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20

@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    requires_response: bool = False
    correlation_id: Optional[str] = None
    
class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, description: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.capabilities: List[str] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self.orchestrator = None
        self.tools_registry = None
        self.created_at = datetime.utcnow()
        self.stats = {
            'messages_processed': 0,
            'messages_sent': 0,
            'errors': 0,
            'uptime_seconds': 0
        }
        
    @abstractmethod
    async def initialize(self):
        """Initialize the agent"""
        pass
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process an incoming message"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
    
    async def start(self):
        """Start the agent"""
        try:
            await self.initialize()
            self.running = True
            logger.info(f"Agent {self.name} started")
            
            # Start message processing loop
            asyncio.create_task(self._message_loop())
            
        except Exception as e:
            logger.error(f"Failed to start agent {self.name}: {e}")
            self.status = AgentStatus.ERROR
            raise
    
    async def stop(self):
        """Stop the agent"""
        self.running = False
        self.status = AgentStatus.OFFLINE
        logger.info(f"Agent {self.name} stopped")
    
    async def _message_loop(self):
        """Main message processing loop"""
        while self.running:
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                self.status = AgentStatus.BUSY
                self.stats['messages_processed'] += 1
                
                # Process the message
                response = await self.process_message(message)
                
                # Send response if required
                if message.requires_response and response:
                    await self.send_message(
                        recipient=message.sender,
                        content=response.content,
                        correlation_id=message.id
                    )
                
                self.status = AgentStatus.IDLE
                
            except asyncio.TimeoutError:
                # No messages, continue
                pass
            except Exception as e:
                logger.error(f"Error in message loop for {self.name}: {e}")
                self.stats['errors'] += 1
                self.status = AgentStatus.ERROR
    
    async def send_message(
        self,
        recipient: str,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_response: bool = False,
        correlation_id: Optional[str] = None
    ) -> Optional[AgentMessage]:
        """Send a message to another agent"""
        message = AgentMessage(
            sender=self.id,
            recipient=recipient,
            content=content,
            priority=priority,
            requires_response=requires_response,
            correlation_id=correlation_id
        )
        
        self.stats['messages_sent'] += 1
        
        if self.orchestrator:
            return await self.orchestrator.route_message(message)
        else:
            logger.warning(f"No orchestrator set for agent {self.name}")
            return None
    
    async def broadcast_message(
        self,
        content: Dict[str, Any],
        agent_type: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ):
        """Broadcast a message to multiple agents"""
        if self.orchestrator:
            await self.orchestrator.broadcast_message(
                sender=self.id,
                content=content,
                agent_type=agent_type,
                priority=priority
            )
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self.handlers[message_type] = handler
    
    def set_orchestrator(self, orchestrator):
        """Set the orchestrator reference"""
        self.orchestrator = orchestrator
    
    def set_tools_registry(self, registry):
        """Set the tools registry reference"""
        self.tools_registry = registry
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and statistics"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'capabilities': self.capabilities,
            'stats': self.stats,
            'created_at': self.created_at.isoformat(),
            'uptime_seconds': (datetime.utcnow() - self.created_at).total_seconds()
        }


