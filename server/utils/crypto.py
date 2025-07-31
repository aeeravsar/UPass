import base64
import time
import hmac
import hashlib
from typing import Optional, Tuple

class CryptoVerifier:
    @staticmethod
    def get_timestamp_tolerance():
        from config import config
        return config.TIMESTAMP_TOLERANCE
    
    @staticmethod
    def decode_base64(data: str) -> Optional[bytes]:
        try:
            return base64.b64decode(data)
        except Exception:
            return None
    
    @staticmethod
    def encode_base64(data: bytes) -> str:
        return base64.b64encode(data).decode('utf-8')
    
    @staticmethod
    def verify_timestamp(timestamp: int) -> bool:
        current_time = int(time.time())
        time_diff = abs(current_time - timestamp)
        return time_diff <= CryptoVerifier.get_timestamp_tolerance()
    
    @staticmethod
    def verify_signature(
        stored_public_key_b64: str,
        provided_signing_key_b64: str,
        signature_b64: str,
        message: bytes
    ) -> bool:
        """
        Verify HMAC-SHA256 signature with public key validation.
        stored_public_key_b64: Base64-encoded stored public key (SHA256 of signing key)
        provided_signing_key_b64: Base64-encoded signing key provided by client
        signature_b64: Base64-encoded HMAC signature
        message: Message bytes that were signed
        """
        try:
            stored_public_key = CryptoVerifier.decode_base64(stored_public_key_b64)
            signing_key = CryptoVerifier.decode_base64(provided_signing_key_b64)
            signature_bytes = CryptoVerifier.decode_base64(signature_b64)
            
            if not stored_public_key or not signing_key or not signature_bytes:
                return False
            
            # Verify that the provided signing key matches the stored public key
            derived_public_key = hashlib.sha256(signing_key).digest()
            if not hmac.compare_digest(stored_public_key, derived_public_key):
                return False
            
            # Compute expected HMAC
            expected_signature = hmac.new(
                signing_key,
                message,
                hashlib.sha256
            ).digest()
            
            # Constant-time comparison
            return hmac.compare_digest(signature_bytes, expected_signature)
            
        except Exception:
            return False
    
    @staticmethod
    def verify_vault_get(
        stored_public_key: str,
        provided_signing_key: str,
        signature: str,
        timestamp: int
    ) -> bool:
        if not CryptoVerifier.verify_timestamp(timestamp):
            return False
        
        message = f"get_vault{timestamp}".encode('utf-8')
        return CryptoVerifier.verify_signature(stored_public_key, provided_signing_key, signature, message)
    
    @staticmethod
    def verify_vault_put(
        stored_public_key: str,
        provided_signing_key: str,
        signature: str,
        vault_blob: str,
        timestamp: int
    ) -> bool:
        if not CryptoVerifier.verify_timestamp(timestamp):
            return False
        
        message = f"{vault_blob}{timestamp}".encode('utf-8')
        return CryptoVerifier.verify_signature(stored_public_key, provided_signing_key, signature, message)
    
    @staticmethod
    def verify_vault_delete(
        stored_public_key: str,
        provided_signing_key: str,
        signature: str,
        timestamp: int
    ) -> bool:
        if not CryptoVerifier.verify_timestamp(timestamp):
            return False
        
        message = f"delete_vault{timestamp}".encode('utf-8')
        return CryptoVerifier.verify_signature(stored_public_key, provided_signing_key, signature, message)