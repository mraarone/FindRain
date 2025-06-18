# api/data/stream_client.py
class StreamClient:
    """Client for connecting to WebSocket stream"""
    
    def __init__(self, url: str = "ws://localhost:8765"):
        self.url = url
        self.websocket = None
        self.running = False
        self.handlers = {}
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.running = True
            
            # Start message handler
            asyncio.create_task(self._handle_messages())
            
            logger.info(f"Connected to WebSocket server at {self.url}")
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
    
    async def subscribe(self, symbols: List[str], data_types: List[str] = None):
        """Subscribe to symbols"""
        if not self.websocket:
            raise ConnectionError("Not connected to server")
        
        await self.websocket.send(json.dumps({
            'type': 'subscribe',
            'symbols': symbols,
            'data_types': data_types or ['quotes']
        }))
    
    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from symbols"""
        if not self.websocket:
            raise ConnectionError("Not connected to server")
        
        await self.websocket.send(json.dumps({
            'type': 'unsubscribe',
            'symbols': symbols
        }))
    
    def on(self, event_type: str, handler):
        """Register event handler"""
        self.handlers[event_type] = handler
    
    async def _handle_messages(self):
        """Handle incoming messages"""
        while self.running:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                event_type = data.get('type')
                if event_type in self.handlers:
                    await self.handlers[event_type](data)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.info("Connection closed")
                break
            except Exception as e:
                logger.error(f"Error handling message: {e}")


# Example usage
async def example_stream_usage():
    """Example of using the streaming client"""
    client = StreamClient()
    
    # Define handlers
    async def on_quote(data):
        print(f"Quote update: {data['symbol']} @ ${data['price']}")
    
    async def on_news(data):
        print(f"News: {data['headline']}")
    
    # Register handlers
    client.on('market_data', on_quote)
    client.on('news', on_news)
    
    try:
        # Connect and subscribe
        await client.connect()
        await client.subscribe(['AAPL', 'GOOGL', 'MSFT'], ['quotes', 'news'])
        
        # Keep running
        await asyncio.sleep(60)
        
    finally:
        await client.disconnect()