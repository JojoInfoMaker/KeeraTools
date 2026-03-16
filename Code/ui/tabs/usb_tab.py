from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QGraphicsBlurEffect
)
from PyQt5.QtCore import Qt

from core import C, TR, APP_VERSION
from ui.styles import CF


class USBBootableTab(QWidget):
    """Onglet Clé USB — Coming Soon avec fond flou."""

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main_frame = QFrame()
        main_frame.setStyleSheet(f"QFrame {{ background: {C['bg']}; }}")
        main_lay = QVBoxLayout(main_frame)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Arrière-plan flou avec fausses cartes
        blur_zone = QFrame()
        blur_zone.setStyleSheet(f"QFrame {{ background: {C['surface']}; }}")
        blur_lay = QVBoxLayout(blur_zone)
        blur_lay.setContentsMargins(30, 30, 30, 30)
        blur_lay.setSpacing(20)
        blur_lay.setAlignment(Qt.AlignTop)

        cards_data = [
            ("💾  Sélectionner une clé USB",  "Choisissez le périphérique USB"),
            ("🎯  Mode de création",           "Windows Bootable / Linux Bootable"),
            ("📀  Image ISO",                  "Fichier local ou téléchargement"),
            ("⚙️  Options avancées",           "Système de fichiers et cluster"),
        ]

        for title, subtitle in cards_data:
            card = QFrame()
            card.setFixedHeight(80)
            card.setStyleSheet(
                f"QFrame {{ background: {C['surface2']}; "
                f"border: 1px solid {C['border']}; border-radius: 10px; }}"
            )
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(18, 12, 18, 12)
            card_lay.setSpacing(4)

            t = QLabel(title)
            t.setFont(CF(13, True))
            t.setStyleSheet(f"color: {C['text']};")
            card_lay.addWidget(t)

            s = QLabel(subtitle)
            s.setFont(CF(11))
            s.setStyleSheet(f"color: {C['muted']};")
            card_lay.addWidget(s)

            blur_lay.addWidget(card)

        blur_lay.addStretch()

        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(12)
        blur_zone.setGraphicsEffect(blur_effect)
        main_lay.addWidget(blur_zone, 1)

        # Overlay centré avec le message
        overlay = QFrame()
        overlay.setStyleSheet("background: transparent;")
        overlay_lay = QVBoxLayout(overlay)
        overlay_lay.setAlignment(Qt.AlignCenter)

        msg = QLabel(TR.t("clefbootabletext"))
        msg.setFont(CF(16, True))
        msg.setAlignment(Qt.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {C['accent']}; background: transparent;")
        msg.setMaximumWidth(600)
        overlay_lay.addWidget(msg, alignment=Qt.AlignCenter)

        main_lay.addWidget(overlay, 1)
        layout.addWidget(main_frame, 1)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet(
            f"QFrame {{ background: {C['surface']}; border-top: 1px solid {C['border']}; }}"
        )
        footer_lay = QHBoxLayout(footer)
        footer_lay.setContentsMargins(22, 0, 22, 0)

        footer_text = QLabel(f"Fonctionnalité en développement • V{APP_VERSION}")
        footer_text.setFont(CF(10))
        footer_text.setStyleSheet(f"color: {C['muted']};")
        footer_lay.addStretch()
        footer_lay.addWidget(footer_text)
        footer_lay.addStretch()
        layout.addWidget(footer)