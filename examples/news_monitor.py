# examples/news_monitor.py
"""
Real-time News Monitoring System

Monitors news for portfolio holdings and market events with AI analysis.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
import logging

from financial_platform_sdk import FinancialDataClient, StreamClient, AIAssistant

logger = logging.getLogger(__name__)

class NewsMonitor:
    """Real-time news monitoring with AI analysis"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        self.client = FinancialDataClient(api_key)
        self.stream_client = StreamClient()
        self.ai_assistant = AIAssistant(self.client)
        self.config = config
        self.monitored_symbols: Set[str] = set()
        self.alert_handlers = []
        self.running = False
        
    def add_symbols(self, symbols: List[str]):
        """Add symbols to monitor"""
        self.monitored_symbols.update(symbols)
        logger.info(f"Monitoring {len(self.monitored_symbols)} symbols")
        
    def add_alert_handler(self, handler):
        """Add handler for news alerts"""
        self.alert_handlers.append(handler)
        
    async def start(self):
        """Start monitoring"""
        self.running = True
        logger.info("Starting news monitor...")
        
        # Connect to stream
        await self.stream_client.connect()
        await self.stream_client.subscribe(list(self.monitored_symbols), ['news'])
        
        # Register handlers
        self.stream_client.on('news', self._handle_news)
        
        # Start periodic analysis
        asyncio.create_task(self._periodic_analysis())
        
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        await self.stream_client.disconnect()
        
    async def _handle_news(self, data: Dict[str, Any]):
        """Handle incoming news"""
        try:
            symbol = data.get('symbol')
            headline = data.get('headline')
            
            # Quick sentiment check
            sentiment = await self._analyze_sentiment(headline)
            
            # Check if significant
            if abs(sentiment['score']) > 0.7:
                alert = {
                    'type': 'significant_news',
                    'symbol': symbol,
                    'headline': headline,
                    'sentiment': sentiment,
                    'timestamp': datetime.utcnow()
                }
                
                await self._trigger_alert(alert)
                
                # Get detailed analysis for significant news
                detailed = await self._detailed_analysis(data, sentiment)
                if detailed['action_required']:
                    await self._trigger_alert({
                        'type': 'action_required',
                        'symbol': symbol,
                        'analysis': detailed,
                        'timestamp': datetime.utcnow()
                    })
                    
        except Exception as e:
            logger.error(f"Error handling news: {e}")
            
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        response = await self.ai_assistant.analyze_sentiment(text)
        return {
            'score': response.get('sentiment', 0),
            'confidence': response.get('confidence', 0.5)
        }
        
    async def _detailed_analysis(self, news_data: Dict, sentiment: Dict) -> Dict[str, Any]:
        """Detailed AI analysis of news impact"""
        prompt = f"""
        Analyze this news for market impact:
        
        Symbol: {news_data['symbol']}
        Headline: {news_data['headline']}
        Summary: {news_data.get('summary', 'N/A')}
        Sentiment Score: {sentiment['score']}
        
        Determine:
        1. Likely price impact (high/medium/low)
        2. Time horizon of impact (immediate/short-term/long-term)
        3. Action required (yes/no)
        4. Specific recommendations
        """
        
        response = await self.ai_assistant.analyze(prompt)
        
        return {
            'impact_level': response.get('impact_level', 'unknown'),
            'time_horizon': response.get('time_horizon', 'unknown'),
            'action_required': response.get('action_required', False),
            'recommendations': response.get('recommendations', [])
        }
        
    async def _periodic_analysis(self):
        """Periodic comprehensive analysis"""
        while self.running:
            try:
                await asyncio.sleep(self.config.get('analysis_interval', 3600))  # 1 hour
                
                # Get news summary for all symbols
                for symbol in self.monitored_symbols:
                    summary = await self._get_news_summary(symbol)
                    
                    if summary['significant_changes']:
                        await self._trigger_alert({
                            'type': 'periodic_summary',
                            'symbol': symbol,
                            'summary': summary,
                            'timestamp': datetime.utcnow()
                        })
                        
            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")
                
    async def _get_news_summary(self, symbol: str) -> Dict[str, Any]:
        """Get news summary for symbol"""
        # Get recent news
        news = await self.client.get_news(
            symbol=symbol,
            hours_back=self.config.get('summary_hours', 24)
        )
        
        if not news['articles']:
            return {'significant_changes': False}
            
        # Analyze trends
        sentiments = []
        for article in news['articles']:
            sentiment = await self._analyze_sentiment(article['title'])
            sentiments.append(sentiment['score'])
            
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        sentiment_trend = 'improving' if sentiments[-3:] > sentiments[:3] else 'declining'
        
        # Get AI summary
        prompt = f"""
        Summarize news sentiment for {symbol} over the last 24 hours:
        - {len(news['articles'])} articles
        - Average sentiment: {avg_sentiment:.2f}
        - Trend: {sentiment_trend}
        
        Provide a brief summary and indicate if any significant changes occurred.
        """
        
        ai_summary = await self.ai_assistant.analyze(prompt)
        
        return {
            'significant_changes': abs(avg_sentiment) > 0.5 or len(news['articles']) > 10,
            'article_count': len(news['articles']),
            'average_sentiment': avg_sentiment,
            'sentiment_trend': sentiment_trend,
            'ai_summary': ai_summary.get('summary', '')
        }
        
    async def _trigger_alert(self, alert: Dict[str, Any]):
        """Trigger alert to all handlers"""
        logger.info(f"Alert triggered: {alert['type']} for {alert.get('symbol', 'MARKET')}")
        
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")


# Example usage
async def example_news_monitor():
    """Example of using news monitor"""
    
    # Alert handler
    async def handle_alert(alert: Dict[str, Any]):
        print(f"\n🚨 ALERT: {alert['type']}")
        print(f"Symbol: {alert.get('symbol', 'N/A')}")
        
        if alert['type'] == 'significant_news':
            print(f"Headline: {alert['headline']}")
            print(f"Sentiment: {alert['sentiment']['score']:.2f}")
        elif alert['type'] == 'action_required':
            print(f"Action Required!")
            print(f"Analysis: {alert['analysis']}")
            
    # Configure monitor
    config = {
        'analysis_interval': 3600,  # 1 hour
        'summary_hours': 24,
        'alert_threshold': 0.7
    }
    
    monitor = NewsMonitor(api_key='your-api-key', config=config)
    
    # Add symbols to monitor
    monitor.add_symbols(['AAPL', 'GOOGL', 'TSLA', 'MSFT'])
    
    # Add alert handler
    monitor.add_alert_handler(handle_alert)
    
    try:
        # Start monitoring
        await monitor.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        await monitor.stop()


if __name__ == "__main__":
    asyncio.run(example_news_monitor())