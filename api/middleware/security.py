# api/middleware/security.py
from flask import Flask, request, abort
from werkzeug.exceptions import HTTPException
import re
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware for the application"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.setup_security_headers()
        self.setup_request_validation()
        
    def setup_security_headers(self):
        """Add security headers to all responses"""
        @self.app.after_request
        def add_security_headers(response):
            # Security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Remove server header
            response.headers.pop('Server', None)
            
            return response
    
    def setup_request_validation(self):
        """Validate incoming requests"""
        @self.app.before_request
        def validate_request():
            # Check request size
            if request.content_length and request.content_length > 10 * 1024 * 1024:  # 10MB
                abort(413, "Request too large")
            
            # Validate JSON content type for POST/PUT
            if request.method in ['POST', 'PUT']:
                if request.is_json is False and request.content_type != 'application/json':
                    abort(415, "Content-Type must be application/json")
            
            # SQL injection protection
            for key, value in request.args.items():
                if self._contains_sql_injection(str(value)):
                    logger.warning(f"Potential SQL injection attempt: {value}")
                    abort(400, "Invalid input")
            
            # XSS protection
            if request.is_json:
                json_data = request.get_json(silent=True)
                if json_data and self._contains_xss(json_data):
                    logger.warning("Potential XSS attempt in JSON")
                    abort(400, "Invalid input")
    
    def _contains_sql_injection(self, value: str) -> bool:
        """Check for SQL injection patterns"""
        sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create)\b)",
            r"(--|#|\/\*|\*\/)",
            r"(\bor\b\s*\d+\s*=\s*\d+)",
            r"(\band\b\s*\d+\s*=\s*\d+)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def _contains_xss(self, data) -> bool:
        """Check for XSS patterns in data"""
        if isinstance(data, str):
            xss_patterns = [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe",
                r"<object",
                r"<embed"
            ]
            
            for pattern in xss_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    return True
        
        elif isinstance(data, dict):
            for value in data.values():
                if self._contains_xss(value):
                    return True
        
        elif isinstance(data, list):
            for item in data:
                if self._contains_xss(item):
                    return True
        
        return False
