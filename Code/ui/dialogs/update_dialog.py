import sys
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QProgressBar,
    QMessageBox, QApplication
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from core import C, APPDATA, APP_VERSION
from core.config import ICON_SMALL
from ui.styles import CF, btn_style
from updater.app_updater import AppUpdater

UPDATER_AVAILABLE = True


class UpdateWorker(QThread):
    progress = pyqtSignal(int, int)   # bytes_downloaded, total_bytes
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, updater, download=False):
        super().__init__()
        self.updater  = updater
        self.download = download

    def run(self):
        try:
            if self.download:
                success, result = self.updater.download_update(
                    progress_callback=lambda d, t: self.progress.emit(d, t)
                )
                self.finished.emit(success, result)
            else:
                info = self.updater.check_for_updates()
                self.finished.emit(True, json.dumps(info))
        except Exception as e:
            self.finished.emit(False, str(e))


class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄 Vérifier les mises à jour")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        self.setStyleSheet(f"QDialog {{ background: {C['bg']}; }}")
        if ICON_SMALL.exists():
            self.setWindowIcon(QIcon(str(ICON_SMALL)))

        app_dir = Path(sys.argv[0]).resolve().parent if sys.argv[0] else None
        self.updater     = AppUpdater(APP_VERSION, app_dir=app_dir) if UPDATER_AVAILABLE else None
        self.update_info = None
        self.downloaded_file = None

        self._build()
        self._check_updates()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("🔄 Vérification des mises à jour")
        title.setFont(CF(14, True))
        title.setStyleSheet(f"color: {C['text']}; background: transparent;")
        layout.addWidget(title)

        self._info_text = QTextEdit()
        self._info_text.setReadOnly(True)
        self._info_text.setMinimumHeight(400)
        self._info_text.setStyleSheet(f"""
            QTextEdit {{
                background: {C['surface']};
                color: {C['text']};
                border: 1px solid {C['border']};
                border-radius: 6px;
                padding: 10px;
                font-family: 'Courier New';
                font-size: 10pt;
            }}
        """)
        layout.addWidget(self._info_text)

        self._progress = QProgressBar()
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 6px;
                text-align: center;
                color: {C['text']};
            }}
            QProgressBar::chunk {{ background: {C['accent']}; }}
        """)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self._btn_update = QPushButton("📥 Télécharger & Installer")
        self._btn_update.setFont(CF(11))
        self._btn_update.setStyleSheet(btn_style(outline=False))
        self._btn_update.setEnabled(False)
        self._btn_update.clicked.connect(self._start_download)
        btn_layout.addWidget(self._btn_update)

        self._btn_cancel = QPushButton("Annuler")
        self._btn_cancel.setFont(CF(11))
        self._btn_cancel.setStyleSheet(btn_style(outline=True))
        self._btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_cancel)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _check_updates(self):
        if not UPDATER_AVAILABLE:
            self._info_text.setText("❌ Erreur: Module de mise à jour non disponible")
            return
        self._info_text.setText("⏳ Vérification en cours...\n\nVeuillez patienter...")
        self._worker = UpdateWorker(self.updater, download=False)
        self._worker.finished.connect(self._on_check_finished)
        self._worker.start()

    def _on_check_finished(self, success, data):
        if not success:
            self._info_text.setText(f"❌ Erreur lors de la vérification:\n{data}")
            self._btn_update.setEnabled(False)
            return

        self.update_info = json.loads(data)
        if not self.update_info.get("has_update"):
            self._info_text.setText(
                f"✅ Vous utilisez la dernière version!\n\n"
                f"Version actuelle: v{self.update_info.get('current_version', '?')}"
            )
            self._btn_update.setEnabled(False)
            return

        info = self.update_info
        self._info_text.setText(
            f"🎉 Une nouvelle version est disponible!\n\n"
            f"Version actuelle: v{info.get('current_version', '?')}\n"
            f"Nouvelle version: v{info.get('latest_version', '?')}\n"
            f"Taille: {info.get('file_size', 0) / (1024*1024):.1f} MB\n\n"
            f"📝 Notes de mise à jour:\n"
            f"{info.get('release_notes', 'Pas de notes')[:500]}"
        )
        self._btn_update.setEnabled(True)

    def _start_download(self):
        self._btn_update.setEnabled(False)
        self._btn_cancel.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._info_text.setText("⏳ Téléchargement en cours...")
        self._worker = UpdateWorker(self.updater, download=True)
        self._worker.progress.connect(self._on_download_progress)
        self._worker.finished.connect(self._on_download_finished)
        self._worker.start()

    def _on_download_progress(self, downloaded, total):
        if total > 0:
            self._progress.setValue(int((downloaded / total) * 100))

    def _on_download_finished(self, success, result):
        self._progress.setVisible(False)
        self._btn_cancel.setEnabled(True)
        if not success:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du téléchargement:\n{result}")
            self._btn_update.setEnabled(True)
            return

        self.downloaded_file = result
        reply = QMessageBox.question(
            self, "Installation",
            "La mise à jour a été téléchargée avec succès.\n\n"
            "Voulez-vous redémarrer l'application pour installer la mise à jour?\n\n"
            "L'application sera automatiquement fermée et la nouvelle version sera lancée.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            APPDATA.log_install(f"Installation de la mise à jour v{self.update_info.get('latest_version')}")
            self.updater.apply_update_and_restart(result)
            QApplication.quit()
        else:
            self._info_text.setText(
                "📥 Mise à jour téléchargée et prête à être installée.\n\n"
                "Cliquez sur 'Redémarrer maintenant' pour installer."
            )
            self._btn_update.setText("🔄 Redémarrer maintenant")
            self._btn_update.clicked.disconnect()
            self._btn_update.clicked.connect(self._install_now)
            self._btn_update.setEnabled(True)

    def _install_now(self):
        if self.downloaded_file and Path(self.downloaded_file).exists():
            self.updater.apply_update_and_restart(self.downloaded_file)
            QApplication.quit()
