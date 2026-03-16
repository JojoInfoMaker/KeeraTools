import json
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QGridLayout,
    QFileDialog, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

from core import C, TR, APPS_DATA, CAT_ICONS, APP_ICONS
from core.translator import get_winget_id
from ui.styles import CF, btn_style, cat_btn_style
from ui.dialogs.install_dialog import InstallDialog
from workers.icon_loader import IconLoaderThread
from core.translator import get_app_logo_url


# ── AppCard ───────────────────────────────────────────────────────
class AppCard(QFrame):
    """Carré sélectionnable pour une application."""
    clicked = pyqtSignal(str, str)  # (app_name, winget_id)

    def __init__(self, app_name: str, winget_id: str, parent=None):
        super().__init__(parent)
        self.app_name   = app_name
        self.winget_id  = winget_id
        self.is_selected = False
        self.icon_label  = None
        self._icon_thread = None
        self._build()

    def _build(self):
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedSize(150, 170)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)

        logo_url = get_app_logo_url(self.app_name, APPS_DATA)
        if logo_url:
            self._icon_thread = IconLoaderThread(self.app_name, logo_url, 96)
            self._icon_thread.icon_loaded.connect(self._on_icon_loaded)
            self._icon_thread.start()
        else:
            emoji = APP_ICONS.get(self.app_name, "📦")
            self.icon_label.setText(emoji)
            self.icon_label.setFont(QFont("Arial", 48))

        layout.addWidget(self.icon_label)

        name_label = QLabel(self.app_name)
        name_label.setFont(CF(11, True))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"color: {C['text']}; background: transparent;")
        layout.addWidget(name_label)
        layout.addStretch()
        self._update_style()

    def _on_icon_loaded(self, app_name, pixmap):
        if app_name == self.app_name and self.icon_label:
            self.icon_label.setPixmap(pixmap)

    def _update_style(self):
        if self.is_selected:
            self.setStyleSheet(f"""QFrame {{
                background: {C['selected']};
                border: 3px solid {C['success']};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {C['success']};
                background: {C['selected']};
            }}""")
        else:
            self.setStyleSheet(f"""QFrame {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {C['accent']};
                background: {C['surface2']};
            }}""")

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_style()

    def mousePressEvent(self, event):
        self.is_selected = not self.is_selected
        self._update_style()
        self.clicked.emit(self.app_name, self.winget_id)
        super().mousePressEvent(event)


