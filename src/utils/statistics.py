"""Note statistics and analytics."""
import logging
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)


class NoteStatistics:
    """Generate statistics and analytics for notes."""
    
    def __init__(self, note_controller):
        self.note_controller = note_controller
    
    def get_overview(self):
        """Get overview statistics."""
        try:
            all_notes = self.note_controller.get_all_notes()
            
            total_notes = len(all_notes)
            total_words = sum(len(note.get_plain_text().split()) for note in all_notes)
            total_chars = sum(len(note.get_plain_text()) for note in all_notes)
            
            favorites = sum(1 for note in all_notes if note.is_favorite)
            
            return {
                'total_notes': total_notes,
                'total_words': total_words,
                'total_characters': total_chars,
                'average_words_per_note': total_words // total_notes if total_notes > 0 else 0,
                'favorite_notes': favorites
            }
        except Exception as e:
            logger.error(f"Failed to get overview: {e}")
            return {}
    
    def get_activity_stats(self, days=30):
        """Get activity statistics for the last N days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            all_notes = self.note_controller.get_all_notes()
            
            recent_notes = [note for note in all_notes if note.created_at >= cutoff_date]
            
            notes_by_day = Counter()
            for note in recent_notes:
                day = note.created_at.date()
                notes_by_day[day] += 1
            
            return {
                'notes_created': len(recent_notes),
                'notes_by_day': dict(notes_by_day),
                'average_per_day': len(recent_notes) / days if days > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get activity stats: {e}")
            return {}
    
    def get_top_notebooks(self, limit=5):
        """Get notebooks with most notes."""
        try:
            all_notes = self.note_controller.get_all_notes()
            
            notebook_counts = Counter()
            for note in all_notes:
                if note.notebook_id:
                    notebook_counts[note.notebook_id] += 1
            
            return notebook_counts.most_common(limit)
        except Exception as e:
            logger.error(f"Failed to get top notebooks: {e}")
            return []
    
    def get_longest_notes(self, limit=10):
        """Get notes with most words."""
        try:
            all_notes = self.note_controller.get_all_notes()
            
            notes_with_counts = [(note, len(note.get_plain_text().split())) for note in all_notes]
            notes_with_counts.sort(key=lambda x: x[1], reverse=True)
            
            return notes_with_counts[:limit]
        except Exception as e:
            logger.error(f"Failed to get longest notes: {e}")
            return []
