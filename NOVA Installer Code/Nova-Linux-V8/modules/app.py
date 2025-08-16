"""
Nova Installer App Class
Created by Nixiews
Last updated: 2025-08-16 20:59:47 UTC
"""

import os
import sys
import json
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                            QFileDialog, QMenu, QAction)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from .theme_manager import ThemeManager
from .language_manager import LanguageManager
from .icon_manager import IconManager
from .menu_manager import MenuManager
from .ui_manager import UIManager
from .app_manager import AppManager
from .dialogs.about_dialog import AboutDialog
from .dialogs.color_dialog import ColorDialog
from .dialogs.install_dialog import InstallDialog
from .dialogs.language_dialog import LanguageDialog

logger = logging.getLogger(__name__)

# Constants
CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
APPS_FILE = os.path.join(CONFIG_DIR, "apps.json")

def load_config():
    """Load configuration from file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "language": "en",
            "theme": {
                "appearance_mode": "dark",
                "color_theme": "night-blue"
            }
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {
            "language": "en",
            "theme": {
                "appearance_mode": "dark",
                "color_theme": "night-blue"
            }
        }

def save_config(config):
    """Save configuration to file"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        QMessageBox.critical(
            None,
            "Error",
            f"Failed to save configuration: {str(e)}"
        )

class NovaInstallerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set metadata
        self.current_datetime = "2025-08-16 20:59:47"
        self.current_user = "Nixiews"
        logger.info(f"Starting Nova Installer - Time: {self.current_datetime} - User: {self.current_user}")

        # Load configuration first
        self.config = load_config()

        # Initialize managers with config
        self.theme_manager = ThemeManager(self.config)
        self.language_manager = LanguageManager()
        self.icon_manager = IconManager()
        self.menu_manager = MenuManager(self)

        # Synchronize config with theme manager's config
        if "theme" not in self.config:
            self.config["theme"] = {}
        self.config["theme"].update(self.theme_manager.theme_config)
        save_config(self.config)

        # Load settings
        self.load_language()
        self.load_apps()

        # Setup UI basics
        self.setup_fonts()

        # Initialize UI manager
        self.ui_manager = UIManager(self)

        # Initialize app manager
        self.app_manager = AppManager(self)

        # Setup window and UI
        self.ui_manager.setup_window()

        # Set window icon
        self.set_window_icon()

        # Apply theme
        self.apply_theme()

    def setup_fonts(self):
        """Setup application fonts"""
        self.fonts = {
            "title": QFont("Comfortaa", 20, QFont.Bold),
            "header": QFont("Comfortaa", 16, QFont.Bold),
            "normal": QFont("Comfortaa", 12),
            "small": QFont("Comfortaa", 10)
        }

    def set_window_icon(self):
        """Set the window icon"""
        icon = self.icon_manager.get_app_icon()
        if icon:
            self.setWindowIcon(icon)

    def load_language(self):
        """Load language settings"""
        self.current_language = self.config.get("language", "en")

    def load_apps(self):
        """Load applications data"""
        try:
            with open(APPS_FILE, 'r', encoding='utf-8') as f:
                self.apps_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading apps data: {e}")
            self.apps_data = {}

    def apply_theme(self):
        """Apply current theme to application"""
        theme = self.theme_manager.get_current_theme()
        stylesheet = self.theme_manager.generate_stylesheet(theme)
        self.setStyleSheet(stylesheet)

    def show_about_dialog(self):
        """Show about dialog"""
        dialog = AboutDialog(self, self.config)
        dialog.exec_()

    def show_color_dialog(self):
        """Show color theme dialog"""
        dialog = ColorDialog(self, self.config)
        if dialog.exec_():
            self.apply_theme()
            save_config(self.config)

    def show_language_dialog(self):
        """Show language selection dialog"""
        dialog = LanguageDialog(self, self.config)
        if dialog.exec_():
            self.load_language()
            self.ui_manager.update_texts()
            save_config(self.config)

    def install_selected(self):
        """Install selected applications"""
        if not self.app_manager.selected_apps:
            QMessageBox.warning(
                self,
                self.tr("warning"),
                self.tr("no_apps_selected")
            )
            return

        dialog = InstallDialog(self, self.app_manager.selected_apps)
        dialog.exec_()

    def tr(self, key):
        """Translate text using language manager"""
        return self.language_manager.translate(key, self.current_language)

    def closeEvent(self, event):
        """Handle application close"""
        reply = QMessageBox.question(
            self,
            self.tr("confirm_exit"),
            self.tr("exit_message"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            save_config(self.config)
            event.accept()
        else:
            event.ignore()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Nova Installer")
    app.setOrganizationName("Nixiews")
    app.setApplicationVersion("8.0")

    window = NovaInstallerApp()
    window.show()

    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
