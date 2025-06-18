# api/config.py
import os
from datetime import timedelta
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    TESTING = os.environ.get('TESTING', 'False').lower() == 'true'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://user:pass@localhost:5432/financial_platform'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # TimescaleDB
    TIMESCALE_ENABLED = os.environ.get('TIMESCALE_ENABLED', 'True').lower() == 'true'
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Rate Limiting
    RATE_LIMITS = {
        'basic': {'requests': 100, 'period': 60},      # 100 req/min
        'premium': {'requests': 1000, 'period': 60},   # 1000 req/min
        'enterprise': {'requests': 10000, 'period': 60} # 10000 req/min
    }
    
    # Cache Configuration
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_STRATEGIES = {
        'quotes': {'timeout': 30},      # 30 seconds for real-time quotes
        'historical': {'timeout': 3600}, # 1 hour for historical data
        'news': {'timeout': 300},       # 5 minutes for news
        'technical': {'timeout': 60}    # 1 minute for technical indicators
    }
    
    # Data Sources
    DATA_SOURCES = {
        'yfinance': {'enabled': True, 'priority': 1},
        'robin_stocks': {'enabled': True, 'priority': 2},
        'schwab': {'enabled': False, 'priority': 3},
        'sofi': {'enabled': False, 'priority': 4},
        'ibkr': {'enabled': False, 'priority': 5}
    }
    
    # AI Models
    AI_MODELS = {
        'claude': {
            'api_key': os.environ.get('CLAUDE_API_KEY'),
            'model': 'claude-3-opus-20240229',
            'max_tokens': 4096
        },
        'chatgpt': {
            'api_key': os.environ.get('OPENAI_API_KEY'),
            'model': 'gpt-4-turbo-preview',
            'max_tokens': 4096
        },
        'gemini': {
            'api_key': os.environ.get('GEMINI_API_KEY'),
            'model': 'gemini-pro',
            'max_tokens': 4096
        },
        'grok': {
            'api_key': os.environ.get('GROK_API_KEY'),
            'model': 'grok-1',
            'max_tokens': 4096
        }
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # WebSocket Configuration
    WEBSOCKET_PORT = int(os.environ.get('WEBSOCKET_PORT', 8765))
    WEBSOCKET_PING_INTERVAL = 30
    WEBSOCKET_PING_TIMEOUT = 10
    
    # Monitoring
    PROMETHEUS_ENABLED = os.environ.get('PROMETHEUS_ENABLED', 'True').lower() == 'true'
    PROMETHEUS_PORT = int(os.environ.get('PROMETHEUS_PORT', 9090))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith('_') and not callable(getattr(cls, key))
        }


