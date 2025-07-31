import sys
from core import CryptoManager, APIClient, Vault
from utils import get_password, get_input, validate_username, print_error, print_success, print_info
from utils.config import get_config
from utils.session import get_session_manager
import base64

class UPassSession:
    """Manages authenticated session"""
    
    def __init__(self, server_url: str = None):
        self.config = get_config(server_url)
        self.session_manager = get_session_manager(self.config.get_session_file())
        self.crypto = CryptoManager()
        self.api = APIClient(self.config.server_url, self.config.timeout)
        self.vault = Vault()
        self.username: str = ""
        self.authenticated = False
        
        # Try to restore session on init
        self._restore_session()
    
    def register(self, vault_name: str = None) -> bool:
        """Create new vault"""
        # Auto-logout if already logged in
        if self.authenticated:
            print_info("Closing current vault...")
            self.logout()
        
        # Get vault name
        if not vault_name:
            vault_name = get_input("Vault name: ")
        
        if not vault_name:
            print_error("Vault name is required")
            return False
        
        if not validate_username(vault_name):  # Still use same validation internally
            print_error("Invalid vault name (alphanumeric only, max 32 chars)")
            return False
        
        self.username = vault_name  # Internally still stored as username
        
        # Get master password
        master_password = get_password("Master password: ")
        confirm_password = get_password("Confirm password: ")
        
        if master_password != confirm_password:
            print_error("Passwords do not match")
            return False
        
        # Derive keys
        try:
            print("Deriving keys...")
            self.crypto.derive_keys(master_password, vault_name)
        except Exception as e:
            print_error(f"Failed to derive keys: {e}")
            return False
        
        # Set up API client
        self.api.set_crypto(self.crypto, vault_name)
        
        # Check server connection
        if not self.api.check_health():
            print_error("Cannot connect to server")
            return False
        
        # Check if vault already exists
        try:
            if self.api.check_vault_exists(vault_name):
                print_error("Vault name already exists")
                return False
        except Exception as e:
            print_error(f"Failed to check vault existence: {e}")
            return False
        
        # Set authenticated flag
        self.authenticated = True
        
        # Create new vault
        try:
            print("Creating new vault...")
            if self.save_vault(force_create=True):
                print_success("Vault created successfully!")
                self.config.set_last_username(vault_name)  # Config still uses username internally
                self._save_session()
                return True
            else:
                print_error("Failed to create vault")
                self.authenticated = False
                return False
        except Exception as e:
            print_error(f"Failed to create vault: {e}")
            self.authenticated = False
            return False
    
    def login(self, vault_name: str = None) -> bool:
        """Open existing vault"""
        # Auto-logout if already logged in
        if self.authenticated:
            print_info("Closing current vault...")
            self.logout()
        
        # Get vault name
        if not vault_name:
            last_vault = self.config.get_last_username()  # Config still uses username internally
            prompt = f"Vault name ({last_vault}): " if last_vault else "Vault name: "
            vault_name = get_input(prompt, required=False)
            if not vault_name and last_vault:
                vault_name = last_vault
        
        if not vault_name:
            print_error("Vault name is required")
            return False
        
        if not validate_username(vault_name):  # Still use same validation internally
            print_error("Invalid vault name (alphanumeric only, max 32 chars)")
            return False
        
        self.username = vault_name  # Internally still stored as username
        
        # Get master password
        master_password = get_password("Master password: ")
        
        # Derive keys
        try:
            print("Deriving keys...")
            self.crypto.derive_keys(master_password, vault_name)
        except Exception as e:
            print_error(f"Failed to derive keys: {e}")
            return False
        
        # Set up API client
        self.api.set_crypto(self.crypto, vault_name)
        
        # Check server connection
        if not self.api.check_health():
            print_error("Cannot connect to server")
            return False
        
        # Set authenticated flag before vault operations
        self.authenticated = True
        
        # Try to load vault
        try:
            vault_blob = self.api.get_vault()
            if not vault_blob:
                # Mark vault as not existing
                self.session_manager.set_vault_known_to_exist(False)
                print_error("Vault not found. Use 'upass create-vault' to create a new vault.")
                self.authenticated = False
                return False
            
            # Mark vault as known to exist
            self.session_manager.set_vault_known_to_exist(True)
            vault_data = self.crypto.decrypt_vault(vault_blob)
            self.vault.from_list(vault_data)
            print_success(f"Logged into vault successfully! Loaded {len(self.vault.entries)} entries")
            
        except Exception as e:
            print_error(f"Failed to login to vault: {e}")
            self.authenticated = False
            return False
        
        # Save vault name for next time
        self.config.set_last_username(vault_name)  # Config still uses username internally
        self._save_session()
        return True
    
    def save_vault(self, force_create=False) -> bool:
        """Save vault to server"""
        if not self.authenticated:
            print_error("Not authenticated")
            return False
        
        try:
            vault_data = self.vault.to_list()
            vault_blob = self.crypto.encrypt_vault(vault_data)
            
            # Check if vault is known to exist
            vault_known_to_exist = self.session_manager.is_vault_known_to_exist()
            
            # During registration, force create_if_missing=True, otherwise don't allow recreation
            create_if_missing = force_create
            self.api.put_vault(vault_blob, create_if_missing=create_if_missing)
            
            # Mark vault as known to exist after successful save
            self.session_manager.set_vault_known_to_exist(True)
            
            print_success("Vault saved")
            self._save_session()  # Update session after vault changes
            return True
        except Exception as e:
            if "does not exist" in str(e):
                self.session_manager.set_vault_known_to_exist(False)
                print_error(f"Vault was deleted by another client. {e}")
            else:
                print_error(f"Failed to save vault: {e}")
            return False
    
    def delete_vault(self) -> bool:
        """Delete vault permanently from server"""
        if not self.authenticated:
            print_error("Not authenticated")
            return False
        
        try:
            if self.api.delete_vault():
                print_success("Vault deleted permanently")
                # Clear session after deletion
                self.logout()
                return True
            else:
                print_error("Failed to delete vault")
                return False
        except Exception as e:
            print_error(f"Failed to delete vault: {e}")
            return False
    
    def logout(self):
        """Clear session data"""
        self.crypto.clear_keys()
        self.vault.clear()
        self.authenticated = False
        self.username = ""
        self.session_manager.clear_session()
        print_success("Vault closed")
    
    def _restore_session(self):
        """Restore session from saved data"""
        session_data = self.session_manager.load_session()
        if not session_data:
            return
        
        try:
            # Restore all session data
            self.username = session_data['username']
            self.authenticated = session_data['authenticated']
            
            # Restore crypto keys for current HMAC-SHA256 + AES-GCM implementation
            self.crypto.public_key_b64 = session_data['public_key_b64']
            
            # Restore HMAC signing key (raw bytes)
            self.crypto.signing_key = base64.b64decode(session_data['signing_key_bytes'])
            
            # Restore AES key and recreate AES-GCM cipher object
            self.crypto.aes_key = base64.b64decode(session_data['secret_box_key'])  # Key field name is historical
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            self.crypto.aes_gcm = AESGCM(self.crypto.aes_key)
            
            # Set up API client
            self.api.set_crypto(self.crypto, self.username)
            
            # Fetch vault from server (not from session file)
            try:
                vault_blob = self.api.get_vault()
                if vault_blob:
                    vault_data = self.crypto.decrypt_vault(vault_blob)
                    self.vault.from_list(vault_data)
                    self.session_manager.set_vault_known_to_exist(True)
                else:
                    self.session_manager.set_vault_known_to_exist(False)
            except:
                # If we can't fetch vault, assume it doesn't exist
                self.session_manager.set_vault_known_to_exist(False)
            
        except Exception:
            # If restore fails, clear session
            self.session_manager.clear_session()
    
    def _save_session(self):
        """Save current session (without vault data)"""
        if not self.authenticated or not self.crypto.signing_key:
            return
        
        try:
            # Get raw key material for current crypto implementation
            signing_key_bytes = self.crypto.signing_key
            # Get AES key that we now store separately
            aes_key = self.crypto.aes_key
            
            self.session_manager.save_session(
                self.username,
                self.crypto.public_key_b64,
                signing_key_bytes,
                aes_key
            )
        except Exception as e:
            # Silent failure - session persistence is not critical
            pass