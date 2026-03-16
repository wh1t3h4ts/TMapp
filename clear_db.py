import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.core.config import AppConfig

config = AppConfig()
db_file = config.db_file

if db_file.exists():
    db_file.unlink()
    print(f"Deleted: {db_file}")
else:
    print("Database does not exist")
