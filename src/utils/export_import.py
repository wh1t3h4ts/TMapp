"""Export and import functionality for notes."""
import json
import logging
from pathlib import Path
from datetime import datetime
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter

logger = logging.getLogger(__name__)


class ExportImportManager:
    """Manage note export and import operations."""
    
    def __init__(self, note_controller, encryption_service):
        self.note_controller = note_controller
        self.encryption_service = encryption_service
    
    def export_notes_to_json(self, notes, output_path):
        """Export notes to JSON format."""
        try:
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "notes": []
            }
            for note in notes:
                export_data["notes"].append({
                    "id": note.id,
                    "title": note.title,
                    "content": note.get_plain_text(),
                    "created_at": str(note.created_at),
                    "modified_at": str(note.modified_at),
                    "tags": note.tags,
                    "is_favorite": note.is_favorite,
                    "is_pinned": note.is_pinned,
                })
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(notes)} notes to JSON")
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def export_to_markdown(self, notes, output_dir):
        """Export notes as individual markdown files."""
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            for note in notes:
                safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in note.title).strip()
                file_path = output_dir / f"{safe_name or 'Untitled'}.md"
                content = f"# {note.title}\n\n{note.get_plain_text()}"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            logger.info(f"Exported {len(notes)} notes to Markdown")
            return True
        except Exception as e:
            logger.error(f"Markdown export failed: {e}")
            return False

    def export_to_pdf(self, notes, output_path):
        """Export all notes as a single PDF file."""
        try:
            from PyQt6.QtCore import QSizeF
            from PyQt6.QtGui import QFont, QPageSize

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(str(output_path))
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

            # A4 printable area in points (595 x 842 pt minus ~72 pt margins)
            page_width_pt  = 451.0
            page_height_pt = 698.0

            html_parts = [
                """<html><head><style>
                body { font-family: Calibri, Arial, sans-serif; font-size: 12pt;
                       color: #1a1a1a; line-height: 1.6; }
                h2   { font-size: 16pt; font-weight: bold; color: #1e3a5f;
                       border-bottom: 1px solid #cccccc; padding-bottom: 4px;
                       margin: 0 0 4px 0; }
                .meta { font-size: 10pt; color: #666666; margin: 0 0 14px 0; }
                hr   { border: none; border-top: 1px solid #dddddd; margin: 28px 0; }
                p    { margin: 0 0 8px 0; font-size: 12pt; }
                li   { font-size: 12pt; }
                </style></head><body>"""
            ]

            for i, note in enumerate(notes):
                if i:
                    html_parts.append("<hr>")
                try:
                    date_str = note.modified_at.strftime("%B %d, %Y  %H:%M")
                except Exception:
                    date_str = ""
                body = note.content if note.content and note.content.strip() \
                       else f"<p>{note.get_plain_text()}</p>"
                html_parts.append(
                    f"<h2>{note.title or 'Untitled'}</h2>"
                    f"<p class='meta'>{date_str}</p>"
                    f"<div>{body}</div>"
                )

            html_parts.append("</body></html>")

            doc = QTextDocument()
            doc.setDefaultFont(QFont("Calibri", 12))
            doc.setPageSize(QSizeF(page_width_pt, page_height_pt))
            doc.setHtml("".join(html_parts))
            doc.print(printer)
            logger.info(f"Exported {len(notes)} notes to PDF")
            return True
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return False

    def export_to_text(self, notes, output_path):
        """Export all notes as a single plain text file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, note in enumerate(notes):
                    if i:
                        f.write("\n" + "─" * 60 + "\n\n")
                    f.write(f"{note.title}\n")
                    f.write(f"Modified: {note.modified_at.strftime('%Y-%m-%d %H:%M')}\n\n")
                    f.write(note.get_plain_text())
                    f.write("\n")
            logger.info(f"Exported {len(notes)} notes to plain text")
            return True
        except Exception as e:
            logger.error(f"Text export failed: {e}")
            return False

    # ── Import ────────────────────────────────────────────────────────────────

    def import_from_json(self, path: str) -> tuple[int, str]:
        """Import notes from a TMapp JSON export. Returns (count, error)."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            notes_data = data.get("notes", [])
            if not isinstance(notes_data, list):
                return 0, "Invalid JSON format."
            count = 0
            for n in notes_data:
                title = n.get("title") or "Untitled"
                content = n.get("content") or ""
                note = self.note_controller.create_note(title=title, content=content)
                if note:
                    count += 1
            logger.info(f"Imported {count} notes from JSON")
            return count, ""
        except Exception as e:
            logger.error(f"JSON import failed: {e}")
            return 0, str(e)

    def import_from_markdown(self, paths: list[str]) -> tuple[int, str]:
        """Import one or more .md files as individual notes."""
        count = 0
        try:
            for path in paths:
                p = Path(path)
                raw = p.read_text(encoding='utf-8')
                # First line starting with # becomes the title
                lines = raw.splitlines()
                if lines and lines[0].startswith("#"):
                    title = lines[0].lstrip("# ").strip()
                    content = "\n".join(lines[1:]).strip()
                else:
                    title = p.stem
                    content = raw
                note = self.note_controller.create_note(title=title, content=content)
                if note:
                    count += 1
            logger.info(f"Imported {count} markdown files")
            return count, ""
        except Exception as e:
            logger.error(f"Markdown import failed: {e}")
            return count, str(e)

    def import_from_text(self, paths: list[str]) -> tuple[int, str]:
        """Import one or more plain text files as individual notes."""
        count = 0
        try:
            for path in paths:
                p = Path(path)
                content = p.read_text(encoding='utf-8')
                note = self.note_controller.create_note(title=p.stem, content=content)
                if note:
                    count += 1
            logger.info(f"Imported {count} text files")
            return count, ""
        except Exception as e:
            logger.error(f"Text import failed: {e}")
            return count, str(e)
