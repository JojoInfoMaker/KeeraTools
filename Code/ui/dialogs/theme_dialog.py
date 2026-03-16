from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QWidget, QColorDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

from core import TR, C, APPDATA, THEMES, THEME_COLOR_LABELS, apply_theme
from core.config import ICON_SMALL
from ui.styles import CF, btn_style


class ThemeDialog(QDialog):
    theme_applied = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙  Thème & Couleurs — KeeraTools")
        self.setMinimumSize(720, 560)
        self.setModal(True)
        self.setStyleSheet(f"background: {C['surface']}; color: {C['text']};")
        if ICON_SMALL.exists():
            self.setWindowIcon(QIcon(str(ICON_SMALL)))
        self._current_theme_key = APPDATA.get("theme", "dark")
        self._custom_colors = dict(THEMES["custom"])
        saved_custom = APPDATA.get("custom_theme", {})
        if saved_custom:
            self._custom_colors.update(saved_custom)
        self._color_pickers = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel("🎨  Choisissez votre thème")
        title.setFont(CF(16, True))
        title.setStyleSheet(f"color: {C['text']};")
        root.addWidget(title)

        sub = QLabel("Le thème sera appliqué immédiatement après confirmation.")
        sub.setFont(CF(11))
        sub.setStyleSheet(f"color: {C['muted']};")
        root.addWidget(sub)

        themes_frame = QFrame()
        themes_frame.setStyleSheet(
            f"QFrame {{ background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 10px; }}"
        )
        themes_grid_lay = QGridLayout(themes_frame)
        themes_grid_lay.setContentsMargins(16, 14, 16, 14)
        themes_grid_lay.setSpacing(10)

        self._theme_btns = {}
        preset_keys = [k for k in THEMES if k != "custom"]
        for i, key in enumerate(preset_keys):
            btn = self._make_theme_btn(key, THEMES[key])
            self._theme_btns[key] = btn
            themes_grid_lay.addWidget(btn, i // 3, i % 3)

        root.addWidget(themes_frame)

        custom_label = QLabel("🎨  Mode Personnalisé — Couleur par couleur")
        custom_label.setFont(CF(13, True))
        custom_label.setStyleSheet(f"color: {C['text']};")
        root.addWidget(custom_label)

        custom_scroll = QScrollArea()
        custom_scroll.setWidgetResizable(True)
        custom_scroll.setFixedHeight(200)
        custom_scroll.setStyleSheet(
            f"background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 8px;"
        )
        custom_container = QWidget()
        custom_container.setStyleSheet(f"background: {C['bg']};")
        custom_grid = QGridLayout(custom_container)
        custom_grid.setContentsMargins(12, 10, 12, 10)
        custom_grid.setSpacing(8)

        color_keys = list(THEME_COLOR_LABELS.keys())
        for i, key in enumerate(color_keys):
            row_lay = QHBoxLayout()
            lbl = QLabel(THEME_COLOR_LABELS[key])
            lbl.setFont(CF(11))
            lbl.setFixedWidth(170)
            lbl.setStyleSheet(f"color: {C['text']};")

            preview = QLabel()
            preview.setFixedSize(28, 28)
            current_val = self._custom_colors.get(key, C.get(key, "#888888"))
            preview.setStyleSheet(
                f"background: {current_val}; border-radius: 5px; border: 1px solid {C['border']};"
            )
            preview.setCursor(Qt.PointingHandCursor)

            hex_lbl = QLabel(current_val)
            hex_lbl.setFont(CF(10))
            hex_lbl.setStyleSheet(f"color: {C['muted']};")
            hex_lbl.setFixedWidth(80)

            def make_picker(k, prev_widget, hex_widget):
                def pick():
                    current = self._custom_colors.get(k, "#888888")
                    color = QColorDialog.getColor(
                        QColor(current), self, f"Couleur : {THEME_COLOR_LABELS.get(k, k)}"
                    )
                    if color.isValid():
                        hex_val = color.name()
                        self._custom_colors[k] = hex_val
                        prev_widget.setStyleSheet(
                            f"background: {hex_val}; border-radius: 5px; border: 1px solid {C['border']};"
                        )
                        hex_widget.setText(hex_val)
                        self._select_theme("custom")
                return pick

            preview.mousePressEvent = lambda e, k=key, p=preview, h=hex_lbl: make_picker(k, p, h)()
            self._color_pickers[key] = (preview, hex_lbl)

            row_lay.addWidget(lbl)
            row_lay.addWidget(preview)
            row_lay.addWidget(hex_lbl)
            row_lay.addStretch()
            custom_grid.addLayout(row_lay, i // 2, i % 2)

        custom_scroll.setWidget(custom_container)
        root.addWidget(custom_scroll)

        copy_btn = QPushButton("📋  Copier le thème actif comme base personnalisée")
        copy_btn.setFont(CF(11))
        copy_btn.setStyleSheet(btn_style(outline=True))
        copy_btn.setFixedHeight(34)
        copy_btn.clicked.connect(self._copy_active_to_custom)
        root.addWidget(copy_btn, alignment=Qt.AlignLeft)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setFont(CF(12))
        btn_cancel.setStyleSheet(btn_style(outline=True))
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.reject)

        self._btn_apply = QPushButton("✓  Appliquer le thème")
        self._btn_apply.setFont(CF(13, True))
        self._btn_apply.setStyleSheet(btn_style(C["accent"]))
        self._btn_apply.setFixedHeight(40)
        self._btn_apply.clicked.connect(self._apply)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self._btn_apply)
        root.addLayout(btn_row)

        self._select_theme(self._current_theme_key)

    def _make_theme_btn(self, key, theme):
        btn = QFrame()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(190, 70)
        btn.setProperty("theme_key", key)

        lay = QHBoxLayout(btn)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(10)

        preview_widget = QWidget()
        preview_widget.setFixedSize(36, 36)
        preview_widget.setStyleSheet(
            f"background: {theme.get('bg', '#000')}; border-radius: 6px; "
            f"border: 2px solid {theme.get('border', '#333')};"
        )
        dot = QLabel()
        dot.setParent(preview_widget)
        dot.setFixedSize(14, 14)
        dot.move(11, 11)
        dot.setStyleSheet(f"background: {theme.get('accent', '#5B6CF9')}; border-radius: 7px;")

        name_lbl = QLabel(theme.get("name", key))
        name_lbl.setFont(CF(11, True))
        name_lbl.setStyleSheet(f"color: {C['text']}; background: transparent;")

        lay.addWidget(preview_widget)
        lay.addWidget(name_lbl)
        lay.addStretch()

        btn.mousePressEvent = lambda e, k=key: self._select_theme(k)
        self._update_btn_style(btn, key == self._current_theme_key)
        return btn

    def _update_btn_style(self, btn, active):
        if active:
            btn.setStyleSheet(
                f"QFrame {{ background: {C['selected']}; border: 2px solid {C['accent']}; border-radius: 9px; }}"
            )
        else:
            btn.setStyleSheet(
                f"QFrame {{ background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 9px; }}"
                f"QFrame:hover {{ border: 1px solid {C['accent']}55; background: {C['surface2']}; }}"
            )

    def _select_theme(self, key):
        self._current_theme_key = key
        for k, btn in self._theme_btns.items():
            self._update_btn_style(btn, k == key)

    def _copy_active_to_custom(self):
        active_key = APPDATA.get("theme", "dark")
        base = THEMES.get(active_key, THEMES["dark"])
        for key in THEME_COLOR_LABELS.keys():
            val = base.get(key, C.get(key, "#888888"))
            self._custom_colors[key] = val
            if key in self._color_pickers:
                prev, hex_lbl = self._color_pickers[key]
                prev.setStyleSheet(
                    f"background: {val}; border-radius: 5px; border: 1px solid {C['border']};"
                )
                hex_lbl.setText(val)
        self._select_theme("custom")

    def _apply(self):
        new_theme_key = self._current_theme_key
        custom_data = {}
        if new_theme_key == "custom":
            custom_data = {k: v for k, v in self._custom_colors.items() if k != "name"}
            THEMES["custom"].update(custom_data)
            APPDATA.set("custom_theme", custom_data)

        apply_theme(new_theme_key, custom_data if new_theme_key == "custom" else None)
        APPDATA.set("theme", new_theme_key)
        if new_theme_key != "custom":
            APPDATA.set("accent_color", C["accent"])

        self.theme_applied.emit()
        self.accept()
