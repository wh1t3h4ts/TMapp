"""Main application entry point with authentication."""
import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.core.config import AppConfig
from src.core.encryption import EncryptionService
from src.core.database import Database
from src.core.auth_manager import AuthenticationManager
from src.controllers.note_controller import NoteController
from src.controllers.notebook_controller import NotebookController
from src.ui.first_run_wizard import FirstRunWizard
from src.ui.auth_dialog import AuthenticationDialog
from src.ui.main_window import MainWindow
from src.utils.backup_manager import BackupManager

logger = logging.getLogger(__name__)


class TMApp:
    """Main TMapp application with authentication."""
    
    def __init__(self):
        """Initialize the application."""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("TMapp")
        self.app.setOrganizationName("TMapp")
        _logo = os.path.join(os.path.dirname(__file__), 'logo.png')
        if os.path.exists(_logo):
            self.app.setWindowIcon(QIcon(_logo))
        
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        self.config = AppConfig()
        self.encryption_service = EncryptionService()
        self.database = Database(self.config.db_file)
        self.backup_manager = BackupManager(self.config)
        self.auth_manager = AuthenticationManager(self.config.app_dir)
        self.note_controller = NoteController(self.database, self.encryption_service)
        self.notebook_controller = NotebookController(self.database)
        
        self.main_window = None
        self.is_authenticated = False
        
        logger.info("TMapp initialized")
    
    def run(self):
        """Run the application with authentication flow."""
        try:
            if self.auth_manager.is_first_run():
                logger.info("First run detected, showing setup wizard")
                if not self._show_first_run_wizard():
                    logger.info("First-run wizard cancelled, exiting")
                    return 0
            
            logger.info("Showing authentication dialog")
            if not self._show_authentication_dialog():
                logger.info("Authentication cancelled, exiting")
                return 0
            
            if self.is_authenticated:
                logger.info("Authentication successful, showing main window")
                if self.config.get("auto_backup_enabled", True):
                    self.backup_manager.create_backup(self.config.db_file)
                self._show_main_window()
                return self.app.exec()
            else:
                return 0
        
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            QMessageBox.critical(None, "Application Error", f"An unexpected error occurred:\n{str(e)}")
            return 1
    
    def _show_first_run_wizard(self) -> bool:
        """Show the first-run setup wizard."""
        wizard = FirstRunWizard()

        captured = {"password": "", "mode": "both", "totp_secret": ""}

        def _on_completed(password: str, mode: str, totp_secret: str):
            captured["password"] = password
            captured["mode"] = mode
            captured["totp_secret"] = totp_secret

        wizard.wizard_completed.connect(_on_completed)

        if wizard.exec() == wizard.DialogCode.Accepted:
            password = captured["password"]
            mode     = captured["mode"]
            success, message = self.auth_manager.setup_master_password(
                password, totp_secret=captured["totp_secret"])

            if success:
                self.config.set("app_mode", mode)
                self.config.save()
                logger.info(f"Master password configured — mode: {mode}")
                mode_labels = {
                    "notes":     "Notes",
                    "passwords": "Password Manager",
                    "both":      "Notes + Password Manager",
                }
                QMessageBox.information(
                    None, "Setup Complete",
                    f"TMapp is ready!\n\n"
                    f"Mode: {mode_labels.get(mode, mode)}\n\n"
                    "⚠️ IMPORTANT: Store your master password safely.\n"
                    "Use your authenticator app to reset it if forgotten."
                )
                return True
            else:
                logger.error(f"Failed to setup password: {message}")
                QMessageBox.critical(None, "Setup Error", f"Failed to setup master password:\n{message}")
                return False

        return False
    
    def _show_authentication_dialog(self) -> bool:
        """Show authentication dialog and wait for success."""
        auth_dialog = AuthenticationDialog(self.auth_manager, app_mode=self.config.get("app_mode", "both"))
        
        def on_auth_success(encryption_key: bytes):
            self.is_authenticated = True
            self.encryption_service._cached_key = encryption_key
            self.encryption_service._cached_salt = self.auth_manager.get_stored_salt()
            self.encryption_service._cached_password = auth_dialog.entered_password
            logger.info("Encryption key cached for session")
        
        auth_dialog.authentication_successful.connect(on_auth_success)
        result = auth_dialog.exec()
        
        return result == auth_dialog.DialogCode.Accepted and self.is_authenticated
    
    def _show_main_window(self):
        """Show main application window after authentication."""
        mode = self.config.get("app_mode", "both")

        if mode == "passwords":
            from src.ui.credential_window import CredentialWindow
            from src.controllers.credential_controller import CredentialController
            cred_controller = CredentialController(self.database)
            master_password = self.encryption_service._cached_password
            self.main_window = CredentialWindow(cred_controller, self.config, master_password=master_password)
        else:
            self.main_window = MainWindow(
                self.config,
                self.encryption_service,
                self.note_controller,
                self.notebook_controller
            )
            self.main_window.showMaximized()
        logger.info(f"Main window displayed — mode: {mode}")


def main():
    """Application entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app = TMApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
