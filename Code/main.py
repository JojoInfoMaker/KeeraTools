import sys
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette

# ── Bootstrap core (charge settings, thème, traductions) ─────────
import core  # noqa: F401 — exécute core/__init__.py
from core import C, APPDATA, APP_VERSION
from core import TR

from ui.main_window import MainWindow
from ui.styles import load_comfortaa

UPDATER_AVAILABLE = True


def _setup_palette(app: QApplication):
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(C["bg"]))
    palette.setColor(QPalette.WindowText,      QColor(C["text"]))
    palette.setColor(QPalette.Base,            QColor(C["surface"]))
    palette.setColor(QPalette.AlternateBase,   QColor(C["surface2"]))
    palette.setColor(QPalette.Text,            QColor(C["text"]))
    palette.setColor(QPalette.Button,          QColor(C["surface"]))
    palette.setColor(QPalette.ButtonText,      QColor(C["text"]))
    palette.setColor(QPalette.Highlight,       QColor(C["accent"]))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)


def _check_startup_updates(window):
    if not UPDATER_AVAILABLE:
        return
    try:
        from pathlib import Path
        from updater.app_updater import AppUpdater
        from PyQt5.QtWidgets import QMessageBox

        app_dir = Path(sys.argv[0]).resolve().parent if sys.argv[0] else None
        updater = AppUpdater(APP_VERSION, app_dir=app_dir)
        info    = updater.check_for_updates(timeout=5)
        if info.get("has_update"):
            APPDATA.log_install(f"Mise à jour disponible: v{info.get('latest_version')}")
            QMessageBox.information(
                window,
                "🔄 Mise à jour disponible",
                f"Une nouvelle version ({info.get('latest_version')}) est disponible.\n\n"
                f"Cliquez sur le bouton 🔄 dans la barre d'outils pour mettre à jour.",
            )
    except Exception:
        pass  # Silencieux


if __name__ == "__main__":
    # DPI Windows
    os.environ.pop("QT_SCALE_FACTOR", None)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    load_comfortaa()
    _setup_palette(app)

    window = MainWindow()
    window.show()

    QTimer.singleShot(2000, lambda: _check_startup_updates(window))

    sys.exit(app.exec_())
