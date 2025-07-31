import base64
import json
import secrets
import hmac
import hashlib
import os
from typing import Tuple, Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import nacl.utils
import nacl.pwhash

class CryptoManager:
    """Handles all cryptographic operations for UPass CLI"""
    
    def __init__(self):
        self.signing_key: Optional[bytes] = None
        self.aes_key: Optional[bytes] = None
        self.aes_gcm: Optional[AESGCM] = None
        self.public_key_b64: Optional[str] = None
    
    def derive_keys(self, master_password: str, username: str) -> None:
        """
        Derive HMAC signing key and AES key from master password using Argon2id
        """
        # Create a salt from username to ensure deterministic key generation
        salt = nacl.utils.random(nacl.pwhash.argon2id.SALTBYTES)
        salt = username.encode('utf-8').ljust(len(salt), b'\x00')[:len(salt)]
        
        # Derive 256-bit signing key using Argon2id
        self.signing_key = nacl.pwhash.argon2id.kdf(
            size=32,
            password=master_password.encode('utf-8'),
            salt=salt,
            opslimit=nacl.pwhash.argon2id.OPSLIMIT_SENSITIVE,
            memlimit=nacl.pwhash.argon2id.MEMLIMIT_SENSITIVE
        )
        
        # Public key is SHA256 of the signing key
        public_key_bytes = hashlib.sha256(self.signing_key).digest()
        self.public_key_b64 = base64.b64encode(public_key_bytes).decode('utf-8')
        
        # Derive AES key for vault encryption
        self.aes_key = nacl.pwhash.argon2id.kdf(
            size=32,
            password=(master_password + "vault").encode('utf-8'),
            salt=salt,
            opslimit=nacl.pwhash.argon2id.OPSLIMIT_SENSITIVE,
            memlimit=nacl.pwhash.argon2id.MEMLIMIT_SENSITIVE
        )
        
        # Create AES-GCM cipher for symmetric encryption
        self.aes_gcm = AESGCM(self.aes_key)
    
    def sign_message(self, message: bytes) -> str:
        """Sign a message using HMAC-SHA256 and return base64 encoded signature"""
        if not self.signing_key:
            raise ValueError("Keys not derived yet")
        
        signature = hmac.new(self.signing_key, message, hashlib.sha256).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def encrypt_vault(self, vault_data: list) -> str:
        """Encrypt vault data using AES-GCM and return base64 encoded blob"""
        if not self.aes_gcm:
            raise ValueError("Keys not derived yet")
        
        json_data = json.dumps(vault_data).encode('utf-8')
        
        # Generate random 12-byte IV (same as Android)
        iv = os.urandom(12)
        
        # Encrypt with AES-GCM
        encrypted_data = self.aes_gcm.encrypt(iv, json_data, None)
        
        # Prepend IV to encrypted data (same format as Android)
        result = iv + encrypted_data
        
        return base64.b64encode(result).decode('utf-8')
    
    def decrypt_vault(self, vault_blob: str) -> list:
        """Decrypt vault blob using AES-GCM and return vault data"""
        if not self.aes_gcm:
            raise ValueError("Keys not derived yet")
        
        try:
            encrypted_data = base64.b64decode(vault_blob)
            
            if len(encrypted_data) < 12:
                raise ValueError("Invalid encrypted data: too short")
            
            # Extract IV and ciphertext (same format as Android)
            iv = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            
            # Decrypt with AES-GCM
            decrypted = self.aes_gcm.decrypt(iv, ciphertext, None)
            
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Failed to decrypt vault: {str(e)}")
    
    def generate_password(self, length: int = 16, special_chars: bool = True) -> str:
        """Generate a secure, readable random password with proper character distribution"""
        if length < 4:
            length = 4
        
        # Define character sets
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        numbers = "0123456789"
        # Use more readable special characters, avoiding confusing ones
        specials = "!@#$%^&*-_=+" if special_chars else ""
        
        # Ensure we have at least one character from each required set
        password = []
        
        # Always include at least one lowercase, uppercase, and number
        password.append(secrets.choice(lowercase))
        password.append(secrets.choice(uppercase))
        password.append(secrets.choice(numbers))
        
        # Add one special character if enabled
        if special_chars and length > 3:
            password.append(secrets.choice(specials))
        
        # Fill remaining positions
        all_chars = lowercase + uppercase + numbers + specials
        remaining_length = length - len(password)
        
        for _ in range(remaining_length):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password to avoid predictable patterns
        # Convert to list for shuffling, then back to string
        password_list = list(password)
        for i in range(len(password_list)):
            j = secrets.randbelow(len(password_list))
            password_list[i], password_list[j] = password_list[j], password_list[i]
        
        return ''.join(password_list)
    
    def clear_keys(self) -> None:
        """Clear sensitive key material from memory"""
        self.signing_key = None
        self.aes_key = None
        self.aes_gcm = None
        self.public_key_b64 = None