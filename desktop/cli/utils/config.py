import os
import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

class Config:
    """CLI configuration management with per-server storage"""
    
    def __init__(self, server_url: Optional[str] = None):
        self.base_dir = Path.home() / '.upass'
        self.global_config_file = self.base_dir / 'global_config.json'
        self.server_url = server_url or self._get_server_url()
        self.server_dir = self._get_server_dir()
        self.config_file = self.server_dir / 'config.json'
        
        # Ensure directories exist
        self.base_dir.mkdir(exist_ok=True)
        self.server_dir.mkdir(exist_ok=True)
    
    def _get_server_url(self) -> str:
        """Get server URL from environment, last used, or default"""
        # Priority: 1. Environment variable, 2. Last used server, 3. Default
        env_server = os.environ.get('UPASS_SERVER_URL')
        if env_server:
            return env_server
        
        last_server = self.get_last_server()
        if last_server:
            return last_server
        
        return 'https://server.upass.ch'
    
    def _get_server_dir(self) -> Path:
        """Get server-specific directory based on URL"""
        parsed = urlparse(self.server_url)
        # Create safe directory name from server URL
        server_name = f"{parsed.netloc}_{parsed.port or ('443' if parsed.scheme == 'https' else '80')}"
        # Replace unsafe characters
        server_name = server_name.replace(':', '_').replace('/', '_')
        return self.base_dir / server_name
    
    @property
    def timeout(self) -> int:
        """Get request timeout from environment"""
        return int(os.environ.get('UPASS_TIMEOUT', '10'))
    
    def get_config(self) -> dict:
        """Get configuration for current server"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def set_config(self, config: dict) -> None:
        """Save configuration for current server"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except:
            pass  # Fail silently if can't write config
    
    def get_last_username(self) -> Optional[str]:
        """Get the last used username for current server"""
        config = self.get_config()
        return config.get('last_username')
    
    def set_last_username(self, username: str) -> None:
        """Save the last used username for current server"""
        config = self.get_config()
        config['last_username'] = username
        config['server_url'] = self.server_url  # Save server URL for reference
        self.set_config(config)
    
    def get_session_file(self) -> Path:
        """Get session file path for current server"""
        return self.server_dir / 'session.dat'
    
    def list_servers(self) -> list:
        """List all configured servers"""
        servers = []
        if self.base_dir.exists():
            for server_dir in self.base_dir.iterdir():
                if server_dir.is_dir() and (server_dir / 'config.json').exists():
                    config_file = server_dir / 'config.json'
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                            servers.append({
                                'server_url': config.get('server_url', 'unknown'),
                                'last_username': config.get('last_username'),
                                'dir': server_dir.name
                            })
                    except:
                        continue
        return servers
    
    def get_global_config(self) -> dict:
        """Get global configuration (server-independent)"""
        if self.global_config_file.exists():
            try:
                with open(self.global_config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def set_global_config(self, config: dict) -> None:
        """Save global configuration (server-independent)"""
        try:
            with open(self.global_config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except:
            pass  # Fail silently if can't write config
    
    def get_last_server(self) -> Optional[str]:
        """Get the last used server URL"""
        global_config = self.get_global_config()
        return global_config.get('last_server_url')
    
    def set_last_server(self, server_url: str) -> None:
        """Save the last used server URL"""
        global_config = self.get_global_config()
        global_config['last_server_url'] = server_url
        self.set_global_config(global_config)

def get_config(server_url: Optional[str] = None) -> Config:
    """Get configuration instance for specified server"""
    return Config(server_url)