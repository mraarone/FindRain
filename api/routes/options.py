# api/routes/options.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import norm
import logging

from ..utils.validators import validate_symbol, validate_date, validate_number
from ..utils.decorators import rate_limit_by_tier, validate_request
from ..utils.cache import cache

logger = logging.getLogger(__name__)

options_bp = Blueprint('options', __name__)

@options_bp.route('/options/<symbol>/chain', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_options_chain(symbol: str):
    """Get options chain for a symbol"""
    try:
        symbol = validate_symbol(symbol)
        expiration = request.args.get('expiration')
        strike_range = request.args.get('strike_range', 'near')
        option_type = request.args.get('type', 'both')
        
        aggregator = current_app.aggregator
        options_data = await aggregator.get_options_chain(symbol)
        
        if not options_data:
            return jsonify({'error': f'No options data found for {symbol}'}), 404
        
        # Filter by expiration if provided
        if expiration and expiration != 'all':
            if expiration in options_data.get('chains', {}):
                filtered_chain = {
                    'symbol': symbol,
                    'spot_price': options_data.get('spot_price'),
                    'expiration': expiration,
                    'chain': options_data['chains'][expiration]
                }
                return jsonify(filtered_chain), 200
            else:
                return jsonify({'error': f'No options for expiration {expiration}'}), 404
        
        # Filter by strike range
        if strike_range != 'all' and 'spot_price' in options_data:
            spot = options_data['spot_price']
            filtered_chains = {}
            
            for exp, chain in options_data.get('chains', {}).items():
                filtered_chain = {'calls': [], 'puts': []}
                
                for option_type_key in ['calls', 'puts']:
                    if option_type != 'both' and option_type != option_type_key[:-1]:
                        continue
                        
                    for opt in chain.get(option_type_key, []):
                        strike = opt['strike']
                        
                        if strike_range == 'near' and abs(strike - spot) / spot > 0.1:
                            continue
                        elif strike_range == 'itm':
                            if option_type_key == 'calls' and strike >= spot:
                                continue
                            elif option_type_key == 'puts' and strike <= spot:
                                continue
                        elif strike_range == 'otm':
                            if option_type_key == 'calls' and strike <= spot:
                                continue
                            elif option_type_key == 'puts' and strike >= spot:
                                continue
                        
                        filtered_chain[option_type_key].append(opt)
                
                if filtered_chain['calls'] or filtered_chain['puts']:
                    filtered_chains[exp] = filtered_chain
            
            options_data['chains'] = filtered_chains
        
        return jsonify(options_data), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting options chain: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@options_bp.route('/options/<symbol>/expirations', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_options_expirations(symbol: str):
    """Get available expiration dates for options"""
    try:
        symbol = validate_symbol(symbol)
        
        aggregator = current_app.aggregator
        options_data = await aggregator.get_options_chain(symbol)
        
        if not options_data:
            return jsonify({'error': f'No options data found for {symbol}'}), 404
        
        expirations = options_data.get('expirations', [])
        
        # Add metadata about each expiration
        expiration_data = []
        for exp in expirations:
            exp_date = datetime.strptime(exp, '%Y-%m-%d')
            days_to_expiry = (exp_date - datetime.utcnow()).days
            
            expiration_data.append({
                'date': exp,
                # api/routes/market_data.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging

from ..utils.validators import validate_symbol, validate_date_range
from ..utils.decorators import rate_limit_by_tier, validate_request
from ..data.aggregator import DataAggregator

logger = logging.getLogger(__name__)

market_data_bp = Blueprint('market_data', __name__)

@market_data_bp.route('/quote/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@validate_request
async def get_quote(symbol: str):
    """Get real-time quote for a symbol"""
    try:
        # Validate symbol
        symbol = validate_symbol(symbol)
        
        # Get aggregator
        aggregator: DataAggregator = current_app.aggregator
        
        # Get quote
        quote = await aggregator.get_quote(symbol)
        
        if not quote:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
        return jsonify(quote), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@market_data_bp.route('/quotes', methods=['POST'])
@jwt_required()
@rate_limit_by_tier
@validate_request
async def get_batch_quotes():
    """Get quotes for multiple symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
        
        if len(symbols) > 100:
            return jsonify({'error': 'Maximum 100 symbols allowed'}), 400
        
        # Validate all symbols
        validated_symbols = [validate_symbol(s) for s in symbols]
        
        # Get aggregator
        aggregator: DataAggregator = current_app.aggregator
        
        # Get quotes in parallel
        quotes = {}
        for symbol in validated_symbols:
            quote = await aggregator.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        
        return jsonify({
            'quotes': quotes,
            'requested': len(validated_symbols),
            'found': len(quotes),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting batch quotes: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@market_data_bp.route('/historical/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@validate_request
async def get_historical(symbol: str):
    """Get historical price data"""
    try:
        # Validate symbol
        symbol = validate_symbol(symbol)
        
        # Get parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        interval = request.args.get('interval', '1d')
        
        # Validate dates
        start, end = validate_date_range(start_date, end_date)
        
        # Validate interval
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '1d', '1w', '1M']
        if interval not in valid_intervals:
            return jsonify({'error': f'Invalid interval. Must be one of {valid_intervals}'}), 400
        
        # Get aggregator
        aggregator: DataAggregator = current_app.aggregator
        
        # Get historical data
        data = await aggregator.get_historical(symbol, start, end, interval)
        
        if not data:
            return jsonify({'error': f'No historical data found for {symbol}'}), 404
        
        return jsonify({
            'symbol': symbol,
            'interval': interval,
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'data': data,
            'count': len(data)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@market_data_bp.route('/search', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def search_symbols():
    """Search for symbols"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        # TODO: Implement symbol search
        # For now, return mock results
        results = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'type': 'stock'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'type': 'stock'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'type': 'stock'}
        ]
        
        # Filter by query
        filtered = [r for r in results if query.upper() in r['symbol'] or query.lower() in r['name'].lower()]
        
        return jsonify({
            'query': query,
            'results': filtered[:limit],
            'count': len(filtered)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# api/routes/technical.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
import numpy as np
import pandas as pd

technical_bp = Blueprint('technical', __name__)

@technical_bp.route('/indicators/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_technical_indicators(symbol: str):
    """Get technical indicators for a symbol"""
    try:
        symbol = validate_symbol(symbol)
        indicators = request.args.getlist('indicators')
        period = int(request.args.get('period', 14))
        
        if not indicators:
            indicators = ['sma', 'ema', 'rsi', 'macd']
        
        # Get historical data
        aggregator: DataAggregator = current_app.aggregator
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period * 2)  # Get extra data for calculations
        
        data = await aggregator.get_historical(symbol, start_date, end_date, '1d')
        
        if not data:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Calculate indicators
        results = {'symbol': symbol, 'indicators': {}}
        
        if 'sma' in indicators:
            results['indicators']['sma'] = calculate_sma(df, period)
        
        if 'ema' in indicators:
            results['indicators']['ema'] = calculate_ema(df, period)
        
        if 'rsi' in indicators:
            results['indicators']['rsi'] = calculate_rsi(df, period)
        
        if 'macd' in indicators:
            results['indicators']['macd'] = calculate_macd(df)
        
        if 'bollinger' in indicators:
            results['indicators']['bollinger'] = calculate_bollinger_bands(df, period)
        
        if 'stochastic' in indicators:
            results['indicators']['stochastic'] = calculate_stochastic(df, period)
        
        return jsonify(results), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def calculate_sma(df: pd.DataFrame, period: int) -> dict:
    """Calculate Simple Moving Average"""
    sma = df['close'].rolling(window=period).mean()
    
    return {
        'period': period,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'value': float(val) if not pd.isna(val) else None
            }
            for ts, val in sma.items()
        ]
    }


def calculate_ema(df: pd.DataFrame, period: int) -> dict:
    """Calculate Exponential Moving Average"""
    ema = df['close'].ewm(span=period, adjust=False).mean()
    
    return {
        'period': period,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'value': float(val) if not pd.isna(val) else None
            }
            for ts, val in ema.items()
        ]
    }


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> dict:
    """Calculate Relative Strength Index"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return {
        'period': period,
        'overbought': 70,
        'oversold': 30,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'value': float(val) if not pd.isna(val) else None
            }
            for ts, val in rsi.items()
        ]
    }


def calculate_macd(df: pd.DataFrame) -> dict:
    """Calculate MACD"""
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    
    return {
        'values': [
            {
                'timestamp': ts.isoformat(),
                'macd': float(macd.loc[ts]) if not pd.isna(macd.loc[ts]) else None,
                'signal': float(signal.loc[ts]) if not pd.isna(signal.loc[ts]) else None,
                'histogram': float(histogram.loc[ts]) if not pd.isna(histogram.loc[ts]) else None
            }
            for ts in macd.index
        ]
    }


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> dict:
    """Calculate Bollinger Bands"""
    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return {
        'period': period,
        'std_dev': std_dev,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'upper': float(upper.loc[ts]) if not pd.isna(upper.loc[ts]) else None,
                'middle': float(sma.loc[ts]) if not pd.isna(sma.loc[ts]) else None,
                'lower': float(lower.loc[ts]) if not pd.isna(lower.loc[ts]) else None
            }
            for ts in sma.index
        ]
    }


def calculate_stochastic(df: pd.DataFrame, period: int = 14) -> dict:
    """Calculate Stochastic Oscillator"""
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    
    k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
    d_percent = k_percent.rolling(window=3).mean()
    
    return {
        'period': period,
        'overbought': 80,
        'oversold': 20,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'k': float(k_percent.loc[ts]) if not pd.isna(k_percent.loc[ts]) else None,
                'd': float(d_percent.loc[ts]) if not pd.isna(d_percent.loc[ts]) else None
            }
            for ts in k_percent.index
        ]
    }


# api/routes/portfolio.py
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from ..database.models import db, Portfolio, Holding

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/portfolios', methods=['GET'])
@jwt_required()
async def get_portfolios():
    """Get user's portfolios"""
    try:
        user_id = get_jwt_identity()
        
        portfolios = Portfolio.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'portfolios': [
                {
                    'id': str(p.id),
                    'name': p.name,
                    'description': p.description,
                    'created_at': p.created_at.isoformat(),
                    'holdings_count': p.holdings.count()
                }
                for p in portfolios
            ],
            'count': len(portfolios)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting portfolios: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@portfolio_bp.route('/portfolios', methods=['POST'])
@jwt_required()
async def create_portfolio():
    """Create new portfolio"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Portfolio name required'}), 400
        
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=data.get('description', '')
        )
        
        db.session.add(portfolio)
        db.session.commit()
        
        return jsonify({
            'id': str(portfolio.id),
            'name': portfolio.name,
            'description': portfolio.description,
            'created_at': portfolio.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating portfolio: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@portfolio_bp.route('/portfolios/<portfolio_id>', methods=['GET'])
@jwt_required()
async def get_portfolio_details(portfolio_id: str):
    """Get detailed portfolio information"""
    try:
        user_id = get_jwt_identity()
        
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=user_id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Get holdings with current values
        holdings = []
        total_value = 0
        total_cost = 0
        
        aggregator = current_app.aggregator
        
        for holding in portfolio.holdings:
            # Get current price
            quote = await aggregator.get_quote(holding.symbol)
            current_price = quote['price'] if quote else float(holding.purchase_price)
            
            current_value = float(holding.quantity) * current_price
            cost_basis = float(holding.quantity) * float(holding.purchase_price)
            
            holdings.append({
                'id': str(holding.id),
                'symbol': holding.symbol,
                'quantity': float(holding.quantity),
                'purchase_price': float(holding.purchase_price),
                'purchase_date': holding.purchase_date.isoformat(),
                'current_price': current_price,
                'current_value': current_value,
                'cost_basis': cost_basis,
                'gain_loss': current_value - cost_basis,
                'gain_loss_percent': ((current_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
            })
            
            total_value += current_value
            total_cost += cost_basis
        
        return jsonify({
            'id': str(portfolio.id),
            'name': portfolio.name,
            'description': portfolio.description,
            'created_at': portfolio.created_at.isoformat(),
            'holdings': holdings,
            'summary': {
                'total_value': total_value,
                'total_cost': total_cost,
                'total_gain_loss': total_value - total_cost,
                'total_gain_loss_percent': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
                'holdings_count': len(holdings)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting portfolio details: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@portfolio_bp.route('/portfolios/<portfolio_id>/holdings', methods=['POST'])
@jwt_required()
async def add_holding(portfolio_id: str):
    """Add holding to portfolio"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Verify portfolio ownership
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=user_id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Validate input
        symbol = validate_symbol(data.get('symbol'))
        quantity = float(data.get('quantity', 0))
        purchase_price = float(data.get('purchase_price', 0))
        purchase_date = validate_date(data.get('purchase_date', datetime.utcnow()))
        
        if quantity <= 0 or purchase_price <= 0:
            return jsonify({'error': 'Invalid quantity or price'}), 400
        
        # Create holding
        holding = Holding(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            purchase_price=purchase_price,
            purchase_date=purchase_date
        )
        
        db.session.add(holding)
        db.session.commit()
        
        return jsonify({
            'id': str(holding.id),
            'symbol': holding.symbol,
            'quantity': float(holding.quantity),
            'purchase_price': float(holding.purchase_price),
            'purchase_date': holding.purchase_date.isoformat()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding holding: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# api/routes/news.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta

from ..database.models import db, NewsArticle

news_bp = Blueprint('news', __name__)

@news_bp.route('/news', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_news():
    """Get news articles"""
    try:
        # Get parameters
        query = request.args.get('q', '')
        symbols = request.args.getlist('symbols')
        limit = min(int(request.args.get('limit', 20)), 100)
        hours_back = int(request.args.get('hours_back', 24))
        
        # Build query
        since = datetime.utcnow() - timedelta(hours=hours_back)
        
        db_query = NewsArticle.query.filter(
            NewsArticle.published_at >= since
        )
        
        if symbols:
            # Filter by symbols using JSONB contains
            db_query = db_query.filter(
                NewsArticle.symbols.contains(symbols)
            )
        
        if query:
            # Search in title and content
            search_filter = f"%{query}%"
            db_query = db_query.filter(
                db.or_(
                    NewsArticle.title.ilike(search_filter),
                    NewsArticle.content.ilike(search_filter)
                )
            )
        
        # Order by published date
        articles = db_query.order_by(
            NewsArticle.published_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'articles': [
                {
                    'id': str(article.id),
                    'title': article.title,
                    'summary': article.summary,
                    'url': article.url,
                    'source': article.source,
                    'author': article.author,
                    'published_at': article.published_at.isoformat(),
                    'retrieved_at': article.retrieved_at.isoformat(),
                    'symbols': article.symbols,
                    'sentiment': article.sentiment,
                    'categories': article.categories
                }
                for article in articles
            ],
            'count': len(articles),
            'query': query,
            'symbols': symbols,
            'hours_back': hours_back
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@news_bp.route('/news/sentiment/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_sentiment_analysis(symbol: str):
    """Get sentiment analysis for a symbol"""
    try:
        symbol = validate_symbol(symbol)
        days_back = int(request.args.get('days', 7))
        
        since = datetime.utcnow() - timedelta(days=days_back)
        
        # Get articles for symbol
        articles = NewsArticle.query.filter(
            NewsArticle.published_at >= since,
            NewsArticle.symbols.contains([symbol])
        ).all()
        
        if not articles:
            return jsonify({
                'symbol': symbol,
                'sentiment': 0,
                'articles_analyzed': 0,
                'period_days': days_back
            }), 200
        
        # Calculate sentiment metrics
        sentiments = [a.sentiment for a in articles if a.sentiment is not None]
        
        if not sentiments:
            avg_sentiment = 0
        else:
            avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Sentiment distribution
        positive = len([s for s in sentiments if s > 0.2])
        negative = len([s for s in sentiments if s < -0.2])
        neutral = len(sentiments) - positive - negative
        
        return jsonify({
            'symbol': symbol,
            'overall_sentiment': avg_sentiment,
            'sentiment_score': _calculate_sentiment_score(avg_sentiment),
            'articles_analyzed': len(articles),
            'sentiment_distribution': {
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'positive_percent': (positive / len(sentiments) * 100) if sentiments else 0,
                'neutral_percent': (neutral / len(sentiments) * 100) if sentiments else 0,
                'negative_percent': (negative / len(sentiments) * 100) if sentiments else 0
            },
            'recent_headlines': [
                {
                    'title': a.title,
                    'sentiment': a.sentiment,
                    'published_at': a.published_at.isoformat()
                }
                for a in sorted(articles, key=lambda x: x.published_at, reverse=True)[:5]
            ],
            'period_days': days_back
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def _calculate_sentiment_score(sentiment: float) -> str:
    """Convert sentiment value to score label"""
    if sentiment >= 0.5:
        return 'Very Positive'
    elif sentiment >= 0.2:
        return 'Positive'
    elif sentiment >= -0.2:
        return 'Neutral'
    elif sentiment >= -0.5:
        return 'Negative'
    else:
        return 'Very Negative'


# api/routes/crypto.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

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
        
        symbol = validate_symbol(symbol)
        
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


@crypto_bp.route('/crypto/trending', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_trending_crypto():
    """Get trending cryptocurrencies"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Mock trending data - replace with actual implementation
        trending = [
            {'symbol': 'BTC-USD', 'name': 'Bitcoin', 'change_24h': 5.2},
            {'symbol': 'ETH-USD', 'name': 'Ethereum', 'change_24h': 3.8},
            {'symbol': 'BNB-USD', 'name': 'Binance Coin', 'change_24h': 2.1}
        ]
        
        return jsonify({
            'trending': trending[:limit],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trending crypto: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# api/routes/options.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

options_bp = Blueprint('options', __name__)

@options_bp.route('/options/<symbol>/chain', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_options_chain(symbol: str):
    """Get options chain for a symbol"""
    try:
        symbol = validate_symbol(symbol)
        expiration = request.args.get('expiration')
        
        aggregator = current_app.aggregator
        options_data = await aggregator.get_options_chain(symbol)
        
        if not options_data:
            return jsonify({'error': f'No options data found for {symbol}'}), 404
        
        # Filter by expiration if provided
        if expiration and expiration in options_data.get('chains', {}):
            filtered_chain = {
                'symbol': symbol,
                'expiration': expiration,
                'chain': options_data['chains'][expiration]
            }
            return jsonify(filtered_chain), 200
        
        return jsonify(options_data), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting options chain: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@options_bp.route('/options/<symbol>/expirations', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_options_expirations(symbol: str):
    """Get available expiration dates for options"""
    try:
        symbol = validate_symbol(symbol)
        
        aggregator = current_app.aggregator
        options_data = await aggregator.get_options_chain(symbol)
        
        if not options_data:
            return jsonify({'error': f'No options data found for {symbol}'}), 404
        
        return jsonify({
            'symbol': symbol,
            'expirations': options_data.get('expirations', [])
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting expirations: {e}")
        return jsonify({'error': 'Internal server error'}), 500

        # INTERRUPTED RUN AT 5:00PM, 6/18/2025, WAITING UNTIL 9PM TO CONTINUE