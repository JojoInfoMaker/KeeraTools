import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar,
                             QPushButton, QScrollArea, QWidget, QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QTimer
from .flathub_install_dialog import FlathubInstallDialog

logger = logging.getLogger(__name__)

class InstallDialog(QDialog):
    def __init__(self, parent, selected_apps_info):
        """
        selected_apps_info: list of dicts containing app info
        """
        super().__init__(parent)
        self.parent = parent
        self.app_info_list = selected_apps_info
        self.current_index = -1
        self.successful_installs = []

        self.setWindowTitle("Installing Applications")
        self.setup_ui()

        QTimer.singleShot(100, self.start_next_installation)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("Installing Selected Applications")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.status_widget = QWidget()
        self.status_layout = QVBoxLayout(self.status_widget)
        self.status_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.status_widget)
        layout.addWidget(scroll)

        self.progress_label = QLabel("Preparing installation...")
        layout.addWidget(self.progress_label)

        self.current_progress = QProgressBar()
        self.current_progress.setRange(0, 0)
        layout.addWidget(self.current_progress)

        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, len(self.app_info_list))
        layout.addWidget(self.overall_progress)

        button_layout = QHBoxLayout()
        self.skip_button = QPushButton("Skip Current")
        self.skip_button.clicked.connect(self.skip_current)
        button_layout.addWidget(self.skip_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_installation)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        self.resize(600, 400)

    def add_status_message(self, message, success=True):
        label = QLabel(message)
        color = "green" if success else "red"
        label.setStyleSheet(f"color: {color}")
        self.status_layout.addWidget(label)
        self.status_widget.repaint()

    def start_next_installation(self):
        self.current_index += 1
        if self.current_index >= len(self.app_info_list):
            self.finish_installation()
            return

        app = self.app_info_list[self.current_index]
        self.progress_label.setText(f"Installing {app['name']}...")
        dialog = FlathubInstallDialog(self.parent, app)
        dialog.exec_()
        if getattr(dialog, "success", False):
            self.successful_installs.append(app['name'])
            self.add_status_message(f"Installed {app['name']}")
        else:
            self.add_status_message(f"Failed {app['name']}", False)

        self.overall_progress.setValue(len(self.successful_installs))
        QTimer.singleShot(100, self.start_next_installation)

    def skip_current(self):
        if self.current_index < len(self.app_info_list):
            app = self.app_info_list[self.current_index]
            self.add_status_message(f"Skipped {app['name']}", False)
            QTimer.singleShot(100, self.start_next_installation)

    def cancel_installation(self):
        self.add_status_message("Installation cancelled by user", False)
        self.close()

    def finish_installation(self):
        self.progress_label.setText("Installation Complete")
        self.current_progress.setRange(0, 1)
        self.current_progress.setValue(1)
        for app in self.successful_installs:
            self.add_status_message(f"- {app}", True)
        failed = set(app['name'] for app in self.app_info_list) - set(self.successful_installs)
        for app in failed:
            self.add_status_message(f"- {app}", False)
        self.cancel_button.setText("Close")
        self.skip_button.setEnabled(False)
