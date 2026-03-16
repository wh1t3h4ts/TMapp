import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class Note:
    """Data class representing a note."""
    id: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = None

class NoteManager:
    """
    Manages note storage and retrieval with encryption.
    Security Controls: Information Disclosure, Tampering
    """
    
    def __init__(self, encryption_service):
        self.encryption_service = encryption_service
        self.db_path = Path(os.path.expanduser("~/.secure-notes")) / "notes.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with notes table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    title_encrypted TEXT NOT NULL,
                    content_encrypted TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags_encrypted TEXT DEFAULT ''
                )
            """)
            
            # Create index for faster searches
            conn.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON notes(updated_at)")
            conn.commit()
    
    def create_note(self, content: str, title: str = None) -> str:
        """Create a new note and return its ID."""
        note_id = str(uuid.uuid4())
        
        if not title:
            # Extract title from first line
            title = content.split('\n')[0][:50] or "Untitled Note"
        
        # Encrypt sensitive data
        title_encrypted = self.encryption_service.encrypt(title)
        content_encrypted = self.encryption_service.encrypt(content)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO notes (id, title_encrypted, content_encrypted)
                VALUES (?, ?, ?)
            """, (note_id, title_encrypted, content_encrypted))
            conn.commit()
        
        return note_id
    
    def get_note(self, note_id: str) -> Optional[Note]:
        """Retrieve a note by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title_encrypted, content_encrypted, created_at, updated_at, tags_encrypted
                FROM notes WHERE id = ?
            """, (note_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Decrypt sensitive data
            title = self.encryption_service.decrypt(row[1])
            content = self.encryption_service.decrypt(row[2])
            tags_str = self.encryption_service.decrypt(row[5]) if row[5] else ""
            tags = tags_str.split(",") if tags_str else []
            
            return Note(
                id=row[0],
                title=title,
                content=content,
                created_at=datetime.fromisoformat(row[3]),
                updated_at=datetime.fromisoformat(row[4]),
                tags=tags
            )
    
    def update_note(self, note_id: str, content: str, title: str = None) -> bool:
        """Update an existing note."""
        if not title:
            # Extract title from first line
            title = content.split('\n')[0][:50] or "Untitled Note"
        
        # Encrypt sensitive data
        title_encrypted = self.encryption_service.encrypt(title)
        content_encrypted = self.encryption_service.encrypt(content)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE notes 
                SET title_encrypted = ?, content_encrypted = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title_encrypted, content_encrypted, note_id))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def list_notes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all notes (metadata only for performance)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title_encrypted, created_at, updated_at
                FROM notes 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (limit,))
            
            notes = []
            for row in cursor.fetchall():
                # Decrypt only title for list view
                title = self.encryption_service.decrypt(row[1])
                notes.append({
                    'id': row[0],
                    'title': title,
                    'created_at': row[2],
                    'updated_at': row[3]
                })
            
            return notes
    
    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """Search notes (decrypts content for searching - performance trade-off for security)."""
        # Note: This is a security vs performance trade-off
        # For better security, consider client-side search indexing
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title_encrypted, content_encrypted, created_at, updated_at
                FROM notes 
                ORDER BY updated_at DESC
            """)
            
            matching_notes = []
            query_lower = query.lower()
            
            for row in cursor.fetchall():
                try:
                    # Decrypt and search
                    title = self.encryption_service.decrypt(row[1])
                    content = self.encryption_service.decrypt(row[2])
                    
                    if (query_lower in title.lower() or 
                        query_lower in content.lower()):
                        matching_notes.append({
                            'id': row[0],
                            'title': title,
                            'created_at': row[3],
                            'updated_at': row[4]
                        })
                except Exception:
                    # Skip corrupted notes
                    continue
            
            return matching_notes