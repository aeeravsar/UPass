import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent.parent
    DATABASE_PATH = os.environ.get('UPASS_DB_PATH', BASE_DIR / 'upass.db')
    
    # Security
    SECRET_KEY = os.environ.get('UPASS_SECRET_KEY', 'dev-key-change-in-production')
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.environ.get('UPASS_RATE_LIMIT', 'true').lower() == 'true'
    RATE_LIMIT_DEFAULT = os.environ.get('UPASS_RATE_LIMIT_DEFAULT', '10/minute')
    
    # Server
    HOST = os.environ.get('UPASS_HOST', '0.0.0.0')
    PORT = int(os.environ.get('UPASS_PORT', 8000))
    DEBUG = os.environ.get('UPASS_DEBUG', 'false').lower() == 'true'
    
    # CORS
    CORS_ORIGINS = os.environ.get('UPASS_CORS_ORIGINS', '*')
    
    # Logging
    LOG_LEVEL = os.environ.get('UPASS_LOG_LEVEL', 'INFO')
    
    # Limits
    MAX_VAULT_SIZE = int(os.environ.get('UPASS_MAX_VAULT_SIZE', 100000))  # 100KB
    MAX_USERNAME_LENGTH = int(os.environ.get('UPASS_MAX_USERNAME_LENGTH', 32))
    
    # Timestamp tolerance (seconds)
    TIMESTAMP_TOLERANCE = int(os.environ.get('UPASS_TIMESTAMP_TOLERANCE', 300))  # 5 minutes

config = Config()