# ── AppsTab ───────────────────────────────────────────────────────
class AppsTab(QWidget):
    def __init__(self):
        super().__init__()
        self._selected       = {}
        self._cat_buttons    = {}
        self._current_cat    = ""
        self._app_cards      = {}
        self._app_cards_list = []
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Panneau gauche (catégories) ───────────────────────────
        left = QFrame()
        left.setFixedWidth(248)
        left.setStyleSheet(f"QFrame {{ background: {C['surface']}; border-right: 1px solid {C['border']}; }}")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(10, 16, 10, 16)
        ll.setSpacing(4)

        cat_title = QLabel(TR.t("Categories"))
        cat_title.setFont(CF(10, True))
        cat_title.setStyleSheet(f"color: {C['muted']}; padding: 4px 8px; letter-spacing: 1px;")
        ll.addWidget(cat_title)

        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cat_scroll.setStyleSheet("background: transparent; border: none;")
        cat_container = QWidget()
        cat_container.setStyleSheet("background: transparent;")
        cat_vbox = QVBoxLayout(cat_container)
        cat_vbox.setContentsMargins(0, 0, 0, 0)
        cat_vbox.setSpacing(2)
        cat_vbox.setAlignment(Qt.AlignTop)

        for cat in APPS_DATA.keys():
            icon = CAT_ICONS.get(cat, "📦")
            btn = QPushButton(f"  {icon}  {cat}")
            btn.setStyleSheet(cat_btn_style(False))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda _, c=cat: self._select_category(c))
            cat_vbox.addWidget(btn)
            self._cat_buttons[cat] = btn

        cat_scroll.setWidget(cat_container)
        ll.addWidget(cat_scroll, 1)

        self._sel_counter = QLabel(TR.t("selected", count=0))
        self._sel_counter.setFont(CF(11, True))
        self._sel_counter.setStyleSheet(
            f"color: {C['accent']}; padding: 7px 10px; background: {C['accent']}18; border-radius: 7px;"
        )
        self._sel_counter.setAlignment(Qt.AlignCenter)
        ll.addWidget(self._sel_counter)
        root.addWidget(left)

        # ── Panneau droit ─────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet(f"background: {C['bg']};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self._cat_header = QFrame()
        self._cat_header.setFixedHeight(60)
        self._cat_header.setStyleSheet(
            f"QFrame {{ background: {C['surface2']}; border-bottom: 1px solid {C['border']}; }}"
        )
        hh = QHBoxLayout(self._cat_header)
        hh.setContentsMargins(22, 0, 22, 0)

        self._cat_label = QLabel(TR.t("select_category"))
        self._cat_label.setFont(CF(14, True))
        self._cat_label.setStyleSheet(f"color: {C['text']};")

        pm_label = QLabel("Gestionnaire:")
        pm_label.setFont(CF(11))
        pm_label.setStyleSheet(f"color: {C['text']};")

        self._pm_selector = QComboBox()
        self._pm_selector.addItems(["Winget", "Chocolatey (NOT WORK / NON FONCTIONNEL)"])
        self._pm_selector.setFont(CF(11))
        self._pm_selector.setFixedWidth(130)
        self._pm_selector.setFixedHeight(36)
        self._pm_selector.setStyleSheet(f"""
            QComboBox {{
                background: {C['bg']}; color: {C['text']};
                border: 1px solid {C['border']}; border-radius: 6px;
                padding: 5px 10px; font-size: 11px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: {C['surface']}; color: {C['text']};
                selection-background-color: {C['accent']};
                border: 1px solid {C['border']};
            }}
        """)

        self._sel_all_btn = QPushButton(TR.t("select_all"))
        self._sel_all_btn.setFont(CF(12))
        self._sel_all_btn.setStyleSheet(btn_style(outline=True))
        self._sel_all_btn.setFixedHeight(36)
        self._sel_all_btn.setVisible(False)
        self._sel_all_btn.clicked.connect(self._toggle_select_all)

        hh.addWidget(self._cat_label)
        hh.addStretch()
        hh.addWidget(pm_label)
        hh.addWidget(self._pm_selector)
        hh.addWidget(self._sel_all_btn)
        rl.addWidget(self._cat_header)

        self._apps_scroll = QScrollArea()
        self._apps_scroll.setWidgetResizable(True)
        self._apps_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._apps_scroll.setStyleSheet(f"background: {C['bg']}; border: none;")

        self._apps_container = QWidget()
        self._apps_container.setStyleSheet(f"background: {C['bg']};")
        self._apps_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._apps_grid = QGridLayout(self._apps_container)
        self._apps_grid.setContentsMargins(22, 18, 22, 18)
        self._apps_grid.setSpacing(20)
        self._apps_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self._apps_scroll.setWidget(self._apps_container)
        rl.addWidget(self._apps_scroll, 1)

        # Barre d'actions
        self._action_bar = QFrame()
        self._action_bar.setFixedHeight(68)
        self._action_bar.setStyleSheet(
            f"QFrame {{ background: {C['surface']}; border-top: 1px solid {C['border']}; }}"
        )
        ah = QHBoxLayout(self._action_bar)
        ah.setContentsMargins(22, 0, 22, 0)
        ah.setSpacing(10)

        self._action_info   = QLabel("")
        self._btn_install   = QPushButton(f"⬇  {TR.t('install')}")
        self._btn_update    = QPushButton(f"↑  {TR.t('update')}")
        self._btn_uninstall = QPushButton("✕  Désinstaller")
        self._btn_export    = QPushButton(TR.t("export"))
        self._btn_import    = QPushButton(TR.t("import"))

        self._action_info.setFont(CF(12))
        self._action_info.setStyleSheet(f"color: {C['muted']};")

        for btn in [self._btn_install, self._btn_update, self._btn_uninstall,
                    self._btn_export, self._btn_import]:
            btn.setFont(CF(12, True))
            btn.setFixedHeight(42)

        self._btn_install.setStyleSheet(btn_style(C["accent"]))
        self._btn_update.setStyleSheet(btn_style(C["warning"]))
        self._btn_uninstall.setStyleSheet(btn_style(C["danger"]))
        self._btn_export.setStyleSheet(btn_style(outline=True))
        self._btn_import.setStyleSheet(btn_style(outline=True))

        self._btn_install.clicked.connect(lambda: self._do_action("install"))
        self._btn_update.clicked.connect(lambda: self._do_action("update"))
        self._btn_uninstall.clicked.connect(lambda: self._do_action("uninstall"))
        self._btn_export.clicked.connect(self._export_selection)
        self._btn_import.clicked.connect(self._import_selection)

        ah.addWidget(self._action_info, 1)
        ah.addWidget(self._btn_export)
        ah.addWidget(self._btn_import)
        ah.addWidget(self._btn_install)
        ah.addWidget(self._btn_update)
        ah.addWidget(self._btn_uninstall)

        self._action_bar.setVisible(True)
        rl.addWidget(self._action_bar)
        root.addWidget(right, 1)

        cats = list(APPS_DATA.keys())
        if cats:
            self._select_category(cats[0])

    # ── Logique ───────────────────────────────────────────────────
    def _select_category(self, cat):
        for c, btn in self._cat_buttons.items():
            btn.setStyleSheet(cat_btn_style(c == cat))
        self._current_cat = cat
        icon = CAT_ICONS.get(cat, "📦")
        self._cat_label.setText(f"{icon}  {cat}")
        self._sel_all_btn.setVisible(True)

        self._app_cards.clear()
        self._app_cards_list.clear()
        while self._apps_grid.count():
            item = self._apps_grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        apps = APPS_DATA.get(cat, {})
        row, col, cols = 0, 0, 5
        for app_name in apps.keys():
            wid  = get_winget_id(app_name, APPS_DATA)
            card = AppCard(app_name, wid)
            if app_name in self._selected:
                card.set_selected(True)
            card.clicked.connect(self._on_card_clicked)
            self._apps_grid.addWidget(card, row, col)
            self._app_cards[app_name] = card
            self._app_cards_list.append(card)
            col += 1
            if col >= cols:
                col = 0
                row += 1

        self._update_counter()

    def _on_card_clicked(self, name, winget_id):
        card = self._app_cards.get(name)
        if not card:
            return
        if card.is_selected:
            self._selected[name] = winget_id
        else:
            self._selected.pop(name, None)
        self._update_counter()

    def _update_counter(self):
        n = len(self._selected)
        self._sel_counter.setText(TR.t("selected", count=n))
        self._action_bar.setVisible(n > 0)
        if n > 0:
            self._action_info.setText(TR.t("selected", count=n))
        cat_apps  = set(APPS_DATA.get(self._current_cat, {}).keys())
        sel_in    = cat_apps & set(self._selected.keys())
        self._sel_all_btn.setText(
            TR.t("deselect_all") if sel_in == cat_apps and cat_apps else TR.t("select_all")
        )

    def _toggle_select_all(self):
        cat_apps = APPS_DATA.get(self._current_cat, {})
        all_sel  = all(n in self._selected for n in cat_apps)
        for card in self._app_cards_list:
            card.set_selected(not all_sel)
            if card.app_name in cat_apps:
                if not all_sel:
                    self._selected[card.app_name] = card.winget_id
                else:
                    self._selected.pop(card.app_name, None)
        self._update_counter()

    def _do_action(self, mode):
        if not self._selected:
            QMessageBox.information(self, "Info", TR.t("no_app_selected"))
            return
        if mode == "uninstall":
            names = ", ".join(list(self._selected.keys())[:4])
            if len(self._selected) > 4:
                names += "…"
            if QMessageBox.question(
                self, "Confirmer",
                f"Désinstaller :\n{names}\n\nContinuer ?",
                QMessageBox.Yes | QMessageBox.No
            ) != QMessageBox.Yes:
                return
        pm = self._pm_selector.currentText().lower()
        InstallDialog(list(self._selected.items()), mode, self, pm).exec_()

    def _export_selection(self):
        if not self._selected:
            QMessageBox.information(self, "Info", TR.t("no_app_selected_export"))
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exporter", "", "Fichier JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._selected, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Info", TR.t("export_success"))

    def _import_selection(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importer", "", "Fichier JSON (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._selected.update(data)
                self._select_category(self._current_cat)
                QMessageBox.information(self, "Info", TR.t("import_success"))
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))