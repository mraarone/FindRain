# api/data/streaming.py
import asyncio
import websockets
import json
import logging
from typing import Dict, Set, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import aioredis

logger = logging.getLogger(__name__)

@dataclass
class StreamSubscription:
    """Represents a streaming subscription"""
    client_id: str
    symbols: Set[str]
    data_types: Set[str]  # 'quotes', 'trades', 'orderbook', 'news'
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class WebSocketServer:
    """WebSocket server for real-time data streaming"""
    
    def __init__(self, host: str = "localhost", port: int = 8765, redis_url: str = None):
        self.host = host
        self.port = port
        self.redis_url = redis_url
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, StreamSubscription] = {}
        self.redis_client = None
        self.server = None
        self.running = False
        
    async def start(self):
        """Start the WebSocket server"""
        try:
            # Connect to Redis for pub/sub
            if self.redis_url:
                self.redis_client = await aioredis.create_redis_pool(self.redis_url)
            
            # Start server
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            self.running = True
            logger.info(f"WebSocket server started on {self.host}:{self.port}")
            
            # Start data streaming tasks
            asyncio.create_task(self._stream_market_data())
            asyncio.create_task(self._stream_news())
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop(self):
        """Stop the WebSocket server"""
        self.running = False
        
        # Close all client connections
        for client_id in list(self.clients.keys()):
            await self.disconnect_client(client_id)
        
        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Close Redis
        if self.redis_client:
            self.redis_client.close()
            await self.redis_client.wait_closed()
        
        logger.info("WebSocket server stopped")
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connection"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}_{datetime.utcnow().timestamp()}"
        self.clients[client_id] = websocket
        
        logger.info(f"New client connected: {client_id}")
        
        try:
            # Send welcome message
            await self.send_message(client_id, {
                'type': 'connection',
                'status': 'connected',
                'client_id': client_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Handle client messages
            async for message in websocket:
                await self.handle_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            await self.disconnect_client(client_id)
    
    async def handle_message(self, client_id: str, message: str):
        """Handle message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'subscribe':
                await self.handle_subscribe(client_id, data)
            elif msg_type == 'unsubscribe':
                await self.handle_unsubscribe(client_id, data)
            elif msg_type == 'ping':
                await self.send_message(client_id, {'type': 'pong'})
            else:
                await self.send_error(client_id, f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            await self.send_error(client_id, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self.send_error(client_id, str(e))
    
    async def handle_subscribe(self, client_id: str, data: Dict[str, Any]):
        """Handle subscription request"""
        symbols = set(data.get('symbols', []))
        data_types = set(data.get('data_types', ['quotes']))
        
        if not symbols:
            await self.send_error(client_id, "No symbols provided")
            return
        
        # Create or update subscription
        if client_id in self.subscriptions:
            sub = self.subscriptions[client_id]
            sub.symbols.update(symbols)
            sub.data_types.update(data_types)
        else:
            sub = StreamSubscription(
                client_id=client_id,
                symbols=symbols,
                data_types=data_types
            )
            self.subscriptions[client_id] = sub
        
        # Send confirmation
        await self.send_message(client_id, {
            'type': 'subscribed',
            'symbols': list(sub.symbols),
            'data_types': list(sub.data_types),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Client {client_id} subscribed to {symbols}")
    
    async def handle_unsubscribe(self, client_id: str, data: Dict[str, Any]):
        """Handle unsubscription request"""
        symbols = set(data.get('symbols', []))
        
        if client_id not in self.subscriptions:
            await self.send_error(client_id, "No active subscription")
            return
        
        sub = self.subscriptions[client_id]
        sub.symbols.difference_update(symbols)
        
        if not sub.symbols:
            del self.subscriptions[client_id]
        
        await self.send_message(client_id, {
            'type': 'unsubscribed',
            'symbols': list(symbols),
            'remaining': list(sub.symbols) if client_id in self.subscriptions else [],
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def send_message(self, client_id: str, data: Dict[str, Any]):
        """Send message to specific client"""
        if client_id in self.clients:
            try:
                await self.clients[client_id].send(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                await self.disconnect_client(client_id)
    
    async def send_error(self, client_id: str, error: str):
        """Send error message to client"""
        await self.send_message(client_id, {
            'type': 'error',
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def broadcast(self, data: Dict[str, Any], filter_func=None):
        """Broadcast message to all or filtered clients"""
        disconnected = []
        
        for client_id, websocket in self.clients.items():
            if filter_func and not filter_func(client_id):
                continue
            
            try:
                await websocket.send(json.dumps(data))
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            await self.disconnect_client(client_id)
    
    async def disconnect_client(self, client_id: str):
        """Disconnect and clean up client"""
        if client_id in self.clients:
            try:
                await self.clients[client_id].close()
            except:
                pass
            del self.clients[client_id]
        
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        
        logger.info(f"Client {client_id} disconnected and cleaned up")
    
    async def _stream_market_data(self):
        """Stream market data to subscribed clients"""
        while self.running:
            try:
                # Simulate market data updates (replace with actual data source)
                await asyncio.sleep(1)  # Update every second
                
                # Get market data for all subscribed symbols
                all_symbols = set()
                for sub in self.subscriptions.values():
                    all_symbols.update(sub.symbols)
                
                if not all_symbols:
                    continue
                
                # Generate market data (replace with actual data)
                for symbol in all_symbols:
                    market_data = {
                        'type': 'market_data',
                        'data_type': 'quote',
                        'symbol': symbol,
                        'price': 100 + (hash(symbol + str(datetime.utcnow())) % 100) / 100,
                        'volume': hash(symbol) % 1000000,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    # Send to subscribed clients
                    await self._send_to_subscribers(symbol, 'quotes', market_data)
                    
            except Exception as e:
                logger.error(f"Error streaming market data: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _stream_news(self):
        """Stream news updates to subscribed clients"""
        while self.running:
            try:
                # Check for news updates every 30 seconds
                await asyncio.sleep(30)
                
                # Get subscribed symbols for news
                news_symbols = set()
                for sub in self.subscriptions.values():
                    if 'news' in sub.data_types:
                        news_symbols.update(sub.symbols)
                
                if not news_symbols:
                    continue
                
                # Simulate news (replace with actual news source)
                for symbol in list(news_symbols)[:5]:  # Limit to 5 symbols per update
                    news_data = {
                        'type': 'news',
                        'symbol': symbol,
                        'headline': f"Breaking: {symbol} announces quarterly results",
                        'summary': f"{symbol} reported strong earnings...",
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    await self._send_to_subscribers(symbol, 'news', news_data)
                    
            except Exception as e:
                logger.error(f"Error streaming news: {e}")
                await asyncio.sleep(60)
    
    async def _send_to_subscribers(self, symbol: str, data_type: str, data: Dict[str, Any]):
        """Send data to clients subscribed to specific symbol and data type"""
        disconnected = []
        
        for client_id, sub in self.subscriptions.items():
            if symbol in sub.symbols and data_type in sub.data_types:
                if client_id in self.clients:
                    try:
                        await self.clients[client_id].send(json.dumps(data))
                    except Exception as e:
                        logger.error(f"Error sending to {client_id}: {e}")
                        disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            await self.disconnect_client(client_id)


