"""
Nova Installer Main Application
Created by Nixiews
Last updated: 2025-08-16 21:43:05 UTC
"""

import os
import sys
import json
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                            QFileDialog, QMenu, QAction, QWidget, QVBoxLayout,
                            QStyleFactory, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont

from modules.language_manager import LanguageManager
from modules.icon_manager import IconManager
from modules.menu_manager import MenuManager
from modules.ui_manager import UIManager
from modules.app_manager import AppManager
from modules.dialogs.about_dialog import AboutDialog
from modules.dialogs.install_dialog import InstallDialog
from modules.dialogs.language_dialog import LanguageDialog

logger = logging.getLogger(__name__)

class NovaInstallerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set metadata
        self.current_datetime = "2025-08-17 09:27:55"
        self.current_user = "Nixiews"
        logger.info(f"Starting Nova Installer - Time: {self.current_datetime} - User: {self.current_user}")

        # Load configuration first
        self.config = load_config()

        # Initialize managers
        self.language_manager = LanguageManager()
        self.icon_manager = IconManager()
        self.menu_manager = MenuManager(self)

        # Load settings
        self.load_language()

        # Setup UI basics
        self.setup_fonts()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # Initialize UI manager first
        self.ui_manager = UIManager(self)
        # Setup window and UI (this creates categories_frame)
        self.ui_manager.setup_window()

        # Now initialize app manager after UI is set up
        self.app_manager = AppManager(self)

        # Set window icon
        self.set_window_icon()

        # Configure window
        self.setWindowTitle("Nova Installer")
        self.resize(1000, 600)
        self.setMinimumSize(800, 500)

    def setup_window(self):
        """Setup main window layout"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for categories and content
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # Create category frame (left side)
        self.category_frame = QWidget()
        self.category_frame.setMinimumWidth(200)
        self.category_frame.setMaximumWidth(300)

        # Create content frame (right side)
        self.content_frame = QWidget()

        # Add frames to splitter
        self.splitter.addWidget(self.category_frame)
        self.splitter.addWidget(self.content_frame)

        # Set splitter proportions
        self.splitter.setStretchFactor(0, 0)  # Category frame doesn't stretch
        self.splitter.setStretchFactor(1, 1)  # Content frame stretches

    def setup_fonts(self):
        """Setup application fonts"""
        self.fonts = {
            "title": QFont("Comfortaa", 20, QFont.Bold),
            "header": QFont("Comfortaa", 16, QFont.Bold),
            "normal": QFont("Comfortaa", 12),
            "small": QFont("Comfortaa", 10)
        }

    def closeEvent(self, event):
        """Handle application close"""
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    app = QApplication(sys.argv)

    # Use system style
    app.setStyle(QStyleFactory.create('Fusion'))

    # Set application metadata
    app.setApplicationName("Nova Installer")
    app.setOrganizationName("Nixiews")
    app.setApplicationVersion("8.0")

    window = NovaInstallerApp()
    window.show()

    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
