import base64
import struct
import time
import hmac
import hashlib
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs

class TOTPManager:
    """Manages Time-based One-Time Password (TOTP) generation"""
    
    DEFAULT_TIME_STEP = 30
    DEFAULT_DIGITS = 6
    DEFAULT_ALGORITHM = 'SHA1'
    
    @staticmethod
    def generate_totp(secret: str, time_step: int = DEFAULT_TIME_STEP, 
                     digits: int = DEFAULT_DIGITS, algorithm: str = DEFAULT_ALGORITHM) -> str:
        """
        Generate a TOTP code from the given secret.
        
        Args:
            secret: Base32 encoded secret
            time_step: Time step in seconds (default: 30)
            digits: Number of digits (default: 6)
            algorithm: Hash algorithm (default: SHA1)
            
        Returns:
            TOTP code as string with leading zeros if necessary
        """
        key = TOTPManager._base32_decode(secret)
        time_counter = int(time.time()) // time_step
        
        return TOTPManager._generate_hotp(key, time_counter, digits, algorithm)
    
    @staticmethod
    def get_remaining_seconds(time_step: int = DEFAULT_TIME_STEP) -> int:
        """Get the remaining seconds until the current TOTP expires"""
        current_seconds = int(time.time())
        return time_step - (current_seconds % time_step)
    
    @staticmethod
    def _generate_hotp(key: bytes, counter: int, digits: int, algorithm: str) -> str:
        """Generate HOTP value"""
        # Convert counter to bytes (big-endian)
        counter_bytes = struct.pack('>Q', counter)
        
        # Get the appropriate hash function
        hash_func = {
            'SHA1': hashlib.sha1,
            'SHA256': hashlib.sha256,
            'SHA512': hashlib.sha512
        }.get(algorithm.upper(), hashlib.sha1)
        
        # Generate HMAC
        hmac_hash = hmac.new(key, counter_bytes, hash_func).digest()
        
        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0F
        truncated = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
        truncated &= 0x7FFFFFFF
        
        # Generate OTP
        otp = truncated % (10 ** digits)
        
        return str(otp).zfill(digits)
    
    @staticmethod
    def _base32_decode(base32_string: str) -> bytes:
        """Decode a Base32 string to bytes"""
        # Remove spaces and convert to uppercase
        base32_string = base32_string.replace(' ', '').upper()
        
        # Add padding if necessary
        padding = len(base32_string) % 8
        if padding:
            base32_string += '=' * (8 - padding)
        
        try:
            return base64.b32decode(base32_string)
        except Exception as e:
            raise ValueError(f"Invalid Base32 string: {e}")
    
    @staticmethod
    def is_valid_secret(secret: str) -> bool:
        """Validate a TOTP secret"""
        try:
            decoded = TOTPManager._base32_decode(secret)
            # At least 80 bits (10 bytes) for security
            return len(decoded) >= 10
        except:
            return False
    
    @staticmethod
    def parse_otpauth_uri(uri: str) -> Optional[dict]:
        """
        Parse an otpauth URI.
        Format: otpauth://totp/Account?secret=BASE32SECRET
        
        Returns:
            Dictionary with parsed parameters or None if invalid
        """
        if not uri.startswith('otpauth://totp/'):
            return None
        
        try:
            parsed = urlparse(uri)
            if parsed.scheme != 'otpauth' or parsed.netloc != 'totp':
                return None
            
            # Parse label (path without leading /) - account only, ignore issuer
            label = parsed.path.lstrip('/')
            if ':' in label:
                # Use account part after colon, ignore issuer
                account = label.split(':', 1)[1]
            else:
                account = label
            
            # Parse query parameters
            params = parse_qs(parsed.query)
            
            secret = params.get('secret', [''])[0]
            if not secret:
                return None
            
            return {
                'secret': secret,
                'account': account,
                'digits': int(params.get('digits', [6])[0]),
                'period': int(params.get('period', [30])[0]),
                'algorithm': params.get('algorithm', ['SHA1'])[0].upper()
            }
        except:
            return None
    
    @staticmethod
    def format_code(code: str) -> str:
        """Format TOTP code for display (e.g., '123 456')"""
        if len(code) == 6:
            return f"{code[:3]} {code[3:]}"
        return code