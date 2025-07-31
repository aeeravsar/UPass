import sqlite3
import json
from pathlib import Path
import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
import threading

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            from config import config
            db_path = config.DATABASE_PATH
        self.db_path = Path(db_path)
        self.local = threading.local()
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row
            self.local.conn.execute("PRAGMA foreign_keys = ON")
            self.local.conn.execute("PRAGMA journal_mode = WAL")
        return self.local.conn
    
    @contextmanager
    def get_db(self):
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def _init_db(self):
        with self.get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vaults (
                    username TEXT PRIMARY KEY,
                    public_key TEXT NOT NULL,
                    vault_blob TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_username ON vaults(username)
            """)
    
    def get_vault(self, username: str) -> Optional[Dict[str, Any]]:
        with self.get_db() as conn:
            cursor = conn.execute(
                "SELECT username, public_key, vault_blob FROM vaults WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def upsert_vault(self, username: str, public_key: str, vault_blob: str) -> bool:
        with self.get_db() as conn:
            # Check if user exists
            existing = conn.execute(
                "SELECT public_key FROM vaults WHERE username = ?", 
                (username,)
            ).fetchone()
            
            if existing:
                # User exists - update only if public key matches
                if existing['public_key'] == public_key:
                    cursor = conn.execute("""
                        UPDATE vaults 
                        SET vault_blob = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE username = ?
                    """, (vault_blob, username))
                    return cursor.rowcount > 0
                else:
                    # Public key mismatch - unauthorized
                    return False
            else:
                # New user - insert
                cursor = conn.execute("""
                    INSERT INTO vaults (username, public_key, vault_blob, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (username, public_key, vault_blob))
                return cursor.rowcount > 0
    
    def delete_vault(self, username: str, public_key: str) -> bool:
        with self.get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM vaults WHERE username = ? AND public_key = ?",
                (username, public_key)
            )
            return cursor.rowcount > 0
    
    def close(self):
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None