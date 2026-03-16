"""Advanced search functionality for notes."""
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AdvancedSearch:
    """Advanced search with filters and operators."""
    
    def __init__(self, note_controller):
        self.note_controller = note_controller
    
    def search(self, query, filters=None):
        """Search notes with advanced filters."""
        try:
            all_notes = self.note_controller.get_all_notes()
            results = []
            
            for note in all_notes:
                if self._matches_query(note, query) and self._matches_filters(note, filters or {}):
                    results.append(note)
            
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _matches_query(self, note, query):
        """Check if note matches search query."""
        if not query:
            return True
        
        query_lower = query.lower()
        title_match = query_lower in note.title.lower()
        content_match = query_lower in note.get_plain_text().lower()
        
        return title_match or content_match
    
    def _matches_filters(self, note, filters):
        """Check if note matches all filters."""
        if filters.get('is_favorite') and not note.is_favorite:
            return False
        
        if filters.get('notebook_id') and note.notebook_id != filters['notebook_id']:
            return False
        
        if filters.get('date_from'):
            if note.created_at < filters['date_from']:
                return False
        
        if filters.get('date_to'):
            if note.created_at > filters['date_to']:
                return False
        
        if filters.get('tags'):
            note_tags = set(note.tags) if note.tags else set()
            filter_tags = set(filters['tags'])
            if not filter_tags.issubset(note_tags):
                return False
        
        return True
    
    def search_by_date_range(self, days_ago):
        """Search notes created within the last N days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_ago)
            all_notes = self.note_controller.get_all_notes()
            
            return [note for note in all_notes if note.created_at >= cutoff_date]
        except Exception as e:
            logger.error(f"Date range search failed: {e}")
            return []
    
    def search_by_word_count(self, min_words=None, max_words=None):
        """Search notes by word count range."""
        try:
            all_notes = self.note_controller.get_all_notes()
            results = []
            
            for note in all_notes:
                word_count = len(note.get_plain_text().split())
                
                if min_words and word_count < min_words:
                    continue
                if max_words and word_count > max_words:
                    continue
                
                results.append(note)
            
            return results
        except Exception as e:
            logger.error(f"Word count search failed: {e}")
            return []
