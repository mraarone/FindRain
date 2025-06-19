# api/routes/news.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta

from ..database.models import db, NewsArticle

news_bp = Blueprint('news', __name__)

@news_bp.route('/news', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_news():
    """Get news articles"""
    try:
        # Get parameters
        query = request.args.get('q', '')
        symbols = request.args.getlist('symbols')
        limit = min(int(request.args.get('limit', 20)), 100)
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


@news_bp.route('/news/sentiment/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_sentiment_analysis(symbol: str):
    """Get sentiment analysis for a symbol"""
    try:
        symbol = validate_symbol(symbol)
        days_back = int(request.args.get('days', 7))
        
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
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'positive_percent': (positive / len(sentiments) * 100) if sentiments else 0,
                'neutral_percent': (neutral / len(sentiments) * 100) if sentiments else 0,
                'negative_percent': (negative / len(sentiments) * 100) if sentiments else 0
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
