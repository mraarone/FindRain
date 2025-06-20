# api/utils/decorators.py
from functools import wraps
from flask import request, jsonify, g
import logging
from .validators import validate_symbol, validate_date, validate_number

logger = logging.getLogger(__name__)

def validate_request(f):
    """
    Decorator to validate incoming request data based on route expectations.
    This is a generic validator; more specific validation should be done
    within route functions or using libraries like Flask-marshmallow.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Example validation: Check 'symbol' in args or JSON body
        if 'symbol' in kwargs:
            try:
                kwargs['symbol'] = validate_symbol(kwargs['symbol'])
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        if request.is_json:
            json_data = request.get_json(silent=True)
            if json_data and 'symbols' in json_data and isinstance(json_data['symbols'], list):
                validated_symbols = []
                for s in json_data['symbols']:
                    try:
                        validated_symbols.append(validate_symbol(s))
                    except ValueError as e:
                        return jsonify({'error': f'Invalid symbol in list: {str(e)}'}), 400
                request.json = {**json_data, 'symbols': validated_symbols} # Update request.json for downstream use

        # Basic date validation for query parameters
        for param in ['start_date', 'end_date', 'purchase_date']:
            if request.args.get(param):
                try:
                    request.args = request.args.copy()
                    request.args[param] = validate_date(request.args[param]).isoformat()
                except ValueError as e:
                    return jsonify({'error': f'Invalid date format for {param}: {str(e)}'}), 400
            elif request.is_json and request.json and param in request.json:
                try:
                    request.json[param] = validate_date(request.json[param]).isoformat()
                except ValueError as e:
                    return jsonify({'error': f'Invalid date format for {param}: {str(e)}'}), 400

        # Basic number validation for query or JSON parameters
        for param in ['limit', 'period', 'quantity', 'purchase_price', 'commission', 'hours_back', 'days_back', 'min_value', 'max_value']:
            if request.args.get(param):
                try:
                    request.args = request.args.copy()
                    request.args[param] = validate_number(request.args[param])
                except ValueError as e:
                    return jsonify({'error': f'Invalid number format for {param}: {str(e)}'}), 400
            elif request.is_json and request.json and param in request.json:
                try:
                    request.json[param] = validate_number(request.json[param])
                except ValueError as e:
                    return jsonify({'error': f'Invalid number format for {param}: {str(e)}'}), 400

        return f(*args, **kwargs)
    return decorated_function
""")

# Update api/utils/validators.py
print("""# api/utils/validators.py
from datetime import datetime, timedelta
from typing import Tuple
import re

def validate_symbol(symbol: str) -> str:
    """Validate and normalize stock symbol"""
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string")
    
    symbol = symbol.upper().strip()
    
    # Basic symbol validation
    if not re.match(r'^[A-Z0-9\\-\\.]*$', symbol): # Adjusted regex to allow empty string and only specified chars
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    return symbol


def validate_date(date_str: str) -> datetime:
    """Validate and parse date string"""
    if isinstance(date_str, datetime):
        return date_str
    
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%d-%m-%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Invalid date format: {date_str}")


def validate_date_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    """Validate date range"""
    start = validate_date(start_date)
    end = validate_date(end_date)
    
    if start > end:
        raise ValueError("Start date must be before end date")
    
    # Limit range to prevent excessive data requests
    max_days = 365 * 5  # 5 years
    if (end - start).days > max_days:
        raise ValueError(f"Date range cannot exceed {max_days} days.")
    
    return start, end

def validate_number(value: Any, min_val: Optional[float] = None, 
                       max_val: Optional[float] = None) -> float:
    """Validate numeric value"""
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Value must be numeric, got {type(value)}")
    
    if min_val is not None and num < min_val:
        raise ValueError(f"Value {num} is below minimum {min_val}")
    
    if max_val is not None and num > max_val:
        raise ValueError(f"Value {num} is above maximum {max_val}")
    
    return num
""")

# Clean and update api/routes/crypto.py
print("""# api/routes/crypto.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from datetime import datetime
import logging

from ..utils.validators import validate_symbol
from ..utils.decorators import rate_limit_by_tier, validate_request
# from ..data.aggregator import DataAggregator # circular import, will be accessed via current_app

logger = logging.getLogger(__name__)

crypto_bp = Blueprint('crypto', __name__)

@crypto_bp.route('/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@validate_request
async def get_crypto_quote(symbol: str):
    """Get cryptocurrency quote"""
    try:
        # Crypto symbols often don't include currency pair
        if '-' not in symbol and not symbol.endswith('USD'):
            symbol = f"{symbol}-USD"
        
        # symbol is already validated by @validate_request
        
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


@crypto_bp.route('/trending', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@validate_request
async def get_trending_crypto():
    """Get trending cryptocurrencies"""
    try:
        limit = int(request.args.get('limit', 10))
        # limit is already validated by @validate_request

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

""")

