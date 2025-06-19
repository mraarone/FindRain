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
        
        return jsonify({
            'symbol': symbol,
            'expirations': options_data.get('expirations', [])
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting expirations: {e}")
        return jsonify({'error': 'Internal server error'}), 500

