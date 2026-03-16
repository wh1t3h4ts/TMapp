"""Enhanced database with complete schema and query methods."""
import sqlite3
import logging
from pathlib import Path
from typing import List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager with complete schema."""
    
    def __init__(self, db_path: Path):
        """Initialize database connection."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self.connect()
        self.initialize_schema()
        logger.info(f"Database initialized: {self.db_path}")
    
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            logger.debug("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def initialize_schema(self):
        """Create all required tables."""
        cursor = self.connection.cursor()
        
        try:
            # Check if schema needs migration
            needs_migration = self._check_schema_migration()
            
            if needs_migration:
                logger.info("Schema migration needed, recreating tables...")
                self._drop_old_schema()
            
            # Notes table with all fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    notebook_id TEXT,
                    tags TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    is_favorite INTEGER DEFAULT 0,
                    is_pinned INTEGER DEFAULT 0,
                    is_archived INTEGER DEFAULT 0,
                    is_trashed INTEGER DEFAULT 0,
                    color TEXT,
                    attachments TEXT DEFAULT '',
                    images TEXT DEFAULT '',
                    links TEXT DEFAULT '',
                    has_tasks INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    total_tasks INTEGER DEFAULT 0,
                    word_count INTEGER DEFAULT 0,
                    character_count INTEGER DEFAULT 0,
                    reading_time INTEGER DEFAULT 0,
                    encrypted INTEGER DEFAULT 1,
                    encryption_version TEXT DEFAULT '1.0',
                    FOREIGN KEY (notebook_id) REFERENCES notebooks(id)
                )
            """)
            
            # Notebooks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notebooks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent_id TEXT,
                    color TEXT,
                    icon TEXT DEFAULT '📓',
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    note_count INTEGER DEFAULT 0,
                    is_default INTEGER DEFAULT 0,
                    sort_order INTEGER DEFAULT 0,
                    FOREIGN KEY (parent_id) REFERENCES notebooks(id)
                )
            """)
            
            # Tags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT,
                    created_at TEXT NOT NULL,
                    note_count INTEGER DEFAULT 0
                )
            """)
            
            # Attachments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attachments (
                    id TEXT PRIMARY KEY,
                    note_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    mime_type TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notes_notebook 
                ON notes(notebook_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notes_modified 
                ON notes(modified_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notes_favorite 
                ON notes(is_favorite)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notes_trashed 
                ON notes(is_trashed)
            """)
            
            self.connection.commit()
            logger.debug("Database schema initialized")
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            self.connection.rollback()
            raise
    
    def _check_schema_migration(self) -> bool:
        """Check if schema needs migration."""
        try:
            # Check if notes table exists and has the correct columns
            result = self.query_one("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='notes'
            """)
            
            if result:
                # Check if modified_at column exists
                cursor = self.connection.cursor()
                cursor.execute("PRAGMA table_info(notes)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # If modified_at doesn't exist, we need migration
                if 'modified_at' not in columns:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Schema check failed: {e}")
            return False
    
    def _drop_old_schema(self):
        """Drop old schema tables."""
        try:
            cursor = self.connection.cursor()
            
            # Disable foreign keys temporarily
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Drop old tables
            cursor.execute("DROP TABLE IF EXISTS notes")
            cursor.execute("DROP TABLE IF EXISTS notebooks")
            cursor.execute("DROP TABLE IF EXISTS tags")
            cursor.execute("DROP TABLE IF EXISTS attachments")
            
            # Drop old indexes
            cursor.execute("DROP INDEX IF EXISTS idx_notes_notebook")
            cursor.execute("DROP INDEX IF EXISTS idx_notes_modified")
            cursor.execute("DROP INDEX IF EXISTS idx_notes_favorite")
            cursor.execute("DROP INDEX IF EXISTS idx_notes_trashed")
            
            self.connection.commit()
            
            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            logger.info("Old schema dropped successfully")
            
        except Exception as e:
            logger.error(f"Failed to drop old schema: {e}")
            self.connection.rollback()
            raise
    
    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        Execute a query (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Cursor object
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}\nParams: {params}")
            self.connection.rollback()
            raise
    
    def query_one(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """
        Execute query and return one result.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Single row or None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Query failed: {e}\nQuery: {query}\nParams: {params}")
            return None
    
    def query_all(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        Execute query and return all results.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of rows
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query failed: {e}\nQuery: {query}\nParams: {params}")
            return []
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """
        Execute the same query multiple times with different parameters.
        
        Args:
            query: SQL query
            params_list: List of parameter tuples
            
        Returns:
            Success status
        """
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            self.connection.rollback()
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        result = self.query_one("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return result is not None
    
    def get_table_info(self, table_name: str) -> List[sqlite3.Row]:
        """Get table schema information."""
        return self.query_all(f"PRAGMA table_info({table_name})")
    
    def vacuum(self):
        """Optimize database (reclaim space)."""
        try:
            self.connection.execute("VACUUM")
            logger.info("Database vacuumed")
        except Exception as e:
            logger.error(f"Vacuum failed: {e}")
    
    def backup(self, backup_path: Path) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Success status
        """
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup connection
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Copy database
            with backup_conn:
                self.connection.backup(backup_conn)
            
            backup_conn.close()
            logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def restore(self, backup_path: Path) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Success status
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Close current connection
            self.close()
            
            # Replace database file
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            # Reconnect
            self.connect()
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        try:
            stats = {}
            
            # Note counts
            result = self.query_one("SELECT COUNT(*) as count FROM notes WHERE is_trashed = 0")
            stats['total_notes'] = result['count'] if result else 0
            
            result = self.query_one("SELECT COUNT(*) as count FROM notes WHERE is_favorite = 1")
            stats['favorite_notes'] = result['count'] if result else 0
            
            result = self.query_one("SELECT COUNT(*) as count FROM notes WHERE is_trashed = 1")
            stats['trashed_notes'] = result['count'] if result else 0
            
            # Notebook count
            result = self.query_one("SELECT COUNT(*) as count FROM notebooks")
            stats['total_notebooks'] = result['count'] if result else 0
            
            # Tag count
            result = self.query_one("SELECT COUNT(*) as count FROM tags")
            stats['total_tags'] = result['count'] if result else 0
            
            # Database size
            import os
            if self.db_path.exists():
                stats['db_size_bytes'] = os.path.getsize(self.db_path)
                stats['db_size_mb'] = stats['db_size_bytes'] / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.debug("Database connection closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()