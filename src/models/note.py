"""Complete note data model."""
import uuid
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Note:
    """Complete note data model with all fields."""
    
    id: str
    title: str
    content: str
    notebook_id: Optional[str]
    tags: List[str]
    created_at: datetime
    modified_at: datetime
    is_favorite: bool
    is_pinned: bool
    is_archived: bool
    is_trashed: bool
    color: Optional[str]
    
    # Rich content
    attachments: List[str]
    images: List[str]
    links: List[str]
    
    # Task management
    has_tasks: bool
    completed_tasks: int
    total_tasks: int
    
    # Metadata
    word_count: int
    character_count: int
    reading_time: int
    
    # Encryption metadata
    encrypted: bool
    encryption_version: str
    
    @staticmethod
    def create_new(title: str = "Untitled Note", notebook_id: Optional[str] = None) -> 'Note':
        """Create a new note with default values."""
        now = datetime.now()
        return Note(
            id=str(uuid.uuid4()),
            title=title,
            content="",
            notebook_id=notebook_id,
            tags=[],
            created_at=now,
            modified_at=now,
            is_favorite=False,
            is_pinned=False,
            is_archived=False,
            is_trashed=False,
            color=None,
            attachments=[],
            images=[],
            links=[],
            has_tasks=False,
            completed_tasks=0,
            total_tasks=0,
            word_count=0,
            character_count=0,
            reading_time=0,
            encrypted=True,
            encryption_version="1.0"
        )
    
    def update_metadata(self, content: str):
        """Update metadata based on content."""
        self.word_count = len(content.split())
        self.character_count = len(content)
        self.reading_time = max(1, self.word_count // 200)  # Average reading speed
        self.modified_at = datetime.now()
        
        # Detect tasks
        task_pattern = r'\[ \]|\[x\]|\[X\]'
        tasks = re.findall(task_pattern, content)
        self.total_tasks = len(tasks)
        self.completed_tasks = len([t for t in tasks if t.lower() == '[x]'])
        self.has_tasks = self.total_tasks > 0
    
<<<<<<< HEAD
    def get_plain_text(self) -> str:
        """Get plain text content."""
        return self.content
    
=======
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'notebook_id': self.notebook_id,
            'tags': ','.join(self.tags),
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'is_favorite': int(self.is_favorite),
            'is_pinned': int(self.is_pinned),
            'is_archived': int(self.is_archived),
            'is_trashed': int(self.is_trashed),
            'color': self.color,
            'attachments': ','.join(self.attachments),
            'images': ','.join(self.images),
            'links': ','.join(self.links),
            'has_tasks': int(self.has_tasks),
            'completed_tasks': self.completed_tasks,
            'total_tasks': self.total_tasks,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'reading_time': self.reading_time,
            'encrypted': int(self.encrypted),
            'encryption_version': self.encryption_version
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Note':
        """Create Note from dictionary."""
        return Note(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            notebook_id=data.get('notebook_id'),
            tags=data.get('tags', '').split(',') if data.get('tags') else [],
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at']),
            is_favorite=bool(data.get('is_favorite', 0)),
            is_pinned=bool(data.get('is_pinned', 0)),
            is_archived=bool(data.get('is_archived', 0)),
            is_trashed=bool(data.get('is_trashed', 0)),
            color=data.get('color'),
            attachments=data.get('attachments', '').split(',') if data.get('attachments') else [],
            images=data.get('images', '').split(',') if data.get('images') else [],
            links=data.get('links', '').split(',') if data.get('links') else [],
            has_tasks=bool(data.get('has_tasks', 0)),
            completed_tasks=data.get('completed_tasks', 0),
            total_tasks=data.get('total_tasks', 0),
            word_count=data.get('word_count', 0),
            character_count=data.get('character_count', 0),
            reading_time=data.get('reading_time', 0),
            encrypted=bool(data.get('encrypted', 1)),
            encryption_version=data.get('encryption_version', '1.0')
        )