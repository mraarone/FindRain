# examples/trading_bot.py
"""
AI-Powered Trading Bot Example

This example demonstrates how to build a trading bot using the financial data platform
with AI decision-making capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from dataclasses import dataclass
from enum import Enum

# Import the platform SDK (would be installed as a package)
from financial_platform_sdk import (
    FinancialDataClient,
    StreamClient,
    AIAssistant,
    TechnicalIndicators
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class TradingSignal:
    """Trading signal data"""
    symbol: str
    signal: SignalType
    confidence: float
    price: float
    reason: str
    indicators: Dict[str, Any]
    timestamp: datetime

class TradingStrategy:
    """Base trading strategy class"""
    
    def __init__(self, name: str):
        self.name = name
        
    async def analyze(self, symbol: str, data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze data and generate trading signal"""
        raise NotImplementedError

class AITradingBot:
    """AI-powered trading bot"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        self.client = FinancialDataClient(api_key)
        self.stream_client = StreamClient()
        self.ai_assistant = AIAssistant(self.client)
        self.config = config
        self.portfolio = {}
        self.strategies = []
        self.running = False
        
    def add_strategy(self, strategy: TradingStrategy):
        """Add trading strategy"""
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.name}")
        
    async def start(self):
        """Start the trading bot"""
        logger.info("Starting AI Trading Bot...")
        self.running = True
        
        # Connect to streaming data
        await self.stream_client.connect()
        
        # Subscribe to symbols
        symbols = self.config.get('symbols', ['AAPL', 'GOOGL', 'MSFT'])
        await self.stream_client.subscribe(symbols, ['quotes', 'news'])
        
        # Register handlers
        self.stream_client.on('market_data', self._handle_market_data)
        self.stream_client.on('news', self._handle_news)
        
        # Start main trading loop
        await self._trading_loop()
        
    async def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping AI Trading Bot...")
        self.running = False
        await self.stream_client.disconnect()
        
    async def _trading_loop(self):
        """Main trading loop"""
        while self.running:
            try:
                # Analyze each symbol
                for symbol in self.config['symbols']:
                    await self._analyze_symbol(symbol)
                
                # Sleep before next iteration
                await asyncio.sleep(self.config.get('interval', 60))
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(5)
                
    async def _analyze_symbol(self, symbol: str):
        """Analyze a symbol and make trading decisions"""
        try:
            # Get current data
            quote = await self.client.get_quote(symbol)
            historical = await self.client.get_historical(
                symbol,
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow(),
                interval='1h'
            )
            
            # Get technical indicators
            indicators = await self._calculate_indicators(symbol, historical)
            
            # Get AI analysis
            ai_analysis = await self._get_ai_analysis(symbol, quote, indicators)
            
            # Run strategies
            signals = []
            for strategy in self.strategies:
                signal = await strategy.analyze(symbol, {
                    'quote': quote,
                    'historical': historical,
                    'indicators': indicators,
                    'ai_analysis': ai_analysis
                })
                if signal:
                    signals.append(signal)
            
            # Make trading decision
            if signals:
                await self._execute_trade_decision(signals)
                
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            
    async def _calculate_indicators(self, symbol: str, historical: List[Dict]) -> Dict[str, Any]:
        """Calculate technical indicators"""
        indicators = {}
        
        # Get various indicators from the API
        indicators['sma_20'] = await self.client.get_indicator(symbol, 'sma', period=20)
        indicators['rsi'] = await self.client.get_indicator(symbol, 'rsi', period=14)
        indicators['macd'] = await self.client.get_indicator(symbol, 'macd')
        indicators['bollinger'] = await self.client.get_indicator(symbol, 'bollinger')
        
        return indicators
        
    async def _get_ai_analysis(self, symbol: str, quote: Dict, indicators: Dict) -> Dict[str, Any]:
        """Get AI analysis for the symbol"""
        prompt = f"""
        Analyze {symbol} for trading opportunities:
        
        Current Price: ${quote['price']}
        Day Change: {quote['changePercent']}%
        
        Technical Indicators:
        - RSI: {indicators['rsi']['values'][-1]['value']}
        - SMA 20: {indicators['sma_20']['values'][-1]['value']}
        - MACD Signal: {indicators['macd']['values'][-1]['signal']}
        
        Provide trading recommendation (BUY/SELL/HOLD) with confidence level and reasoning.
        """
        
        response = await self.ai_assistant.analyze(prompt, context={
            'symbol': symbol,
            'indicators': indicators
        })
        
        return response
        
    async def _execute_trade_decision(self, signals: List[TradingSignal]):
        """Execute trading decision based on signals"""
        # Aggregate signals
        buy_signals = [s for s in signals if s.signal == SignalType.BUY]
        sell_signals = [s for s in signals if s.signal == SignalType.SELL]
        
        # Simple decision logic (can be made more sophisticated)
        if len(buy_signals) > len(sell_signals):
            strongest_buy = max(buy_signals, key=lambda s: s.confidence)
            await self._execute_buy(strongest_buy)
        elif len(sell_signals) > len(buy_signals):
            strongest_sell = max(sell_signals, key=lambda s: s.confidence)
            await self._execute_sell(strongest_sell)
        else:
            logger.info("Mixed signals - holding position")
            
    async def _execute_buy(self, signal: TradingSignal):
        """Execute buy order"""
        logger.info(f"BUY SIGNAL: {signal.symbol} @ ${signal.price}")
        logger.info(f"Confidence: {signal.confidence}, Reason: {signal.reason}")
        
        # In a real implementation, this would place an actual order
        # For demo, just update portfolio
        if signal.symbol not in self.portfolio:
            self.portfolio[signal.symbol] = {
                'quantity': 0,
                'avg_price': 0
            }
        
        # Simulate buying 10 shares
        quantity = 10
        self.portfolio[signal.symbol]['quantity'] += quantity
        self.portfolio[signal.symbol]['avg_price'] = signal.price
        
        logger.info(f"Bought {quantity} shares of {signal.symbol}")
        
    async def _execute_sell(self, signal: TradingSignal):
        """Execute sell order"""
        logger.info(f"SELL SIGNAL: {signal.symbol} @ ${signal.price}")
        logger.info(f"Confidence: {signal.confidence}, Reason: {signal.reason}")
        
        if signal.symbol in self.portfolio and self.portfolio[signal.symbol]['quantity'] > 0:
            # Simulate selling all shares
            quantity = self.portfolio[signal.symbol]['quantity']
            profit = (signal.price - self.portfolio[signal.symbol]['avg_price']) * quantity
            
            logger.info(f"Sold {quantity} shares of {signal.symbol}, Profit: ${profit:.2f}")
            
            self.portfolio[signal.symbol]['quantity'] = 0
            
    async def _handle_market_data(self, data: Dict[str, Any]):
        """Handle real-time market data"""
        symbol = data['symbol']
        price = data['price']
        
        # Check for significant price movements
        if symbol in self.portfolio:
            position = self.portfolio[symbol]
            if position['quantity'] > 0:
                change_pct = ((price - position['avg_price']) / position['avg_price']) * 100
                
                # Alert on significant moves
                if abs(change_pct) > 5:
                    logger.warning(f"Significant move in {symbol}: {change_pct:.2f}%")
                    
    async def _handle_news(self, data: Dict[str, Any]):
        """Handle news events"""
        symbol = data['symbol']
        headline = data['headline']
        
        logger.info(f"News for {symbol}: {headline}")
        
        # Get AI sentiment analysis
        sentiment = await self.ai_assistant.analyze_sentiment(headline)
        
        if sentiment['score'] < -0.5:
            logger.warning(f"Negative news sentiment for {symbol}: {sentiment['score']}")
            # Could trigger immediate analysis or position adjustment


# Example trading strategies

class MomentumStrategy(TradingStrategy):
    """Momentum-based trading strategy"""
    
    def __init__(self):
        super().__init__("Momentum")
        
    async def analyze(self, symbol: str, data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze momentum indicators"""
        rsi = data['indicators']['rsi']['values'][-1]['value']
        macd = data['indicators']['macd']['values'][-1]
        price = data['quote']['price']
        
        # Simple momentum rules
        if rsi < 30 and macd['histogram'] > 0:
            return TradingSignal(
                symbol=symbol,
                signal=SignalType.BUY,
                confidence=0.7,
                price=price,
                reason="Oversold with positive MACD momentum",
                indicators={'rsi': rsi, 'macd': macd},
                timestamp=datetime.utcnow()
            )
        elif rsi > 70 and macd['histogram'] < 0:
            return TradingSignal(
                symbol=symbol,
                signal=SignalType.SELL,
                confidence=0.7,
                price=price,
                reason="Overbought with negative MACD momentum",
                indicators={'rsi': rsi, 'macd': macd},
                timestamp=datetime.utcnow()
            )
        
        return None


