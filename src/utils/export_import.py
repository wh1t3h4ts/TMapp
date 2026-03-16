"""Export and import functionality for notes."""
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportImportManager:
    """Manage note export and import operations."""
    
    def __init__(self, note_controller, encryption_service):
        self.note_controller = note_controller
        self.encryption_service = encryption_service
    
    def export_notes_to_json(self, notes, output_path):
        """Export notes to JSON format."""
        try:
            export_data = {"version": "1.0", "exported_at": datetime.now().isoformat(), "notes": []}
            
            for note in notes:
                note_data = {"id": note.id, "title": note.title, "content": note.get_plain_text(), 
                            "created_at": str(note.created_at), "modified_at": str(note.updated_at)}
                export_data["notes"].append(note_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(notes)} notes")
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def export_to_markdown(self, notes, output_dir):
        """Export notes as markdown files."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for note in notes:
                filename = f"{note.title.replace('/', '-')}.md"
                file_path = output_dir / filename
                
                content = f"# {note.title}\n\n{note.get_plain_text()}"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            logger.info(f"Exported {len(notes)} notes to markdown")
            return True
        except Exception as e:
            logger.error(f"Markdown export failed: {e}")
            return False
