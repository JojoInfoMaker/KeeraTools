import webbrowser
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap

from core import TR, C, APP_NAME
from core.config import ICON_SMALL, ICON_BIG
from ui.styles import CF, btn_style


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"À propos de {APP_NAME} ™")
        self.setMinimumSize(580, 480)
        self.resize(620, 520)
        self.setStyleSheet(f"background: {C['surface']}; color: {C['text']};")
        if ICON_SMALL.exists():
            self.setWindowIcon(QIcon(str(ICON_SMALL)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(20)

        if ICON_BIG.exists():
            logo_lbl = QLabel()
            px = QPixmap(str(ICON_BIG)).scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(px)
            logo_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_lbl)

        name_lbl = QLabel(f"{APP_NAME} ™")
        name_lbl.setFont(CF(22, True))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(f"color: {C['accent']};")
        layout.addWidget(name_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setMinimumHeight(140)

        text_container = QWidget()
        text_container.setStyleSheet("background: transparent;")
        text_lay = QVBoxLayout(text_container)
        text_lay.setContentsMargins(0, 0, 0, 0)

        text = QLabel(TR.t("about_text").replace("KeeraTools", APP_NAME))
        text.setFont(CF(13))
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet(f"color: {C['muted']}; line-height: 1.7; background: transparent;")
        text_lay.addWidget(text)
        scroll.setWidget(text_container)
        layout.addWidget(scroll, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {C['border']}; background: {C['border']}; max-height: 1px;")
        layout.addWidget(sep)

        links_row = QHBoxLayout()
        links_row.setSpacing(14)

        btn_github = QPushButton("  GitHub")
        btn_github.setFont(CF(13, True))
        btn_github.setFixedHeight(44)
        btn_github.setStyleSheet(btn_style(outline=True))
        btn_github.setCursor(Qt.PointingHandCursor)
        btn_github.clicked.connect(lambda: webbrowser.open("https://github.com/JojoInfoMaker/KeeraTools"))

        btn_discord = QPushButton("  Discord")
        btn_discord.setFont(CF(13, True))
        btn_discord.setFixedHeight(44)
        btn_discord.setStyleSheet(btn_style("#5865F2"))
        btn_discord.setCursor(Qt.PointingHandCursor)
        btn_discord.clicked.connect(lambda: webbrowser.open("https://discord.gg/UJzAqHPCs8"))

        links_row.addWidget(btn_github)
        links_row.addWidget(btn_discord)
        layout.addLayout(links_row)

        btn = QPushButton("Fermer")
        btn.setFont(CF(13, True))
        btn.setStyleSheet(btn_style(C["accent"]))
        btn.setFixedHeight(42)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
