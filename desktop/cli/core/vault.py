from datetime import datetime
from typing import List, Optional, Dict, Any
import json

class VaultEntry:
    """Represents a single password entry in the vault"""
    
    def __init__(self, username: str, password: str, note: str = "", totp_secret: str = None):
        self.username = username
        self.password = password
        self.note = note
        self.totp_secret = totp_secret
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, str]:
        data = {
            "username": self.username,
            "password": self.password,
            "note": self.note,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        if self.totp_secret:
            data["totp_secret"] = self.totp_secret
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'VaultEntry':
        entry = cls(
            data["username"], 
            data["password"], 
            data.get("note", ""),
            data.get("totp_secret")
        )
        entry.created_at = data.get("created_at", entry.created_at)
        entry.updated_at = data.get("updated_at", entry.updated_at)
        return entry

class Vault:
    """Manages the password vault"""
    
    MAX_ENTRIES = 1024
    MAX_NOTE_LENGTH = 128
    MAX_USERNAME_LENGTH = 64
    MAX_PASSWORD_LENGTH = 128
    MAX_TOTP_SECRET_LENGTH = 64
    
    def __init__(self):
        self.entries: List[VaultEntry] = []
    
    def add_entry(self, username: str, password: str, note: str = "", totp_secret: str = None) -> bool:
        """Add a new entry to the vault"""
        if len(self.entries) >= self.MAX_ENTRIES:
            raise ValueError(f"Vault is full (max {self.MAX_ENTRIES} entries)")
        
        # Validate field lengths
        if len(note) > self.MAX_NOTE_LENGTH:
            raise ValueError(f"Note too long (max {self.MAX_NOTE_LENGTH} characters)")
        if len(username) > self.MAX_USERNAME_LENGTH:
            raise ValueError(f"Username too long (max {self.MAX_USERNAME_LENGTH} characters)")
        if len(password) > self.MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password too long (max {self.MAX_PASSWORD_LENGTH} characters)")
        if totp_secret and len(totp_secret) > self.MAX_TOTP_SECRET_LENGTH:
            raise ValueError(f"TOTP secret too long (max {self.MAX_TOTP_SECRET_LENGTH} characters)")
        
        # Check for duplicates
        for entry in self.entries:
            if entry.note.lower() == note.lower():
                raise ValueError(f"Entry with note '{note}' already exists")
        
        entry = VaultEntry(username, password, note, totp_secret)
        self.entries.append(entry)
        return True
    
    def get_entry(self, note: str) -> Optional[VaultEntry]:
        """Get entry by note (case-insensitive)"""
        for entry in self.entries:
            if entry.note.lower() == note.lower():
                return entry
        return None
    
    def update_entry(self, note: str, username: Optional[str] = None, 
                    password: Optional[str] = None, new_note: Optional[str] = None,
                    totp_secret: Optional[str] = None) -> bool:
        """Update an existing entry"""
        entry = self.get_entry(note)
        if not entry:
            return False
        
        if username is not None:
            entry.username = username
        if password is not None:
            if len(password) > self.MAX_PASSWORD_LENGTH:
                raise ValueError(f"Password too long (max {self.MAX_PASSWORD_LENGTH} characters)")
            entry.password = password
        if new_note is not None:
            # Check if new note already exists
            for e in self.entries:
                if e != entry and e.note.lower() == new_note.lower():
                    raise ValueError(f"Entry with note '{new_note}' already exists")
            entry.note = new_note
        if totp_secret is not None:
            if totp_secret and len(totp_secret) > self.MAX_TOTP_SECRET_LENGTH:
                raise ValueError(f"TOTP secret too long (max {self.MAX_TOTP_SECRET_LENGTH} characters)")
            entry.totp_secret = totp_secret
        
        entry.updated_at = datetime.utcnow().isoformat() + "Z"
        return True
    
    def delete_entry(self, note: str) -> bool:
        """Delete entry by note"""
        entry = self.get_entry(note)
        if not entry:
            return False
        
        self.entries.remove(entry)
        return True
    
    def list_entries(self) -> List[Dict[str, str]]:
        """List all entries (without passwords)"""
        return [
            {
                "note": entry.note,
                "username": entry.username,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at
            }
            for entry in self.entries
        ]
    
    def search_entries(self, query: str) -> List[Dict[str, str]]:
        """Search entries by note or username"""
        query_lower = query.lower()
        results = []
        
        for entry in self.entries:
            if query_lower in entry.note.lower() or query_lower in entry.username.lower():
                results.append({
                    "note": entry.note,
                    "username": entry.username,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at
                })
        
        return results
    
    def to_list(self) -> List[Dict[str, str]]:
        """Convert vault to list format for encryption"""
        return [entry.to_dict() for entry in self.entries]
    
    def from_list(self, data: List[Dict[str, str]]) -> None:
        """Load vault from decrypted list"""
        self.entries = []
        for item in data:
            if len(self.entries) >= self.MAX_ENTRIES:
                break
            try:
                entry = VaultEntry.from_dict(item)
                self.entries.append(entry)
            except (KeyError, TypeError):
                continue  # Skip invalid entries
    
    def clear(self) -> None:
        """Clear all entries from memory"""
        self.entries = []