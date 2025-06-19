# api/routes/technical.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
import numpy as np
import pandas as pd

technical_bp = Blueprint('technical', __name__)

@technical_bp.route('/indicators/<symbol>', methods=['GET'])
@jwt_required()
@rate_limit_by_tier
async def get_technical_indicators(symbol: str):
    """Get technical indicators for a symbol"""
    try:
        symbol = validate_symbol(symbol)
        indicators = request.args.getlist('indicators')
        period = int(request.args.get('period', 14))
        
        if not indicators:
            indicators = ['sma', 'ema', 'rsi', 'macd']
        
        # Get historical data
        aggregator: DataAggregator = current_app.aggregator
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period * 2)  # Get extra data for calculations
        
        data = await aggregator.get_historical(symbol, start_date, end_date, '1d')
        
        if not data:
            return jsonify({'error': f'No data found for {symbol}'}), 404
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Calculate indicators
        results = {'symbol': symbol, 'indicators': {}}
        
        if 'sma' in indicators:
            results['indicators']['sma'] = calculate_sma(df, period)
        
        if 'ema' in indicators:
            results['indicators']['ema'] = calculate_ema(df, period)
        
        if 'rsi' in indicators:
            results['indicators']['rsi'] = calculate_rsi(df, period)
        
        if 'macd' in indicators:
            results['indicators']['macd'] = calculate_macd(df)
        
        if 'bollinger' in indicators:
            results['indicators']['bollinger'] = calculate_bollinger_bands(df, period)
        
        if 'stochastic' in indicators:
            results['indicators']['stochastic'] = calculate_stochastic(df, period)
        
        return jsonify(results), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def calculate_sma(df: pd.DataFrame, period: int) -> dict:
    """Calculate Simple Moving Average"""
    sma = df['close'].rolling(window=period).mean()
    
    return {
        'period': period,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'value': float(val) if not pd.isna(val) else None
            }
            for ts, val in sma.items()
        ]
    }


def calculate_ema(df: pd.DataFrame, period: int) -> dict:
    """Calculate Exponential Moving Average"""
    ema = df['close'].ewm(span=period, adjust=False).mean()
    
    return {
        'period': period,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'value': float(val) if not pd.isna(val) else None
            }
            for ts, val in ema.items()
        ]
    }


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> dict:
    """Calculate Relative Strength Index"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return {
        'period': period,
        'overbought': 70,
        'oversold': 30,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'value': float(val) if not pd.isna(val) else None
            }
            for ts, val in rsi.items()
        ]
    }


def calculate_macd(df: pd.DataFrame) -> dict:
    """Calculate MACD"""
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    
    return {
        'values': [
            {
                'timestamp': ts.isoformat(),
                'macd': float(macd.loc[ts]) if not pd.isna(macd.loc[ts]) else None,
                'signal': float(signal.loc[ts]) if not pd.isna(signal.loc[ts]) else None,
                'histogram': float(histogram.loc[ts]) if not pd.isna(histogram.loc[ts]) else None
            }
            for ts in macd.index
        ]
    }


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> dict:
    """Calculate Bollinger Bands"""
    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return {
        'period': period,
        'std_dev': std_dev,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'upper': float(upper.loc[ts]) if not pd.isna(upper.loc[ts]) else None,
                'middle': float(sma.loc[ts]) if not pd.isna(sma.loc[ts]) else None,
                'lower': float(lower.loc[ts]) if not pd.isna(lower.loc[ts]) else None
            }
            for ts in sma.index
        ]
    }


def calculate_stochastic(df: pd.DataFrame, period: int = 14) -> dict:
    """Calculate Stochastic Oscillator"""
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    
    k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
    d_percent = k_percent.rolling(window=3).mean()
    
    return {
        'period': period,
        'overbought': 80,
        'oversold': 20,
        'values': [
            {
                'timestamp': ts.isoformat(),
                'k': float(k_percent.loc[ts]) if not pd.isna(k_percent.loc[ts]) else None,
                'd': float(d_percent.loc[ts]) if not pd.isna(d_percent.loc[ts]) else None
            }
            for ts in k_percent.index
        ]
    }
