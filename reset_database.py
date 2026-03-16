#!/usr/bin/env python3
"""Database reset utility - clears all notes and resets the database."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import AppConfig
from src.core.database import Database

def reset_database():
    """Clear all notes from the database."""
    print("=" * 60)
    print("TMapp Database Reset Utility")
    print("=" * 60)
    print()
    
    # Initialize config
    config = AppConfig()
    db_file = config.db_file
    
    print(f"Database location: {db_file}")
    print()
    
    # Confirm action
    response = input("WARNING: This will DELETE ALL NOTES permanently!\nType 'YES' to confirm: ")
    
    if response != "YES":
        print("❌ Reset cancelled.")
        return
    
    print()
    print("Resetting database...")
    
    try:
        # Initialize database connection
        db = Database(db_file)
        
        # Delete all notes
        result = db.execute("DELETE FROM notes")
        print(f"✓ Deleted all notes from database")
        
        # Delete all notebooks except default
        db.execute("DELETE FROM notebooks WHERE is_default = 0")
        print(f"✓ Deleted all custom notebooks")
        
        # Reset default notebook
        db.execute("UPDATE notebooks SET note_count = 0 WHERE is_default = 1")
        print(f"✓ Reset default notebook")
        
        # Vacuum database to reclaim space
        db.execute("VACUUM")
        print(f"✓ Optimized database")
        
        db.close()
        
        print()
        print("=" * 60)
        print("✅ Database reset complete!")
        print("=" * 60)
        print()
        print("You can now start the application with a clean database.")
        print("All new notes will be encrypted with the correct salt.")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_database()
