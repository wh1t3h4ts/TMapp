"""Remove duplicate _apply_app_mode definitions, keep only one clean version."""
import re

path = r'src\ui\main_window.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

print("Before:", content.count('def _apply_app_mode'), "occurrences")

# The clean single definition we want
CLEAN = '''    def _apply_app_mode(self):
        """Show/hide panels based on the configured app mode."""
        mode = self.config.get("app_mode", "both")
        notes_on     = mode in ("notes", "both")
        passwords_on = mode in ("passwords", "both")

        if hasattr(self, 'vault_btn'):
            self.vault_btn.setVisible(passwords_on)

        if not notes_on:
            self.left_panel.setVisible(False)
            self.editor_panel.setVisible(False)
            self._toggle_vault_popup()

        if not passwords_on:
            for action in self.menuBar().actions():
                if action.text() == "Edit":
                    for a in action.menu().actions():
                        if "Credential" in a.text():
                            a.setVisible(False)

        import logging
        logging.getLogger(__name__).info(f"App mode applied: {mode}")

'''

# Remove ALL existing _apply_app_mode definitions using regex
# Match from "    def _apply_app_mode" up to the next "    def " at same indent
pattern = r'    def _apply_app_mode\(self\):.*?(?=\n    def |\Z)'
cleaned = re.sub(pattern, '', content, flags=re.DOTALL)

print("After removal:", cleaned.count('def _apply_app_mode'), "occurrences")

# Insert the clean version before _load_data
cleaned = cleaned.replace('    def _load_data(self):', CLEAN + '    def _load_data(self):', 1)

print("After insert:", cleaned.count('def _apply_app_mode'), "occurrences")

with open(path, 'w', encoding='utf-8') as f:
    f.write(cleaned)

print("Done.")
