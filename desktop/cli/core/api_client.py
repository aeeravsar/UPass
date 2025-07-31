import requests
import time
import json
import base64
from typing import Optional, Dict, Any
from core.crypto import CryptoManager

class APIClient:
    """Handles communication with UPass server"""
    
    def __init__(self, server_url: str = "http://localhost:8000", timeout: int = 10):
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.crypto: Optional[CryptoManager] = None
        self.username: Optional[str] = None
    
    def set_crypto(self, crypto: CryptoManager, username: str):
        """Set crypto manager and username for authenticated requests"""
        self.crypto = crypto
        self.username = username
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Make HTTP request to server"""
        url = f"{self.server_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                return requests.get(url, headers=headers, timeout=self.timeout)
            elif method == 'PUT':
                return requests.put(url, json=data, headers=headers, timeout=self.timeout)
            elif method == 'POST':
                return requests.post(url, json=data, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Failed to connect to server. Is the server running?")
        except requests.exceptions.Timeout:
            raise TimeoutError("Request timed out")
    
    def check_vault_exists(self, username: str) -> bool:
        """Check if a vault exists for the given username"""
        response = self._make_request('GET', f'/vaults/{username}/exists')
        
        if response.status_code == 200:
            return response.json().get('exists', False)
        else:
            error = response.json().get('error', 'Unknown error')
            raise Exception(f"Failed to check vault existence: {error}")
    
    def get_vault(self) -> Optional[str]:
        """Retrieve encrypted vault from server"""
        if not self.crypto or not self.username:
            raise ValueError("Not authenticated")
        
        timestamp = int(time.time())
        message = f"get_vault{timestamp}".encode('utf-8')
        signature = self.crypto.sign_message(message)
        
        data = {
            "public_key": self.crypto.public_key_b64,
            "signing_key": base64.b64encode(self.crypto.signing_key).decode('utf-8'),
            "timestamp": timestamp,
            "signature": signature
        }
        
        response = self._make_request('POST', f'/vaults/{self.username}/retrieve', data)
        
        if response.status_code == 200:
            return response.json().get('vault_blob')
        elif response.status_code == 404:
            return None  # Vault doesn't exist yet
        else:
            error = response.json().get('error', 'Unknown error')
            raise Exception(f"Failed to get vault: {error}")
    
    def put_vault(self, vault_blob: str, create_if_missing: bool = True) -> bool:
        """Save encrypted vault to server"""
        if not self.crypto or not self.username:
            raise ValueError("Not authenticated")
        
        timestamp = int(time.time())
        message = f"{vault_blob}{timestamp}".encode('utf-8')
        signature = self.crypto.sign_message(message)
        
        data = {
            "public_key": self.crypto.public_key_b64,
            "signing_key": base64.b64encode(self.crypto.signing_key).decode('utf-8'),
            "timestamp": timestamp,
            "vault_blob": vault_blob,
            "signature": signature,
            "create_if_missing": create_if_missing
        }
        
        response = self._make_request('PUT', f'/vaults/{self.username}', data)
        
        if response.status_code == 200:
            return True
        else:
            error = response.json().get('error', 'Unknown error')
            raise Exception(f"Failed to save vault: {error}")
    
    def delete_vault(self) -> bool:
        """Delete vault from server"""
        if not self.crypto or not self.username:
            raise ValueError("Not authenticated")
        
        timestamp = int(time.time())
        message = f"delete_vault{timestamp}".encode('utf-8')
        signature = self.crypto.sign_message(message)
        
        data = {
            "public_key": self.crypto.public_key_b64,
            "signing_key": base64.b64encode(self.crypto.signing_key).decode('utf-8'),
            "timestamp": timestamp,
            "signature": signature
        }
        
        response = self._make_request('POST', f'/vaults/{self.username}/delete', data)
        
        if response.status_code == 200:
            return True
        else:
            error = response.json().get('error', 'Unknown error')
            raise Exception(f"Failed to delete vault: {error}")
    
    def check_health(self) -> bool:
        """Check if server is healthy"""
        try:
            response = self._make_request('GET', '/health')
            return response.status_code == 200
        except:
            return False