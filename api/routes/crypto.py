# api/routes/crypto.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
import logging

from ..utils.validators import validate_crypto_symbol, validate_number, validate_date_range
from ..utils.decorators import rate_limit_by_tier, validate_request
from ..utils.cache import cache

logger = logging.getLogger(__name__)

crypto_bp = Blueprint('crypto', __name__)

@crypto_bp.route('/crypto/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_crypto_quote(symbol: str):
    """Get cryptocurrency quote"""
    try:
        # Crypto symbols often don't include currency pair
        if '-' not in symbol and not symbol.endswith('USD'):
            symbol = f"{symbol}-USD"
        
        symbol = validate_crypto_symbol(symbol)
        
        aggregator = current_app.aggregator
        crypto_data = await aggregator.get_crypto_data(symbol)
        
        if not crypto_data:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        return jsonify(crypto_data), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting crypto data: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@crypto_bp.route('/crypto/batch', methods=['POST'])
@jwt_required()
@rate_limit_by_tier
async def get_batch_crypto_quotes():
    """Get multiple cryptocurrency quotes"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
        
        if len(symbols) > 50:
            return jsonify({'error': 'Maximum 50 symbols allowed'}), 400
        
        # Validate and normalize symbols
        validated_symbols = []
        for symbol in symbols:
            if '-' not in symbol and not symbol.endswith('USD'):
                symbol = f"{symbol}-USD"
            validated_symbols.append(validate_crypto_symbol(symbol))
        
        aggregator = current_app.aggregator
        
        # Get quotes in parallel
        quotes = {}
        for symbol in validated_symbols:
            crypto_data = await aggregator.get_crypto_data(symbol)
            if crypto_data:
                quotes[symbol] = crypto_data
        
        return jsonify({
            'quotes': quotes,
            'requested': len(validated_symbols),
            'found': len(quotes),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting batch crypto quotes: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@crypto_bp.route('/crypto/trending', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@cache(prefix="crypto_trending", ttl=300)
async def get_trending_crypto():
    """Get trending cryptocurrencies"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        time_period = request.args.get('period', '24h')
        category = request.args.get('category', 'all')
        
        # Validate time period
        valid_periods = ['1h', '24h', '7d', '30d']
        if time_period not in valid_periods:
            return jsonify({'error': f'Invalid period. Must be one of {valid_periods}'}), 400
        
        # Get trending data from aggregator
        aggregator = current_app.aggregator
        
        # This would connect to a service that tracks trending cryptos
        trending_data = await aggregator.get_trending_crypto(
            limit=limit,
            period=time_period,
            category=category
        )
        
        if not trending_data:
            # Fallback to mock data
            trending_data = [
                {'symbol': 'BTC-USD', 'name': 'Bitcoin', 'change_24h': 5.2, 'volume_24h': 28000000000},
                {'symbol': 'ETH-USD', 'name': 'Ethereum', 'change_24h': 3.8, 'volume_24h': 15000000000},
                {'symbol': 'BNB-USD', 'name': 'Binance Coin', 'change_24h': 2.1, 'volume_24h': 1200000000}
            ]
        
        return jsonify({
            'trending': trending_data[:limit],
            'period': time_period,
            'category': category,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trending crypto: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@crypto_bp.route('/crypto/<symbol>/orderbook', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_crypto_orderbook(symbol: str):
    """Get cryptocurrency order book data"""
    try:
        symbol = validate_crypto_symbol(symbol)
        depth = min(int(request.args.get('depth', 20)), 100)
        exchange = request.args.get('exchange', 'aggregate')
        
        aggregator = current_app.aggregator
        
        # Get order book data
        orderbook = await aggregator.get_crypto_orderbook(
            symbol=symbol,
            depth=depth,
            exchange=exchange
        )
        
        if not orderbook:
            return jsonify({'error': f'No orderbook data for {symbol}'}), 404
        
        # Calculate spread and other metrics
        if orderbook.get('bids') and orderbook.get('asks'):
            best_bid = orderbook['bids'][0]['price']
            best_ask = orderbook['asks'][0]['price']
            spread = best_ask - best_bid
            spread_pct = (spread / best_ask) * 100
            
            orderbook['metrics'] = {
                'spread': spread,
                'spread_percentage': spread_pct,
                'mid_price': (best_bid + best_ask) / 2,
                'bid_depth': sum(bid['size'] for bid in orderbook['bids']),
                'ask_depth': sum(ask['size'] for ask in orderbook['asks'])
            }
        
        return jsonify(orderbook), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting orderbook: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@crypto_bp.route('/crypto/<symbol>/trades', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_crypto_trades(symbol: str):
    """Get recent cryptocurrency trades"""
    try:
        symbol = validate_crypto_symbol(symbol)
        limit = min(int(request.args.get('limit', 100)), 1000)
        
        aggregator = current_app.aggregator
        
        # Get recent trades
        trades = await aggregator.get_crypto_trades(symbol, limit)
        
        if not trades:
            return jsonify({'error': f'No trade data for {symbol}'}), 404
        
        # Calculate trade statistics
        if trades:
            total_volume = sum(t['size'] for t in trades)
            buy_volume = sum(t['size'] for t in trades if t.get('side') == 'buy')
            sell_volume = sum(t['size'] for t in trades if t.get('side') == 'sell')
            
            stats = {
                'total_trades': len(trades),
                'total_volume': total_volume,
                'buy_volume': buy_volume,
                'sell_volume': sell_volume,
                'buy_sell_ratio': buy_volume / sell_volume if sell_volume > 0 else float('inf'),
                'avg_trade_size': total_volume / len(trades) if trades else 0
            }
        else:
            stats = {}
        
        return jsonify({
            'symbol': symbol,
            'trades': trades,
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@crypto_bp.route('/crypto/defi/<protocol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@cache(prefix="defi_metrics", ttl=600)
async def get_defi_metrics(protocol: str):
    """Get DeFi protocol metrics"""
    try:
        protocol = protocol.lower().strip()
        chain = request.args.get('chain', 'all')
        
        aggregator = current_app.aggregator
        
        # Get DeFi metrics
        metrics = await aggregator.get_defi_metrics(protocol, chain)
        
        if not metrics:
            return jsonify({'error': f'No data for protocol {protocol}'}), 404
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Error getting DeFi metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@crypto_bp.route('/crypto/mining/<coin>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@cache(prefix="mining_stats", ttl=300)
async def get_mining_stats(coin: str):
    """Get cryptocurrency mining statistics"""
    try:
        coin = coin.upper().strip()
        
        # Only certain coins have mining
        minable_coins = ['BTC', 'ETH', 'LTC', 'BCH', 'ETC', 'ZEC', 'XMR', 'DASH']
        if coin not in minable_coins:
            return jsonify({'error': f'{coin} is not a minable cryptocurrency'}), 400
        
        aggregator = current_app.aggregator
        
        # Get mining statistics
        mining_stats = await aggregator.get_mining_stats(coin)
        
        if not mining_stats:
            # Mock data for demo
            mining_stats = {
                'coin': coin,
                'network_hashrate': 250000000000000000,  # Example for BTC
                'difficulty': 35000000000000,
                'block_time': 600,  # seconds
                'block_reward': 6.25 if coin == 'BTC' else 2.0,
                'blocks_24h': 144,
                'revenue_per_th': 0.08,  # USD per TH/s per day
                'electricity_cost': 0.05,  # USD per kWh
                'profitability': {
                    'per_th_daily': 0.08,
                    'break_even_efficiency': 30  # J/TH
                }
            }
        
        return jsonify(mining_stats), 200
        
    except Exception as e:
        logger.error(f"Error getting mining stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@crypto_bp.route('/crypto/exchange-rates', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@cache(prefix="exchange_rates", ttl=60)
async def get_exchange_rates():
    """Get cryptocurrency exchange rates across different pairs"""
    try:
        base = request.args.get('base', 'USD').upper()
        quotes = request.args.getlist('quote')
        
        if not quotes:
            quotes = ['BTC', 'ETH', 'EUR', 'GBP', 'JPY']
        
        aggregator = current_app.aggregator
        
        # Get exchange rates
        rates = {}
        for quote in quotes:
            if base == quote:
                rates[quote] = 1.0
                continue
                
            # Try crypto pairs first
            if base in ['BTC', 'ETH'] or quote in ['BTC', 'ETH']:
                pair = f"{base}-{quote}"
                data = await aggregator.get_crypto_data(pair)
                if data:
                    rates[quote] = data.get('price', 0)
            else:
                # For fiat pairs, would use forex data
                # Mock for now
                rates[quote] = 1.0
        
        return jsonify({
            'base': base,
            'rates': rates,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting exchange rates: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@crypto_bp.route('/crypto/<symbol>/technical', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_crypto_technical_analysis(symbol: str):
    """Get technical analysis for cryptocurrency"""
    try:
        symbol = validate_crypto_symbol(symbol)
        interval = request.args.get('interval', '4h')
        indicators = request.args.getlist('indicators')
        
        if not indicators:
            indicators = ['sma', 'ema', 'rsi', 'macd', 'bollinger']
        
        # Validate interval
        valid_intervals = ['15m', '30m', '1h', '4h', '1d', '1w']
        if interval not in valid_intervals:
            return jsonify({'error': f'Invalid interval. Must be one of {valid_intervals}'}), 400
        
        aggregator = current_app.aggregator
        
        # Get historical data for calculations
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)  # Get enough data for indicators
        
        historical = await aggregator.get_historical(
            symbol, start_date, end_date, interval
        )
        
        if not historical:
            return jsonify({'error': f'No historical data for {symbol}'}), 404
        
        # Calculate technical indicators
        # (In production, this would use the technical indicators service)
        technical_data = {
            'symbol': symbol,
            'interval': interval,
            'current_price': historical[-1]['close'] if historical else 0,
            'indicators': {},
            'signals': {}
        }
        
        # Add calculated indicators (simplified)
        if 'sma' in indicators:
            technical_data['indicators']['sma_20'] = calculate_sma(historical, 20)
            technical_data['indicators']['sma_50'] = calculate_sma(historical, 50)
        
        if 'rsi' in indicators:
            technical_data['indicators']['rsi'] = calculate_rsi(historical, 14)
        
        # Generate trading signals
        technical_data['signals'] = generate_crypto_signals(technical_data['indicators'])
        
        return jsonify(technical_data), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting crypto technical analysis: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@crypto_bp.route('/crypto/gas-tracker', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@cache(prefix="gas_tracker", ttl=30)
async def get_gas_tracker():
    """Get gas prices for Ethereum and other EVM chains"""
    try:
        chain = request.args.get('chain', 'ethereum').lower()
        
        valid_chains = ['ethereum', 'bsc', 'polygon', 'avalanche', 'arbitrum', 'optimism']
        if chain not in valid_chains:
            return jsonify({'error': f'Invalid chain. Must be one of {valid_chains}'}), 400
        
        aggregator = current_app.aggregator
        
        # Get gas prices
        gas_data = await aggregator.get_gas_prices(chain)
        
        if not gas_data:
            # Mock data for demo
            gas_data = {
                'chain': chain,
                'prices': {
                    'slow': {'gwei': 20, 'usd': 1.50, 'time': '10 min'},
                    'standard': {'gwei': 30, 'usd': 2.25, 'time': '3 min'},
                    'fast': {'gwei': 40, 'usd': 3.00, 'time': '30 sec'},
                    'instant': {'gwei': 60, 'usd': 4.50, 'time': '15 sec'}
                },
                'base_fee': 25,
                'priority_fee': 2,
                'eth_price': 2500,
                'last_block': 18500000
            }
        
        return jsonify(gas_data), 200
        
    except Exception as e:
        logger.error(f"Error getting gas prices: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Helper functions

def calculate_sma(data, period):
    """Calculate Simple Moving Average"""
    if len(data) < period:
        return None
    
    prices = [d['close'] for d in data[-period:]]
    return sum(prices) / period


def calculate_rsi(data, period=14):
    """Calculate RSI"""
    if len(data) < period + 1:
        return None
    
    prices = [d['close'] for d in data[-(period+1):]]
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def generate_crypto_signals(indicators):
    """Generate trading signals from indicators"""
    signals = {
        'overall': 'neutral',
        'strength': 0,
        'recommendations': []
    }
    
    buy_signals = 0
    sell_signals = 0
    
    # RSI signals
    if 'rsi' in indicators and indicators['rsi'] is not None:
        if indicators['rsi'] < 30:
            buy_signals += 1
            signals['recommendations'].append('RSI oversold - potential buy')
        elif indicators['rsi'] > 70:
            sell_signals += 1
            signals['recommendations'].append('RSI overbought - potential sell')
    
    # SMA signals
    if 'sma_20' in indicators and 'sma_50' in indicators:
        if indicators['sma_20'] and indicators['sma_50']:
            if indicators['sma_20'] > indicators['sma_50']:
                buy_signals += 1
                signals['recommendations'].append('Golden cross pattern')
            else:
                sell_signals += 1
                signals['recommendations'].append('Death cross pattern')
    
    # Determine overall signal
    if buy_signals > sell_signals:
        signals['overall'] = 'buy'
        signals['strength'] = buy_signals / (buy_signals + sell_signals)
    elif sell_signals > buy_signals:
        signals['overall'] = 'sell'
        signals['strength'] = sell_signals / (buy_signals + sell_signals)
    
    return signals
