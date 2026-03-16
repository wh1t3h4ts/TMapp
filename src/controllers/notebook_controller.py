"""Complete notebook controller."""
import logging
from typing import List, Optional
from datetime import datetime

from src.models.notebook import Notebook
from src.core.database import Database

logger = logging.getLogger(__name__)


class NotebookController:
    """Controller for notebook/folder operations."""
    
    def __init__(self, database: Database):
        self.db = database
        logger.info("NotebookController initialized")
        self._ensure_default_notebook()
    
    def _ensure_default_notebook(self):
        """Ensure a default notebook exists."""
        result = self.db.query_one("""
            SELECT * FROM notebooks WHERE is_default = 1
        """)
        
        if not result:
            # Create default notebook
            default = Notebook.create_new("My Notes")
            default.is_default = True
            self.create_notebook(default)
            logger.info("Created default notebook")
    
    def create_notebook(self, notebook: Notebook = None, name: str = None, 
                       parent_id: Optional[str] = None) -> Notebook:
        """
        Create a new notebook.
        
        Args:
            notebook: Notebook object (if provided, use it)
            name: Notebook name (if notebook not provided)
            parent_id: Parent notebook ID for nesting
            
        Returns:
            Created Notebook object
        """
        try:
            if notebook is None:
                if name is None:
                    name = "New Notebook"
                notebook = Notebook.create_new(name, parent_id)
            
            data = notebook.to_dict()
            
            self.db.execute("""
                INSERT INTO notebooks (
                    id, name, parent_id, color, icon, created_at, modified_at,
                    note_count, is_default, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['id'], data['name'], data['parent_id'], data['color'], data['icon'],
                data['created_at'], data['modified_at'], data['note_count'],
                data['is_default'], data['sort_order']
            ))
            
            logger.info(f"Created notebook: {notebook.id} - {notebook.name}")
            return notebook
        
        except Exception as e:
            logger.error(f"Failed to create notebook: {e}")
            raise
    
    def get_notebook(self, notebook_id: str) -> Optional[Notebook]:
        """Get notebook by ID."""
        try:
            result = self.db.query_one("""
                SELECT * FROM notebooks WHERE id = ?
            """, (notebook_id,))
            
            if result:
                return Notebook.from_dict(dict(result))
            return None
        
        except Exception as e:
            logger.error(f"Failed to get notebook {notebook_id}: {e}")
            return None
    
    def get_all_notebooks(self) -> List[Notebook]:
        """Get all notebooks ordered by sort_order."""
        try:
            results = self.db.query_all("""
                SELECT * FROM notebooks ORDER BY sort_order, name
            """)
            
            notebooks = [Notebook.from_dict(dict(row)) for row in results]
            
            # Update note counts
            for notebook in notebooks:
                count_result = self.db.query_one("""
                    SELECT COUNT(*) as count FROM notes 
                    WHERE notebook_id = ? AND is_trashed = 0
                """, (notebook.id,))
                notebook.note_count = count_result['count'] if count_result else 0
            
            return notebooks
        
        except Exception as e:
            logger.error(f"Failed to get all notebooks: {e}")
            return []
    
    def get_default_notebook(self) -> Optional[Notebook]:
        """Get the default notebook."""
        try:
            result = self.db.query_one("""
                SELECT * FROM notebooks WHERE is_default = 1
            """)
            
            if result:
                return Notebook.from_dict(dict(result))
            return None
        
        except Exception as e:
            logger.error(f"Failed to get default notebook: {e}")
            return None
    
    def update_notebook(self, notebook: Notebook) -> bool:
        """Update a notebook."""
        try:
            notebook.modified_at = datetime.now()
            data = notebook.to_dict()
            
            self.db.execute("""
                UPDATE notebooks SET
                    name = ?, parent_id = ?, color = ?, icon = ?, modified_at = ?,
                    note_count = ?, is_default = ?, sort_order = ?
                WHERE id = ?
            """, (
                data['name'], data['parent_id'], data['color'], data['icon'],
                data['modified_at'], data['note_count'], data['is_default'],
                data['sort_order'], data['id']
            ))
            
            logger.info(f"Updated notebook: {notebook.id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update notebook {notebook.id}: {e}")
            return False
    
    def delete_notebook(self, notebook_id: str, move_notes_to: Optional[str] = None) -> bool:
        """
        Delete a notebook.
        
        Args:
            notebook_id: Notebook ID to delete
            move_notes_to: If provided, move notes to this notebook; otherwise delete notes
            
        Returns:
            Success status
        """
        try:
            # Prevent deleting default notebook
            notebook = self.get_notebook(notebook_id)
            if notebook and notebook.is_default:
                logger.warning("Cannot delete default notebook")
                return False
            
            if move_notes_to:
                # Move notes to another notebook
                self.db.execute("""
                    UPDATE notes SET notebook_id = ? WHERE notebook_id = ?
                """, (move_notes_to, notebook_id))
            else:
                # Delete all notes in notebook (soft delete to trash)
                self.db.execute("""
                    UPDATE notes SET is_trashed = 1 WHERE notebook_id = ?
                """, (notebook_id,))
            
            # Delete notebook
            self.db.execute("DELETE FROM notebooks WHERE id = ?", (notebook_id,))
            
            logger.info(f"Deleted notebook: {notebook_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete notebook {notebook_id}: {e}")
            return False
    
    def rename_notebook(self, notebook_id: str, new_name: str) -> bool:
        """Rename a notebook."""
        try:
            notebook = self.get_notebook(notebook_id)
            if notebook:
                notebook.name = new_name
                return self.update_notebook(notebook)
            return False
        
        except Exception as e:
            logger.error(f"Failed to rename notebook {notebook_id}: {e}")
            return False
    
    def set_default_notebook(self, notebook_id: str) -> bool:
        """Set a notebook as default."""
        try:
            # Clear existing default
            notebooks = self.get_all_notebooks()
            for nb in notebooks:
                if nb.is_default:
                    nb.is_default = False
                    self.update_notebook(nb)
            
            # Set new default
            notebook = self.get_notebook(notebook_id)
            if notebook:
                notebook.is_default = True
                return self.update_notebook(notebook)
            return False
        
        except Exception as e:
            logger.error(f"Failed to set default notebook: {e}")
            return False