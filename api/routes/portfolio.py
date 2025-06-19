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
