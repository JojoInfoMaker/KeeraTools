import subprocess
import logging
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

class TerminalWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)

    def append_message(self, message, color="#FFFFFF"):
        # Kept simple; could style with HTML if desired
        self.append(message)


class FlatpakInstallWorker(QThread):
    progress = pyqtSignal(str, bool)
    finished = pyqtSignal(bool)

    def __init__(self, app_id: str):
        super().__init__()
        self.app_id = app_id
        self._stop = False

    def run(self):
        if self._stop:
            self.finished.emit(False)
            return
        try:
            # Use explicit 'flathub' remote to avoid ambiguity
            cmd = ["flatpak", "install", "--system", "-y", "flathub", self.app_id]
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                self.progress.emit(f"Installed {self.app_id}", True)
                self.finished.emit(True)
            else:
                err = (result.stderr or "").strip()
                out = (result.stdout or "").strip()
                msg = err if err else out if out else "Unknown error"
                self.progress.emit(f"Failed: {msg}", False)
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
    """
    Expects app_info to contain at least:
      - app_info['app_id']  -> Flatpak application ID (e.g., 'app.bbsync.BlackboardSync')
      - app_info['name']    -> Display name (for UI)
    """
    def __init__(self, parent, app_info: dict):
        super().__init__(parent)
        self.app_info = app_info or {}
        self.success = False

        display_name = self.app_info.get("name") or self.app_info.get("app_id") or "Application"
        self.setWindowTitle(f"Installing {display_name}")

        self._setup_ui()
        self._start_installation()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(f"Installing {self.app_info.get('name', self.app_info.get('app_id', 'Application'))}")
        layout.addWidget(title)

        self.terminal = TerminalWidget()
        layout.addWidget(self.terminal)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_install)
        layout.addWidget(self.cancel_btn)

        self.resize(600, 400)

    def _start_installation(self):
        # Use app_id (not 'name', not 'flatpak_id')
        app_id = self.app_info.get("app_id")

        if not app_id:
            # Fallback for older callers: accept 'flatpak_id' if present
            app_id = self.app_info.get("flatpak_id")

        if not app_id:
            self.terminal.append_message("Error: Missing Flatpak app_id in app_info")
            return

        self.worker = FlatpakInstallWorker(app_id)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._installation_finished)
        self.worker.start()

    def _update_progress(self, msg, success=True):
        self.terminal.append_message(msg)

    def _cancel_install(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
            self.terminal.append_message("Cancelled by user")
        self.close()

    def _installation_finished(self, success: bool):
        self.success = success
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.cancel_btn.setText("Close")
