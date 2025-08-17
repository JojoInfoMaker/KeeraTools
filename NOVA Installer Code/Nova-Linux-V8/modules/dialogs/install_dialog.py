"""
Nova Installer Install Dialog
Created by Nixiews
Last updated: 2025-08-17 09:22:02 UTC
"""

import os
import subprocess
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar,
                            QPushButton, QScrollArea, QWidget, QCheckBox,
                            QHBoxLayout, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from .flathub_install_dialog import FlathubInstallDialog

logger = logging.getLogger(__name__)

class InstallWorker(QThread):
    progress = pyqtSignal(str, bool)  # Message, Success status
    installation_complete = pyqtSignal(bool)  # Success status

    def __init__(self, app_info):
        super().__init__()
        self.app_info = app_info

    def run(self):
        """Run installation process"""
        try:
            package_manager = self.app_info.get('package_manager', 'unknown')
            package_name = self.app_info.get('package_name')

            if not package_name:
                self.progress.emit(f"Error: No package name for {self.app_info.get('name')}", False)
                self.installation_complete.emit(False)
                return

            # Use pkexec for administrative privileges
            if package_manager == 'snap':
                cmd = ['pkexec', 'snap', 'install', package_name]
            elif package_manager == 'apt':
                cmd = ['pkexec', 'apt-get', 'install', '-y', package_name]
            else:
                self.progress.emit(f"Unsupported package manager: {package_manager}", False)
                self.installation_complete.emit(False)
                return

            self.progress.emit(f"Installing {self.app_info.get('name')}...", True)

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
                    self.progress.emit(output.strip(), True)

            returncode = process.poll()

            if returncode == 0:
                self.progress.emit(f"Successfully installed {self.app_info.get('name')}", True)
                self.installation_complete.emit(True)
            else:
                error = process.stderr.read()
                self.progress.emit(f"Installation failed: {error}", False)
                self.installation_complete.emit(False)

        except Exception as e:
            self.progress.emit(f"Installation error: {str(e)}", False)
            self.installation_complete.emit(False)

class InstallDialog(QDialog):
    def __init__(self, parent, selected_apps):
        super().__init__(parent)
        self.parent = parent
        self.selected_apps = selected_apps
        self.app_info_list = []
        self.current_install_index = -1
        self.successful_installs = []

        self.setWindowTitle("Installing Applications")
        self.setup_ui()
        self.load_app_info()
        self.start_next_installation()

    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("Installing Selected Applications")
        title.setFont(self.parent.fonts["header"])
        layout.addWidget(title)

        # Create scrollable area for installation status
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.status_widget = QWidget()
        self.status_layout = QVBoxLayout(self.status_widget)
        self.status_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.status_widget)
        layout.addWidget(scroll)

        # Progress bar
        self.progress_label = QLabel("Preparing installation...")
        layout.addWidget(self.progress_label)

        # Current operation progress
        self.current_progress = QProgressBar()
        self.current_progress.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.current_progress)

        # Overall progress
        self.overall_progress = QProgressBar()
        layout.addWidget(self.overall_progress)

        # Buttons layout
        button_layout = QHBoxLayout()

        # Skip button
        self.skip_button = QPushButton("Skip Current")
        self.skip_button.clicked.connect(self.skip_current)
        button_layout.addWidget(self.skip_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_installation)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Set dialog size
        self.resize(600, 400)

    def load_app_info(self):
        """Load detailed app information for selected apps"""
        for app_name in self.selected_apps:
            # Find app info in all categories
            for category in self.parent.app_manager.categories.values():
                for app in category:
                    if app.get('name') == app_name:
                        self.app_info_list.append(app)
                        break

        # Setup overall progress
        self.overall_progress.setRange(0, len(self.app_info_list))
        self.overall_progress.setValue(0)

    def add_status_message(self, message, success=True):
        """Add status message to the status area"""
        label = QLabel(message)
        label.setWordWrap(True)
        if not success:
            label.setStyleSheet("color: red;")
        self.status_layout.addWidget(label)

    def start_next_installation(self):
        """Start installation of next app"""
        self.current_install_index += 1

        if self.current_install_index >= len(self.app_info_list):
            self.installation_finished()
            return

        current_app = self.app_info_list[self.current_install_index]
        self.progress_label.setText(f"Installing {current_app.get('name')}...")

        # Handle Flatpak installations differently
        if current_app.get('package_manager') == 'flatpak':
            dialog = FlathubInstallDialog(self.parent, current_app)
            dialog.exec_()
            if dialog.success:
                self.successful_installs.append(current_app.get('name'))
                self.add_status_message(f"Successfully installed {current_app.get('name')}")
            else:
                self.add_status_message(f"Failed to install {current_app.get('name')}", False)
            self.overall_progress.setValue(len(self.successful_installs))
            self.start_next_installation()
            return

        # For other package managers, use the existing worker
        self.worker = InstallWorker(current_app)
        self.worker.progress.connect(self.update_progress)
        self.worker.installation_complete.connect(self.handle_installation_complete)
        self.worker.start()

    def update_progress(self, message, success):
        """Update progress information"""
        self.add_status_message(message, success)

    def handle_installation_complete(self, success):
        """Handle completion of current installation"""
        current_app = self.app_info_list[self.current_install_index]
        if success:
            self.successful_installs.append(current_app.get('name'))
        self.overall_progress.setValue(len(self.successful_installs))
        self.start_next_installation()

    def skip_current(self):
        """Skip current installation"""
        current_app = self.app_info_list[self.current_install_index]
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
        self.add_status_message(f"Skipped installation of {current_app.get('name')}", False)
        self.start_next_installation()

    def cancel_installation(self):
        """Cancel all installations"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
        self.add_status_message("Installation cancelled by user", False)
        self.close()

    def installation_finished(self):
        """Handle completion of all installations"""
        self.progress_label.setText("Installation Complete")
        self.current_progress.setRange(0, 1)
        self.current_progress.setValue(1)

        # Show summary
        if self.successful_installs:
            self.add_status_message("\nSuccessfully installed applications:", True)
            for app in self.successful_installs:
                self.add_status_message(f"- {app}", True)

        failed = set(app.get('name') for app in self.app_info_list) - set(self.successful_installs)
        if failed:
            self.add_status_message("\nFailed or skipped applications:", False)
            for app in failed:
                self.add_status_message(f"- {app}", False)

        # Change cancel button to close
        self.cancel_button.setText("Close")
        self.skip_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle dialog close"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
        event.accept()
