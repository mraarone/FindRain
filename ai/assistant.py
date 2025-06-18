# ai/assistant.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
import asyncio

from ..mcp.protocol import ToolDefinition, ToolRegistry

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Message structure for AI conversations"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AIResponse:
    """Response from AI model"""
    content: str
    model: str
    usage: Dict[str, int]  # tokens used
    tools_used: List[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

class BaseAIAssistant(ABC):
    """Base class for AI assistants"""
    
    def __init__(self, model_name: str, api_key: str, config: Dict[str, Any]):
        self.model_name = model_name
        self.api_key = api_key
        self.config = config
        self.conversation_history: List[Message] = []
        self.tool_registry: Optional[ToolRegistry] = None
        self.available = True
        self.error_count = 0
        self.success_count = 0
        
    def set_tool_registry(self, registry: ToolRegistry):
        """Set the tool registry for this assistant"""
        self.tool_registry = registry
        
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> AIResponse:
        """Generate response from the AI model"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get model capabilities and specializations"""
        pass
    
    def add_message(self, message: Message):
        """Add message to conversation history"""
        self.conversation_history.append(message)
        
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        
    def record_success(self):
        """Record successful API call"""
        self.success_count += 1
        self.error_count = 0
        self.available = True
        
    def record_error(self):
        """Record API error"""
        self.error_count += 1
        if self.error_count >= 3:
            self.available = False
            logger.warning(f"{self.model_name} marked as unavailable after {self.error_count} errors")


