# agents/communication.py
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import logging

from .base_agent import AgentMessage, MessagePriority

logger = logging.getLogger(__name__)

class MessageBus:
    """Central message bus for inter-agent communication"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_log: List[Dict[str, Any]] = []
        self.active = True
        
    async def publish(self, topic: str, message: AgentMessage):
        """Publish message to a topic"""
        if not self.active:
            return
        
        # Log message
        self.message_log.append({
            'topic': topic,
            'message_id': message.id,
            'sender': message.sender,
            'timestamp': message.timestamp.isoformat(),
            'priority': message.priority.value
        })
        
        # Notify subscribers
        if topic in self.subscribers:
            tasks = []
            for callback in self.subscribers[topic]:
                task = asyncio.create_task(callback(message))
                tasks.append(task)
            
            # Wait for all callbacks
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        
        self.subscribers[topic].append(callback)
        logger.debug(f"Subscribed to topic: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        if topic in self.subscribers:
            self.subscribers[topic].remove(callback)
            if not self.subscribers[topic]:
                del self.subscribers[topic]


class WebSocketBridge:
    """Bridge for WebSocket communication with external systems"""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.connections: Dict[str, Any] = {}  # websocket connections
        self.handlers: Dict[str, Callable] = {}
        
    async def handle_external_message(self, ws_message: Dict[str, Any]):
        """Handle message from external WebSocket client"""
        try:
            # Convert to AgentMessage
            agent_message = AgentMessage(
                sender="external",
                content=ws_message,
                priority=MessagePriority.NORMAL
            )
            
            # Publish to appropriate topic
            topic = ws_message.get('topic', 'external')
            await self.message_bus.publish(topic, agent_message)
            
        except Exception as e:
            logger.error(f"Error handling external message: {e}")
    
    async def send_to_external(self, connection_id: str, data: Dict[str, Any]):
        """Send data to external WebSocket client"""
        if connection_id in self.connections:
            try:
                ws = self.connections[connection_id]
                await ws.send(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending to external client: {e}")


class EventBus:
    """Event-driven communication system"""
    
    def __init__(self):
        self.events: asyncio.Queue = asyncio.Queue()
        self.handlers: Dict[str, List[Callable]] = {}
        self.running = False
        
    async def start(self):
        """Start event processing"""
        self.running = True
        asyncio.create_task(self._process_events())
    
    async def stop(self):
        """Stop event processing"""
        self.running = False
    
    async def emit(self, event_type: str, data: Any):
        """Emit an event"""
        await self.events.put({
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow()
        })
    
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    async def _process_events(self):
        """Process events from queue"""
        while self.running:
            try:
                event = await asyncio.wait_for(
                    self.events.get(),
                    timeout=1.0
                )
                
                event_type = event['type']
                if event_type in self.handlers:
                    for handler in self.handlers[event_type]:
                        asyncio.create_task(handler(event['data']))
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")