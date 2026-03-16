"""Notebook model for organizing notes."""
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Notebook:
    """Notebook for organizing notes hierarchically."""
    id: str
    name: str
    parent_id: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    created_at: datetime
    modified_at: datetime
    note_count: int
    is_default: bool
    sort_order: int
    
    @staticmethod
    def create_new(name: str, parent_id: Optional[str] = None) -> 'Notebook':
        """Create a new notebook with default values."""
        now = datetime.now()
        return Notebook(
            id=str(uuid.uuid4()),
            name=name,
            parent_id=parent_id,
            color=None,
            icon="📓",
            created_at=now,
            modified_at=now,
            note_count=0,
            is_default=False,
            sort_order=0
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'note_count': self.note_count,
            'is_default': int(self.is_default),
            'sort_order': self.sort_order
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Notebook':
        """Create notebook from dictionary."""
        return Notebook(
            id=data['id'],
            name=data['name'],
            parent_id=data.get('parent_id'),
            color=data.get('color'),
            icon=data.get('icon', "📓"),
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at']),
            note_count=data.get('note_count', 0),
            is_default=bool(data.get('is_default', 0)),
            sort_order=data.get('sort_number', 0)
        )