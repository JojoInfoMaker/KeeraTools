"""
Nova Installer Flathub Install Dialog
Created by Nixiews
Last updated: 2025-08-17 09:19:22 UTC
"""

import os
import subprocess
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar,
                            QPushButton, QTextEdit, QWidget, QHBoxLayout,
                            QFrame, QScrollBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QTextCharFormat, QFontDatabase

logger = logging.getLogger(__name__)

class TerminalWidget(QTextEdit):
    """Custom widget to emulate terminal display"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_appearance()

    def setup_appearance(self):
        """Setup terminal-like appearance"""
        # Use monospace font
        font_id = QFontDatabase.addApplicationFont(":/fonts/JetBrainsMono-Regular.ttf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            font_family = "Monospace"

        self.setFont(QFont(font_family, 10))

        # Set colors
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor("#1E1E1E"))
        palette.setColor(QPalette.Text, QColor("#FFFFFF"))
        self.setPalette(palette)

        # Setup text edit properties
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)

        # Custom scrollbar styling
        scrollbar = QScrollBar(Qt.Vertical, self)
        scrollbar.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: #2E2E2E;
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #525252;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

    def append_message(self, message, color="#FFFFFF"):
        """Append message with specified color"""
        cursor = self.textCursor()
        format = QTextCharFormat()
        format.setForeground(QColor(color))
        cursor.movePosition(cursor.End)
        cursor.insertText(f"{message}\n", format)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

class FlathubInstallWorker(QThread):
    progress = pyqtSignal(str, str)  # Message, Color
    installation_complete = pyqtSignal(bool)  # Success status

    def __init__(self, app_info):
        super().__init__()
        self.app_info = app_info

    def run(self):
        """Run Flathub installation process"""
        try:
            package_name = self.app_info.get('package_name')

            if not package_name:
                self.progress.emit(
                    f"Error: No package name for {self.app_info.get('name')}",
                    "#FF5555"
                )
                self.installation_complete.emit(False)
                return

            # First, make sure Flathub is added as a remote
            self.add_flathub_remote()

            # Install the package
            cmd = ['flatpak', 'install', 'flathub', package_name, '-y']

            self.progress.emit(
                f"Starting installation of {self.app_info.get('name')}...",
                "#00FF00"
            )

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress.emit(output.strip(), "#FFFFFF")

            returncode = process.poll()

            if returncode == 0:
                self.progress.emit(
                    f"Successfully installed {self.app_info.get('name')}",
                    "#00FF00"
                )
                self.installation_complete.emit(True)
            else:
                error = process.stderr.read()
                self.progress.emit(f"Installation failed: {error}", "#FF5555")
                self.installation_complete.emit(False)

        except Exception as e:
            self.progress.emit(f"Installation error: {str(e)}", "#FF5555")
            self.installation_complete.emit(False)

    def add_flathub_remote(self):
        """Add Flathub remote if not already added"""
        try:
            # Check if Flathub is already added
            check_cmd = ['flatpak', 'remotes']
            result = subprocess.run(check_cmd, capture_output=True, text=True)

            if 'flathub' not in result.stdout.lower():
                self.progress.emit("Adding Flathub remote...", "#FFFF00")
                add_cmd = [
                    'flatpak', 'remote-add', '--if-not-exists',
                    'flathub', 'https://flathub.org/repo/flathub.flatpakrepo'
                ]
                subprocess.run(add_cmd, check=True)
                self.progress.emit("Flathub remote added successfully", "#00FF00")

        except Exception as e:
            self.progress.emit(f"Error adding Flathub remote: {str(e)}", "#FF5555")
            raise

class FlathubInstallDialog(QDialog):
    def __init__(self, parent, app_info):
        super().__init__(parent)
        self.parent = parent
        self.app_info = app_info
        self.success = False

        self.setWindowTitle("Flathub Installation")
        self.setup_ui()
        self.start_installation()

    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel(f"Installing {self.app_info.get('name')} from Flathub")
        title.setFont(self.parent.fonts["header"])
        layout.addWidget(title)

        # Terminal display
        self.terminal = TerminalWidget()
        layout.addWidget(self.terminal)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_installation)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Set dialog size
        self.resize(600, 400)

    def start_installation(self):
        """Start the installation process"""
        self.worker = FlathubInstallWorker(self.app_info)
        self.worker.progress.connect(self.update_progress)
        self.worker.installation_complete.connect(self.installation_finished)
        self.worker.start()

    def update_progress(self, message, color):
        """Update terminal with new message"""
        self.terminal.append_message(message, color)

    def cancel_installation(self):
        """Cancel the installation"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.terminal.append_message("Installation cancelled by user", "#FF5555")
        self.close()

    def installation_finished(self, success):
        """Handle installation completion"""
        self.success = success
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.cancel_button.setText("Close")

    def closeEvent(self, event):
        """Handle dialog close"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
        event.accept()
