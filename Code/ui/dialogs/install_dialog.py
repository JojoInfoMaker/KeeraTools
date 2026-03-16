from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from core import TR, C
from core.config import ICON_SMALL
from ui.styles import CF, btn_style
from workers.install_thread import InstallThread


class InstallDialog(QDialog):
    def __init__(self, apps, mode="install", parent=None, package_manager="winget"):
        super().__init__(parent)
        self.package_manager = package_manager.lower()
        labels = {
            "install":   TR.t("install_in_progress"),
            "update":    TR.t("update_in_progress"),
            "uninstall": TR.t("uninstall_in_progress"),
        }
        self.setWindowTitle(labels[mode])
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"background: {C['surface']}; color: {C['text']};")
        if ICON_SMALL.exists():
            self.setWindowIcon(QIcon(str(ICON_SMALL)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel(TR.t("install_count", count=len(apps)))
        title.setFont(CF(15, True))
        title.setStyleSheet(f"color: {C['text']};")
        layout.addWidget(title)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(480)
        layout.addWidget(self.log_box, 1)

        self.btn_close = QPushButton(TR.t("close"))
        self.btn_close.setFont(CF(13))
        self.btn_close.setStyleSheet(btn_style(C["accent"]))
        self.btn_close.setEnabled(False)
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close, alignment=Qt.AlignRight)

        self.thread = InstallThread(apps, mode, self.package_manager)
        self.thread.log_signal.connect(self._on_log_message)
        self.thread.prog_signal.connect(lambda cur, tot: None)
        self.thread.done_signal.connect(self._on_done)
        self.thread.start()

    def _on_log_message(self, message):
        if not message:
            return
        cursor = self.log_box.textCursor()
        cursor.movePosition(cursor.End)
        parts = message.split('\r')
        for i, part in enumerate(parts):
            if i == 0:
                cursor.insertText(part)
            else:
                cursor.movePosition(cursor.StartOfLine)
                cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)
                cursor.insertText(part)
        cursor.movePosition(cursor.End)
        self.log_box.setTextCursor(cursor)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def _on_done(self, success, failed):
        self.log_box.append(f"\n{'='*60}")
        if self.thread._abort:
            self.log_box.append("⛔  Installation annulée par l'utilisateur.")
        self.log_box.append(f"✓ {len(success)} réussies  —  ✗ {len(failed)} échouées")
        if failed:
            self.log_box.append(f"Problèmes avec: {', '.join(failed)}")
        else:
            self.log_box.append("Aucune erreur!")
        self.log_box.append(f"{'='*60}")
        self.btn_close.setEnabled(True)

    def closeEvent(self, event):
        if self.thread.isRunning() and not self.thread._abort:
            reply = QMessageBox.warning(
                self,
                "⚠  Annuler l'installation ?",
                "Une installation est en cours.\n\n"
                "Voulez-vous l'annuler et fermer la fenêtre ?\n"
                "Le logiciel en cours d'installation sera peut-être partiellement installé.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.log_box.append("\n⛔  Annulation en cours…")
            self.thread.abort()
            self.thread.wait(3000)
        event.accept()
