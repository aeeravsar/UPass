from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import logging

logger = logging.getLogger(__name__)

def get_identifier():
    return f"{get_remote_address()}:{request.endpoint}"

def setup_middleware(app, config):
    # CORS
    CORS(app, origins=config.CORS_ORIGINS)
    
    # Rate limiting
    if config.RATE_LIMIT_ENABLED:
        limiter = Limiter(
            app=app,
            key_func=get_identifier,
            default_limits=[config.RATE_LIMIT_DEFAULT],
            storage_uri="memory://",
        )
        
        # Specific limits for vault operations
        limiter.limit("5/minute")(app.view_functions['vault.get_vault'])
        limiter.limit("3/minute")(app.view_functions['vault.put_vault'])
        limiter.limit("1/minute")(app.view_functions['vault.delete_vault'])
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
    
    # Request logging
    @app.before_request
    def log_request():
        logger.debug(f"{request.method} {request.path}")
    
    # No telemetry, no tracking - respecting UPass principles
    @app.before_request
    def strip_tracking_headers():
        # Remove any tracking-related headers
        headers_to_remove = ['X-Forwarded-For', 'X-Real-IP', 'User-Agent']
        for header in headers_to_remove:
            request.environ.pop(f'HTTP_{header.upper().replace("-", "_")}', None)