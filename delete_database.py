#!/usr/bin/env python3
"""Complete database deletion - removes database file for fresh start."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import AppConfig

def delete_database():
    """Delete the entire database file."""
    print("=" * 60)
    print("TMapp Complete Database Deletion")
    print("=" * 60)
    print()
    
    # Initialize config
    config = AppConfig()
    db_file = config.db_file
    
    print(f"Database location: {db_file}")
    print()
    
    if not db_file.exists():
        print("✓ Database file does not exist. Nothing to delete.")
        return
    
    # Confirm action
    response = input("WARNING: This will DELETE THE ENTIRE DATABASE!\nAll notes will be permanently lost!\nType 'DELETE' to confirm: ")
    
    if response != "DELETE":
        print("❌ Deletion cancelled.")
        return
    
    print()
    print("Deleting database file...")
    
    try:
        # Delete the database file
        db_file.unlink()
        print(f"✓ Deleted database file: {db_file}")
        
        # Also delete any backup files
        backup_pattern = f"{db_file.stem}*.db"
        for backup_file in db_file.parent.glob(backup_pattern):
            if backup_file != db_file:
                backup_file.unlink()
                print(f"✓ Deleted backup: {backup_file.name}")
        
        print()
        print("=" * 60)
        print("✅ Database deletion complete!")
        print("=" * 60)
        print()
        print("The application will create a fresh database on next launch.")
        print("All new notes will be encrypted correctly.")
        
    except Exception as e:
        print(f"❌ Error deleting database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    delete_database()
