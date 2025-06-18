# api/models.py
"""
Models alias file for backward compatibility.
All models are defined in api/database/models.py
"""

# Import all models from the database module
from .database.models import (
    db,
    migrate,
    User,
    Portfolio,
    Holding,
    MarketData,
    NewsArticle,
    APIRequest,
    DataDownload
)

# Re-export for convenience
__all__ = [
    'db',
    'migrate',
    'User',
    'Portfolio',
    'Holding',
    'MarketData',
    'NewsArticle',
    'APIRequest',
    'DataDownload'
]