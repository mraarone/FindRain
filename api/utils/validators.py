# api/utils/validators.py
from datetime import datetime
from typing import Tuple
import re

def validate_symbol(symbol: str) -> str:
    """Validate and normalize stock symbol"""
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string")
    
    symbol = symbol.upper().strip()
    
    # Basic symbol validation
    if not re.match(r'^[A-Z0-9\-\.]{1,20}$', symbol):
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    return symbol


def validate_date(date_str: str) -> datetime:
    """Validate and parse date string"""
    if isinstance(date_str, datetime):
        return date_str
    
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%d-%m-%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Invalid date format: {date_str}")


def validate_date_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    """Validate date range"""
    start = validate_date(start_date)
    end = validate_date(end_date)
    
    if start > end:
        raise ValueError("Start date must be before end date")
    
    # Limit range to prevent excessive data requests
    max_days = 365 * 5  # 5 years
    if (end - start).days > max_days:
        raise ValueError(f"Date range cannot 