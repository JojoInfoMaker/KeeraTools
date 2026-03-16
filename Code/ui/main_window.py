from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QStackedWidget,
    QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QPalette

from core import C, TR, APPDATA, APP_NAME, APP_VERSION
from core.config import ICON_SMALL, ICON_BIG
from ui.styles import CF, global_css, btn_style, nav_btn_style
from ui.tabs import AppsTab, PersonalizationTab, USBBootableTab
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.theme_dialog import ThemeDialog
from ui.dialogs.update_dialog import UpdateDialog

UPDATER_AVAILABLE = True


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} ™")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 860)
        if ICON_SMALL.exists():
            self.setWindowIcon(QIcon(str(ICON_SMALL)))
        self.setStyleSheet(global_css() + f"QMainWindow {{ background: {C['bg']}; }}")
        self._build()

    def _build(self):
        old = self.centralWidget()
        if old:
            old.deleteLater()
        central = QWidget()
        central.setStyleSheet(f"background: {C['bg']};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {C['bg']};")
        self._apps_tab  = AppsTab()
        self._perso_tab = PersonalizationTab()
        self._usb_tab   = USBBootableTab()
        self._stack.addWidget(self._apps_tab)
        self._stack.addWidget(self._perso_tab)
        self._stack.addWidget(self._usb_tab)
        root.addWidget(self._stack, 1)

    def _build_header(self):
        header = QFrame()
        header.setFixedHeight(120)
        header.setStyleSheet(
            f"QFrame {{ background: {C['surface']}; border-bottom: 1px solid {C['border']}; }}"
        )
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 10, 24, 10)
        h.setSpacing(16)
        h.setAlignment(Qt.AlignVCenter)

        if ICON_BIG.exists():
            logo_lbl = QLabel()
            px = QPixmap(str(ICON_BIG)).scaled(110, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(px)
            logo_lbl.setFixedSize(110, 110)
            logo_lbl.setAlignment(Qt.AlignCenter)
            h.addWidget(logo_lbl)

        ver_badge = QLabel(f"v{APP_VERSION}")
        ver_badge.setFont(CF(11))
        ver_badge.setStyleSheet(
            f"background: {C['accent']}22; color: {C['accent']}; "
            f"border: 1px solid {C['accent']}44; border-radius: 11px; padding: 2px 10px;"
        )
        h.addWidget(ver_badge)
        h.addStretch()

        # Navigation centrale
        nav_frame = QFrame()
        nav_frame.setStyleSheet(
            f"QFrame {{ background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 10px; }}"
        )
        nav_h = QHBoxLayout(nav_frame)
        nav_h.setContentsMargins(5, 5, 5, 5)
        nav_h.setSpacing(3)

        self._btn_apps  = QPushButton(f"📦  {TR.t('applications')}")
        self._btn_perso = QPushButton(f"🎨  {TR.t('personalization')}")
        self._btn_usb   = QPushButton(f"🔌  {TR.t('usb_bootable')}")

        for btn in [self._btn_apps, self._btn_perso, self._btn_usb]:
            btn.setFont(CF(13, True))
            btn.setFixedHeight(42)

        self._btn_apps.setStyleSheet(nav_btn_style(True))
        self._btn_perso.setStyleSheet(nav_btn_style(False))
        self._btn_usb.setStyleSheet(nav_btn_style(False))
        self._btn_apps.clicked.connect(lambda: self._switch_tab(0))
        self._btn_perso.clicked.connect(lambda: self._switch_tab(1))
        self._btn_usb.clicked.connect(lambda: self._switch_tab(2))

        nav_h.addWidget(self._btn_apps)
        nav_h.addWidget(self._btn_perso)
        nav_h.addWidget(self._btn_usb)
        h.addWidget(nav_frame)
        h.addStretch()

        # Boutons droite
        _icon_style = f"""QPushButton {{
            background: transparent; color: {C['accent']};
            border: 1.5px solid {C['accent']}; border-radius: 8px;
            padding: 0px; font-size: 18px;
        }}
        QPushButton:hover {{ background: {C['accent']}22; }}
        QPushButton:pressed {{ background: {C['accent']}44; }}"""

        theme_btn = QPushButton("⚙️")
        theme_btn.setFont(QFont("Segoe UI Emoji", 18))
        theme_btn.setFixedSize(38, 38)
        theme_btn.setStyleSheet(_icon_style)
        theme_btn.setToolTip("Changer le thème de couleur")
        theme_btn.clicked.connect(self._open_theme_dialog)
        h.addWidget(theme_btn)

        if UPDATER_AVAILABLE:
            update_btn = QPushButton("🔄")
            update_btn.setFont(QFont("Segoe UI Emoji", 18))
            update_btn.setFixedSize(38, 38)
            update_btn.setStyleSheet(_icon_style)
            update_btn.setToolTip("Vérifier les mises à jour")
            update_btn.clicked.connect(self._open_update_dialog)
            h.addWidget(update_btn)

        self._lang_btn = QPushButton("🇫🇷 FR" if TR.lang == "fr" else "🇬🇧 EN")
        self._lang_btn.setFont(CF(12))
        self._lang_btn.setFixedHeight(38)
        self._lang_btn.setStyleSheet(btn_style(outline=True))
        self._lang_btn.clicked.connect(self._toggle_lang)
        h.addWidget(self._lang_btn)

        about_btn = QPushButton("ℹ")
        about_btn.setFont(CF(13, True))
        about_btn.setFixedSize(38, 38)
        about_btn.setStyleSheet(btn_style(outline=True))
        about_btn.clicked.connect(lambda: AboutDialog(self).exec_())
        h.addWidget(about_btn)

        return header

    # ── Actions ───────────────────────────────────────────────────
    def closeEvent(self, event):
        super().closeEvent(event)

    def _switch_tab(self, idx):
        self._stack.setCurrentIndex(idx)
        self._btn_apps.setStyleSheet(nav_btn_style(idx == 0))
        self._btn_perso.setStyleSheet(nav_btn_style(idx == 1))
        self._btn_usb.setStyleSheet(nav_btn_style(idx == 2))

    def _toggle_lang(self):
        new_lang = "en" if TR.lang == "fr" else "fr"
        TR.set_lang(new_lang)
        APPDATA.set("language", new_lang)
        self._lang_btn.setText("🇫🇷 FR" if new_lang == "fr" else "🇬🇧 EN")
        QMessageBox.information(self, "Info", TR.t("restart_to_apply_lang"))

    def _open_update_dialog(self):
        if UPDATER_AVAILABLE:
            UpdateDialog(self).exec_()

    def _open_theme_dialog(self):
        dlg = ThemeDialog(self)
        dlg.theme_applied.connect(self._refresh_theme)
        dlg.exec_()

    def _refresh_theme(self):
        app     = QApplication.instance()
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
        self.setStyleSheet(global_css() + f"QMainWindow {{ background: {C['bg']}; }}")
        self._build()
        self.show()
