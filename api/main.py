# api/main.py
import asyncio
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_flask_exporter import PrometheusMetrics
import redis
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .database.models import db, migrate
from .middleware.auth import auth_bp
from .middleware.security import SecurityMiddleware
from .routes import (
    market_data_bp,
    technical_bp,
    portfolio_bp,
    news_bp,
    crypto_bp,
    options_bp
)
from .utils.cache import CacheManager
from .data.streaming import WebSocketServer

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Security middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    SecurityMiddleware(app)
    
    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "https://yourdomain.com"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # JWT
    jwt = JWTManager(app)
    
    # Redis and Cache
    redis_client = redis.from_url(app.config['REDIS_URL'])
    app.redis = redis_client
    app.cache = CacheManager(redis_client)
    
    # Rate Limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config['REDIS_URL'],
        default_limits=["1000 per hour"]
    )
    app.limiter = limiter
    
    # Prometheus Metrics
    if app.config['PROMETHEUS_ENABLED']:
        metrics = PrometheusMetrics(app)
        metrics.info('financial_platform', 'Financial Data Platform', version='1.0.0')
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(market_data_bp, url_prefix='/api/market')
    app.register_blueprint(technical_bp, url_prefix='/api/technical')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(news_bp, url_prefix='/api/news')
    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')
    app.register_blueprint(options_bp, url_prefix='/api/options')
    
    # Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': str(error)}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': str(error)}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': str(error)}), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests',
            'retry_after': error.description
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    # Health Check
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        try:
            # Check database
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = 'unhealthy'
        
        try:
            # Check Redis
            app.redis.ping()
            redis_status = 'healthy'
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_status = 'unhealthy'
        
        health_status = {
            'status': 'healthy' if db_status == 'healthy' and redis_status == 'healthy' else 'unhealthy',
            'database': db_status,
            'redis': redis_status,
            'version': '1.0.0'
        }
        
        return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 503
    
    # API Info
    @app.route('/api')
    def api_info():
        """API information endpoint"""
        return jsonify({
            'name': 'Financial Data Platform API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'market_data': '/api/market',
                'technical': '/api/technical',
                'portfolio': '/api/portfolio',
                'news': '/api/news',
                'crypto': '/api/crypto',
                'options': '/api/options'
            },
            'documentation': '/api/docs',
            'health': '/health'
        })
    
    return app


