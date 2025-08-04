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
    # Vault size calculation (worst case with TOTP support):
    # Field limits:
    # - Title/Note: 128 chars max
    # - Username: 64 chars max
    # - Password: 128 chars max
    # - TOTP secret (Base32): 64 chars max
    # - Timestamps (created_at, updated_at): 48 chars total
    # - JSON overhead per entry: ~100 chars
    # Total per entry: ~532 chars (removed issuer field)
    # 
    # Maximum vault: 1024 entries × 532 chars = 544,768 chars (~545KB)
    # With additional JSON formatting overhead: ~600KB
    # 
    # Setting limit to 1024KB (1MB) provides:
    # - Safe margin for worst-case scenario
    # - Room for future features (recovery codes, etc.)
    # - Prevents edge case failures
    # - Supports up to 1024 entries comfortably
    MAX_VAULT_SIZE = int(os.environ.get('UPASS_MAX_VAULT_SIZE', 1048576))  # 1024KB (1MB)
    MAX_USERNAME_LENGTH = int(os.environ.get('UPASS_MAX_USERNAME_LENGTH', 64))  # Increased from 32
    
    # Timestamp tolerance (seconds)
    TIMESTAMP_TOLERANCE = int(os.environ.get('UPASS_TIMESTAMP_TOLERANCE', 300))  # 5 minutes

config = Config()