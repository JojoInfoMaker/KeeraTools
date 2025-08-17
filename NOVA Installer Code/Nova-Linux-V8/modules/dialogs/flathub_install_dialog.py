import subprocess
import logging
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class TerminalWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)

    def append_message(self, message, color="#FFFFFF"):
        self.append(message)

def parse_flatpak_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    apps = []
    for component in root.findall("component"):
        if component.get("type") != "desktop-application":
            continue
        app_id = component.find("id").text
        name = component.find("name").text
        apps.append({
            "flatpak_id": app_id,  # store XML <id> here
            "name": name,
        })
    return apps


class FlatpakInstallWorker(QThread):
    progress = pyqtSignal(str, bool)
    finished = pyqtSignal(bool)

    def __init__(self, app_id):
        super().__init__()
        self.app_id = app_id
        self._stop = False

    def run(self):
        if self._stop:
            self.finished.emit(False)
            return
        try:
            cmd = ["flatpak", "install", "-y", self.app_id]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
            if result.returncode == 0:
                self.progress.emit(f"Installed {self.app_id}", True)
                self.finished.emit(True)
            else:
                self.progress.emit(f"Failed: {result.stderr.strip()}", False)
                self.finished.emit(False)
        except subprocess.TimeoutExpired:
            self.progress.emit("Install timed out", False)
            self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"Error: {e}", False)
            self.finished.emit(False)

    def stop(self):
        self._stop = True

class FlathubInstallDialog(QDialog):
    def __init__(self, parent, app_info):
        super().__init__(parent)
        self.app_info = app_info
        self.success = False
        self.setWindowTitle(f"Installing {app_info['name']}")
        self.setup_ui()
        self.start_installation()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel(f"Installing {self.app_info['name']}")
        layout.addWidget(title)
        self.terminal = TerminalWidget()
        layout.addWidget(self.terminal)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_install)
        layout.addWidget(self.cancel_btn)
        self.resize(600, 400)

    def start_installation(self):
        app_id = self.app_info.get("flatpak_id") or self.app_info.get("name")
        self.worker = FlatpakInstallWorker(app_id)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.installation_finished)
        self.worker.start()

    def update_progress(self, msg, success=True):
        self.terminal.append_message(msg)

    def cancel_install(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
            self.terminal.append_message("Cancelled by user")
        self.close()

    def installation_finished(self, success):
        self.success = success
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.cancel_btn.setText("Close")
