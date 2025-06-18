# api/database/models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Index
import uuid

db = SQLAlchemy()
migrate = Migrate()

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tier = db.Column(db.String(20), default='basic')  # basic, premium, enterprise
    api_key = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    portfolios = db.relationship('Portfolio', backref='user', lazy='dynamic')
    api_requests = db.relationship('APIRequest', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Portfolio(db.Model):
    """Portfolio model"""
    __tablename__ = 'portfolios'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    holdings = db.relationship('Holding', backref='portfolio', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_portfolio_user', 'user_id'),
    )


class Holding(db.Model):
    """Portfolio holding model"""
    __tablename__ = 'holdings'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = db.Column(UUID(as_uuid=True), db.ForeignKey('portfolios.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Numeric(20, 8), nullable=False)
    purchase_price = db.Column(db.Numeric(20, 8), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_holding_portfolio', 'portfolio_id'),
        Index('idx_holding_symbol', 'symbol'),
    )


class MarketData(db.Model):
    """Market data model (TimescaleDB hypertable)"""
    __tablename__ = 'market_data'
    
    time = db.Column(db.DateTime, primary_key=True)
    symbol = db.Column(db.String(20), primary_key=True)
    open = db.Column(db.Numeric(20, 8))
    high = db.Column(db.Numeric(20, 8))
    low = db.Column(db.Numeric(20, 8))
    close = db.Column(db.Numeric(20, 8))
    volume = db.Column(db.BigInteger)
    source = db.Column(db.String(50))
    
    __table_args__ = (
        Index('idx_market_data_symbol_time', 'symbol', 'time'),
    )


class NewsArticle(db.Model):
    """News article model"""
    __tablename__ = 'news_articles'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    url = db.Column(db.String(1000), unique=True, nullable=False)
    source = db.Column(db.String(100))
    author = db.Column(db.String(200))
    published_at = db.Column(db.DateTime, nullable=False)
    retrieved_at = db.Column(db.DateTime, default=datetime.utcnow)
    symbols = db.Column(JSONB)  # List of related symbols
    sentiment = db.Column(db.Float)  # -1 to 1
    categories = db.Column(JSONB)  # List of categories
    
    __table_args__ = (
        Index('idx_news_published', 'published_at'),
        Index('idx_news_symbols', 'symbols', postgresql_using='gin'),
        Index('idx_news_categories', 'categories', postgresql_using='gin'),
    )


class APIRequest(db.Model):
    """API request logging model"""
    __tablename__ = 'api_requests'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    endpoint = db.Column(db.String(200), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer)
    response_time = db.Column(db.Float)  # in milliseconds
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_api_request_user', 'user_id'),
        Index('idx_api_request_created', 'created_at'),
    )


class DataDownload(db.Model):
    """Track data downloads for caching"""
    __tablename__ = 'data_downloads'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = db.Column(db.String(20), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    granularity = db.Column(db.String(10))  # 1s, 1m, 5m, 1h, 1d
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(500))
    
    __table_args__ = (
        Index('idx_download_symbol_source', 'symbol', 'source'),
        Index('idx_download_time_range', 'start_time', 'end_time'),
    )