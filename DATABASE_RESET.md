# Database Reset Utilities

If you're experiencing encryption/decryption errors with existing notes, you can reset the database to start fresh.

## Option 1: Use the Batch File (Easiest - Windows)

1. Close the TMapp application
2. Double-click `reset_db.bat`
3. Follow the prompts
4. Restart the application

## Option 2: Use Python Script

1. Close the TMapp application
2. Open terminal/command prompt in the TMapp directory
3. Run: `python delete_database.py`
4. Type `DELETE` when prompted
5. Restart the application

## Option 3: Use the Application Menu

1. Open TMapp
2. Go to **File → Clear All Notes...**
3. Confirm the action by typing `DELETE ALL`
4. The database will be cleared while the app is running

## Option 4: Manual Deletion

1. Close the TMapp application
2. Navigate to: `C:\Users\YOUR_USERNAME\.tmapp\`
3. Delete the file: `notes.db`
4. Restart the application

## What Happens After Reset?

- All notes will be permanently deleted
- The database will be recreated on next launch
- All new notes will be encrypted with the correct salt
- No more encryption/decryption errors

## Important Notes

⚠️ **WARNING**: All these methods permanently delete your notes. There is no undo!

✅ **Recommendation**: If you have important notes, export them before resetting.

## Why This Is Needed

The encryption error occurs when notes were created with different encryption salts. This happens during development/testing. Resetting ensures all new notes use the same salt from your master password.