class AIStrategy(TradingStrategy):
    """Pure AI-based trading strategy"""
    
    def __init__(self):
        super().__init__("AI-Powered")
        
    async def analyze(self, symbol: str, data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Use AI analysis for trading decisions"""
        ai_analysis = data['ai_analysis']
        price = data['quote']['price']
        
        # Parse AI recommendation
        if 'recommendation' in ai_analysis:
            rec = ai_analysis['recommendation'].upper()
            confidence = ai_analysis.get('confidence', 0.5)
            
            if 'BUY' in rec and confidence > 0.6:
                return TradingSignal(
                    symbol=symbol,
                    signal=SignalType.BUY,
                    confidence=confidence,
                    price=price,
                    reason=ai_analysis.get('reasoning', 'AI recommendation'),
                    indicators=data['indicators'],
                    timestamp=datetime.utcnow()
                )
            elif 'SELL' in rec and confidence > 0.6:
                return TradingSignal(
                    symbol=symbol,
                    signal=SignalType.SELL,
                    confidence=confidence,
                    price=price,
                    reason=ai_analysis.get('reasoning', 'AI recommendation'),
                    indicators=data['indicators'],
                    timestamp=datetime.utcnow()
                )
        
        return None


# Main execution
async def main():
    """Main function to run the trading bot"""
    # Configuration
    config = {
        'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA'],
        'interval': 300,  # 5 minutes
        'risk_management': {
            'max_position_size': 10000,  # $10k per position
            'stop_loss_pct': 5,  # 5% stop loss
            'take_profit_pct': 10  # 10% take profit
        }
    }
    
    # Create bot
    bot = AITradingBot(api_key='your-api-key', config=config)
    
    # Add strategies
    bot.add_strategy(MomentumStrategy())
    bot.add_strategy(AIStrategy())
    
    try:
        # Start bot
        await bot.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())


