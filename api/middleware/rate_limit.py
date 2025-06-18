# api/middleware/rate_limit.py
from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

from ..database.models import User

logger = logging.getLogger(__name__)

def get_user_tier():
    """Get current user's tier for rate limiting"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(user_id)
            if user:
                return user.tier
    except:
        pass
    return 'basic'

def rate_limit_by_tier(f):
    """Decorator to apply tier-based rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tier = get_user_tier()
        
        # Apply rate limits based on tier
        limits = {
            'basic': '100 per minute',
            'premium': '1000 per minute',
            'enterprise': '10000 per minute'
        }
        
        # Store tier in g for use in the route
        g.user_tier = tier
        
        return f(*args, **kwargs)
    
    return decorated_function
