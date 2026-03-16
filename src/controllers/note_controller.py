import logging
from typing import List, Optional
from datetime import datetime

from src.models.note import Note
from src.core.database import Database
from src.core.encryption import EncryptionService

logger = logging.getLogger(__name__)


class NoteController:
    """Controller for all note operations with encryption."""
    
    def __init__(self, database: Database, encryption_service: EncryptionService):
        self.db = database
        self.encryption = encryption_service
        logger.info("NoteController initialized")
    
    def create_note(self, title: str = "Untitled Note", 
                   notebook_id: Optional[str] = None,
                   content: str = "") -> Note:
        """
        Create a new note with encryption.
        
        Args:
            title: Note title
            notebook_id: Parent notebook ID
            content: Note content
            
        Returns:
            Created Note object
        """
        try:
            # Create note object
            note = Note.create_new(title=title, notebook_id=notebook_id)
            note.content = content if content else " "  # Use space for empty content
            note.update_metadata(content)
            
            # Encrypt sensitive fields (handle empty strings)
            encrypted_title = self.encryption.encrypt(note.title if note.title else "Untitled Note")
            encrypted_content = self.encryption.encrypt(note.content)
            
            # Insert into database
            self.db.execute("""
                INSERT INTO notes (
                    id, title, content, notebook_id, tags, created_at, modified_at,
                    is_favorite, is_pinned, is_archived, is_trashed, color,
                    attachments, images, links, has_tasks, completed_tasks, total_tasks,
                    word_count, character_count, reading_time, encrypted, encryption_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                note.id, encrypted_title, encrypted_content, note.notebook_id,
                ','.join(note.tags), note.created_at.isoformat(), note.modified_at.isoformat(),
                int(note.is_favorite), int(note.is_pinned), int(note.is_archived), 
                int(note.is_trashed), note.color,
                ','.join(note.attachments), ','.join(note.images), ','.join(note.links),
                int(note.has_tasks), note.completed_tasks, note.total_tasks,
                note.word_count, note.character_count, note.reading_time,
                int(note.encrypted), note.encryption_version
            ))
            
            logger.info(f"Created note: {note.id}")
            return note
        
        except Exception as e:
            logger.error(f"Failed to create note: {e}", exc_info=True)
            raise
    
    def get_note(self, note_id: str) -> Optional[Note]:
        """
        Retrieve and decrypt a note by ID.
        
        Args:
            note_id: Note ID
            
        Returns:
            Decrypted Note object or None
        """
        try:
            result = self.db.query_one("""
                SELECT * FROM notes WHERE id = ? AND is_trashed = 0
            """, (note_id,))
            
            if not result:
                return None
            
            # Convert to dict and decrypt
            note_dict = dict(result)
            note_dict['title'] = self.encryption.decrypt(note_dict['title'])
            decrypted_content = self.encryption.decrypt(note_dict['content'])
            # Remove placeholder space if it was added for empty content
            note_dict['content'] = decrypted_content.strip() if decrypted_content == " " else decrypted_content
            
            return Note.from_dict(note_dict)
        
        except Exception as e:
            logger.error(f"Failed to get note {note_id}: {e}")
            return None
    
    def update_note(self, note: Note) -> bool:
        """
        Update an existing note with encryption.
        
        Args:
            note: Note object with updated data
            
        Returns:
            Success status
        """
        try:
            note.update_metadata(note.content)
            
            # Encrypt sensitive fields (handle empty strings)
            encrypted_title = self.encryption.encrypt(note.title if note.title else "Untitled Note")
            # Use space for empty content to avoid encryption error
            content_to_encrypt = note.content if note.content.strip() else " "
            encrypted_content = self.encryption.encrypt(content_to_encrypt)
            
            # Update database
            self.db.execute("""
                UPDATE notes SET
                    title = ?, content = ?, notebook_id = ?, tags = ?, modified_at = ?,
                    is_favorite = ?, is_pinned = ?, is_archived = ?, is_trashed = ?, color = ?,
                    attachments = ?, images = ?, links = ?,
                    has_tasks = ?, completed_tasks = ?, total_tasks = ?,
                    word_count = ?, character_count = ?, reading_time = ?
                WHERE id = ?
            """, (
                encrypted_title, encrypted_content, note.notebook_id, ','.join(note.tags),
                note.modified_at.isoformat(), int(note.is_favorite), int(note.is_pinned),
                int(note.is_archived), int(note.is_trashed), note.color,
                ','.join(note.attachments), ','.join(note.images), ','.join(note.links),
                int(note.has_tasks), note.completed_tasks, note.total_tasks,
                note.word_count, note.character_count, note.reading_time,
                note.id
            ))
            
            logger.info(f"Updated note: {note.id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update note {note.id}: {e}")
            return False
    
    def delete_note(self, note_id: str, permanent: bool = False) -> bool:
        """
        Delete a note (soft or permanent).
        
        Args:
            note_id: Note ID
            permanent: If True, permanently delete; if False, move to trash
            
        Returns:
            Success status
        """
        try:
            if permanent:
                # Permanent delete
                self.db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                logger.info(f"Permanently deleted note: {note_id}")
            else:
                # Soft delete (move to trash)
                self.db.execute("""
                    UPDATE notes SET is_trashed = 1, modified_at = ? WHERE id = ?
                """, (datetime.now().isoformat(), note_id))
                logger.info(f"Moved note to trash: {note_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete note {note_id}: {e}")
            return False
    
    def restore_note(self, note_id: str) -> bool:
        """
        Restore a note from trash.
        
        Args:
            note_id: Note ID
            
        Returns:
            Success status
        """
        try:
            self.db.execute("""
                UPDATE notes SET is_trashed = 0, modified_at = ? WHERE id = ?
            """, (datetime.now().isoformat(), note_id))
            
            logger.info(f"Restored note from trash: {note_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to restore note {note_id}: {e}")
            return False
    
    def get_all_notes(self, include_trashed: bool = False, 
                     include_archived: bool = True) -> List[Note]:
        """
        Get all notes with optional filters.
        
        Args:
            include_trashed: Include trashed notes
            include_archived: Include archived notes
            
        Returns:
            List of Note objects (titles decrypted, content not)
        """
        try:
            query = "SELECT * FROM notes WHERE 1=1"
            
            if not include_trashed:
                query += " AND is_trashed = 0"
            
            if not include_archived:
                query += " AND is_archived = 0"
            
            query += " ORDER BY is_pinned DESC, modified_at DESC"
            
            results = self.db.query_all(query)
            notes = []
            
            for row in results:
                note_dict = dict(row)
                # Decrypt only title for list view (performance)
                note_dict['title'] = self.encryption.decrypt(note_dict['title'])
                # Don't decrypt content for preview
                note_dict['content'] = ""
                notes.append(Note.from_dict(note_dict))
            
            logger.info(f"Retrieved {len(notes)} notes")
            return notes
        
        except Exception as e:
            logger.error(f"Failed to get all notes: {e}")
            return []
    
    def get_notes_by_notebook(self, notebook_id: str) -> List[Note]:
        """Get all notes in a specific notebook."""
        try:
            results = self.db.query_all("""
                SELECT * FROM notes 
                WHERE notebook_id = ? AND is_trashed = 0
                ORDER BY is_pinned DESC, modified_at DESC
            """, (notebook_id,))
            
            notes = []
            for row in results:
                note_dict = dict(row)
                note_dict['title'] = self.encryption.decrypt(note_dict['title'])
                note_dict['content'] = ""
                notes.append(Note.from_dict(note_dict))
            
            return notes
        
        except Exception as e:
            logger.error(f"Failed to get notes for notebook {notebook_id}: {e}")
            return []
    
    def get_favorite_notes(self) -> List[Note]:
        """Get all favorited notes."""
        try:
            results = self.db.query_all("""
                SELECT * FROM notes 
                WHERE is_favorite = 1 AND is_trashed = 0
                ORDER BY modified_at DESC
            """)
            
            notes = []
            for row in results:
                note_dict = dict(row)
                note_dict['title'] = self.encryption.decrypt(note_dict['title'])
                note_dict['content'] = ""
                notes.append(Note.from_dict(note_dict))
            
            return notes
        
        except Exception as e:
            logger.error(f"Failed to get favorite notes: {e}")
            return []
    
    def get_trashed_notes(self) -> List[Note]:
        """Get all trashed notes."""
        try:
            results = self.db.query_all("""
                SELECT * FROM notes 
                WHERE is_trashed = 1
                ORDER BY modified_at DESC
            """)
            
            notes = []
            for row in results:
                note_dict = dict(row)
                note_dict['title'] = self.encryption.decrypt(note_dict['title'])
                note_dict['content'] = ""
                notes.append(Note.from_dict(note_dict))
            
            return notes
        
        except Exception as e:
            logger.error(f"Failed to get trashed notes: {e}")
            return []
    
    def toggle_favorite(self, note_id: str) -> bool:
        """Toggle favorite status of a note."""
        try:
            note = self.get_note(note_id)
            if note:
                note.is_favorite = not note.is_favorite
                return self.update_note(note)
            return False
        
        except Exception as e:
            logger.error(f"Failed to toggle favorite for {note_id}: {e}")
            return False
    
    def toggle_pin(self, note_id: str) -> bool:
        """Toggle pin status of a note."""
        try:
            note = self.get_note(note_id)
            if note:
                note.is_pinned = not note.is_pinned
                return self.update_note(note)
            return False
        
        except Exception as e:
            logger.error(f"Failed to toggle pin for {note_id}: {e}")
            return False
    
    def toggle_archive(self, note_id: str) -> bool:
        """Toggle archive status of a note."""
        try:
            note = self.get_note(note_id)
            if note:
                note.is_archived = not note.is_archived
                return self.update_note(note)
            return False
        
        except Exception as e:
            logger.error(f"Failed to toggle archive for {note_id}: {e}")
            return False
    
    def search_notes(self, query: str) -> List[Note]:
        """
        Search notes by title and content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching notes
        """
        try:
            all_notes = self.get_all_notes()
            matching_notes = []
            
            query_lower = query.lower()
            
            for note in all_notes:
                # Get full note with content
                full_note = self.get_note(note.id)
                if full_note:
                    # Search in title and content
                    if (query_lower in full_note.title.lower() or 
                        query_lower in full_note.content.lower()):
                        matching_notes.append(full_note)
            
            logger.info(f"Search '{query}' found {len(matching_notes)} results")
            return matching_notes
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_note_count(self) -> int:
        """Get total note count (excluding trash)."""
        try:
            result = self.db.query_one("""
                SELECT COUNT(*) as count FROM notes WHERE is_trashed = 0
            """)
            return result['count'] if result else 0
        
        except Exception as e:
            logger.error(f"Failed to get note count: {e}")
            return 0
    
    def empty_trash(self) -> bool:
        """Permanently delete all trashed notes."""
        try:
            self.db.execute("DELETE FROM notes WHERE is_trashed = 1")
            logger.info("Emptied trash")
            return True
        
        except Exception as e:
            logger.error(f"Failed to empty trash: {e}")
            return False