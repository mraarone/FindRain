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