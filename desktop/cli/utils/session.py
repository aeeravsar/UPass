import os
import json
import time
import base64
from pathlib import Path
from typing import Optional, Dict, Any
import pickle

class SessionManager:
    """Manages session persistence per server"""
    
    def __init__(self, session_file: Path):
        self.session_file = session_file
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_timeout = 7 * 24 * 3600  # 7 days
    
    def save_session(self, username: str, public_key_b64: str, signing_key_bytes: bytes, aes_key: bytes, vault_known_to_exist: bool = True) -> None:
        """Save session data (NO vault data for security)"""
        session_data = {
            'username': username,
            'public_key_b64': public_key_b64,
            'signing_key_bytes': base64.b64encode(signing_key_bytes).decode(),
            'secret_box_key': base64.b64encode(aes_key).decode(),  # Keep old field name for compatibility
            'timestamp': int(time.time()),
            'authenticated': True,
            'vault_known_to_exist': vault_known_to_exist
        }
        
        try:
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
            # Make file readable only by user
            os.chmod(self.session_file, 0o600)
        except Exception as e:
            # Silent failure - session persistence is not critical
            pass
    
    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load session data if valid"""
        try:
            if not self.session_file.exists():
                return None
            
            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            # Check if session expired
            current_time = int(time.time())
            if current_time - session_data['timestamp'] > self.session_timeout:
                self.clear_session()
                return None
            
            return session_data
        except Exception:
            self.clear_session()
            return None
    
    def clear_session(self) -> None:
        """Clear session data"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
        except Exception:
            pass
    
    def extend_session(self) -> None:
        """Extend current session timeout"""
        session_data = self.load_session()
        if session_data:
            session_data['timestamp'] = int(time.time())
            try:
                with open(self.session_file, 'wb') as f:
                    pickle.dump(session_data, f)
            except Exception:
                pass
    
    def is_vault_known_to_exist(self) -> bool:
        """Check if vault is known to exist"""
        session_data = self.load_session()
        return session_data.get('vault_known_to_exist', False) if session_data else False
    
    def set_vault_known_to_exist(self, exists: bool) -> None:
        """Set vault existence state"""
        session_data = self.load_session()
        if session_data:
            session_data['vault_known_to_exist'] = exists
            try:
                with open(self.session_file, 'wb') as f:
                    pickle.dump(session_data, f)
            except Exception:
                pass

def get_session_manager(session_file: Path) -> SessionManager:
    """Get session manager for specified session file"""
    return SessionManager(session_file)