# Clean and update api/routes/options.py
print("""# api/routes/options.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
import logging

from ..utils.validators import validate_symbol # Removed validate_date, validate_number as they are in decorators
from ..utils.decorators import rate_limit_by_tier, validate_request
# from ..data.aggregator import DataAggregator # circular import, will be accessed via current_app

logger = logging.getLogger(__name__)

options_bp = Blueprint('options', __name__)

@options_bp.route('/<symbol>/chain', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@validate_request
async def get_options_chain(symbol: str):
    """Get options chain for a symbol"""
    try:
        # symbol is already validated by @validate_request
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


@options_bp.route('/<symbol>/expirations', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@validate_request
async def get_options_expirations(symbol: str):
    """Get available expiration dates for options"""
    try:
        # symbol is already validated by @validate_request
        
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
                'days_to_expiry': max(0, days_to_expiry) # ensure non-negative
            })
        
        return jsonify({
            'symbol': symbol,
            'expirations': expiration_data
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting expirations: {e}")
        return jsonify({'error': 'Internal server error'}), 500

""")

# Update api/routes/market_data.py to properly use validate_request
print("""# api/routes/market_data.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging

from ..utils.validators import validate_symbol, validate_date_range # Removed validate_number as it's in decorators
from ..utils.decorators import rate_limit_by_tier, validate_request
from ..data.aggregator import DataAggregator

logger = logging.getLogger(__name__)

market_data_bp = Blueprint('market_data', __name__)

@market_data_bp.route('/quote/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@validate_request # symbol is now validated by this decorator
async def get_quote(symbol: str):
    """Get real-time quote for a symbol"""
    try:
        # symbol is already validated by @validate_request
        
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
@validate_request # symbols are now validated by this decorator
async def get_batch_quotes():
    """Get quotes for multiple symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', []) # Already validated by @validate_request if present

        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
        
        if len(symbols) > 100:
            return jsonify({'error': 'Maximum 100 symbols allowed'}), 400
        
        # symbols are already validated to be strings by @validate_request

        # Get aggregator
        aggregator: DataAggregator = current_app.aggregator
        
        # Get quotes in parallel
        quotes = {}
        # Changed to a single loop, as symbols are already validated
        for symbol in symbols:
            quote = await aggregator.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        
        return jsonify({
            'quotes': quotes,
            'requested': len(symbols), # Use len(symbols) directly
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
@validate_request # symbol, start_date, end_date, interval are now validated by this decorator
async def get_historical(symbol: str):
    """Get historical price data"""
    try:
        # symbol is already validated by @validate_request
        
        # Get parameters - now parsed and validated by decorator
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        interval = request.args.get('interval', '1d') # Defaults handled by validator or route

        # Validate dates using the existing validator (which is now called in @validate_request)
        start, end = validate_date_range(start_date_str, end_date_str)
        
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
@validate_request
async def search_symbols():
    """Search for symbols"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10)) # Already validated by @validate_request
        
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

""")

# Update api/routes/news.py to properly use validate_request and fix helper function placement
print("""# api/routes/news.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
import logging

from ..database.models import db, NewsArticle
from ..utils.validators import validate_symbol # Added validate_symbol
from ..utils.decorators import rate_limit_by_tier, validate_request

logger = logging.getLogger(__name__)

news_bp = Blueprint('news', __name__)

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

@news_bp.route('', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@validate_request # All params are now validated by this decorator
async def get_news():
    """Get news articles"""
    try:
        # Get parameters - now handled by @validate_request
        query = request.args.get('q', '')
        symbols = request.args.getlist('symbols')
        limit = int(request.args.get('limit', 20))
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


@news_bp.route('/sentiment/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
@validate_request # symbol, days_back validated here
async def get_sentiment_analysis(symbol: str):
    """Get sentiment analysis for a symbol"""
    try:
        # symbol is already validated by @validate_request
        days_back = int(request.args.get('days', 7)) # Already validated by @validate_request
        
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
                'positive': (positive / len(sentiments) * 100) if sentiments else 0,
                'neutral': (neutral / len(sentiments) * 100) if sentiments else 0,
                'negative': (negative / len(sentiments) * 100) if sentiments else 0
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

""")

# Update api/routes/portfolio.py to properly use validate_request
print("""# api/routes/portfolio.py
from flask import Blueprint, request, jsonify, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
import logging

from ..database.models import db, Portfolio, Holding
from ..utils.validators import validate_symbol, validate_date # Imported these directly as they're used outside decorators too
from ..utils.decorators import rate_limit_by_tier, validate_request
# from ..data.aggregator import DataAggregator # circular import, will be accessed via current_app

logger = logging.getLogger(__name__)

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
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


@portfolio_bp.route('', methods=['POST'])
@jwt_required()
@rate_limit_by_tier # Added decorator
@validate_request # Added decorator for potential future validation of name/description
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


@portfolio_bp.route('/<portfolio_id>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier # Added decorator
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
        
        aggregator = current_app.aggregator # Access DataAggregator via current_app
        
        for holding in portfolio.holdings:
            # Get current price
            quote = await aggregator.get_quote(holding.symbol)
            # Ensure price is a number, default to purchase price if not found
            current_price = quote['price'] if quote and 'price' in quote else float(holding.purchase_price)
            
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


@portfolio_bp.route('/<portfolio_id>/holdings', methods=['POST'])
@jwt_required()
@rate_limit_by_tier # Added decorator
@validate_request # symbol, quantity, purchase_price, purchase_date validated here
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
        
        # Validate input - now handled by @validate_request
        symbol = data.get('symbol')
        quantity = float(data.get('quantity', 0))
        purchase_price = float(data.get('purchase_price', 0))
        purchase_date = validate_date(data.get('purchase_date', datetime.utcnow()))
        
        if quantity <= 0 or purchase_price <= 0: # Redundant due to validate_request, but good as a sanity check
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

