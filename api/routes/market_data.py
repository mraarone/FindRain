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