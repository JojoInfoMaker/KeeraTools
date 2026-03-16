import os
import subprocess
import shutil
import winreg
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QComboBox, QMessageBox, QColorDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont

from core import C, TR, APPDATA, APP_NAME
from ui.styles import CF, btn_style


class PersonalizationTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 26)
        layout.setSpacing(18)

        title = QLabel(TR.t("personalization_pc"))
        title.setFont(CF(17, True))
        title.setStyleSheet(f"color: {C['text']};")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(container)
        vbox.setSpacing(16)
        vbox.setContentsMargins(0, 0, 10, 0)
        vbox.setAlignment(Qt.AlignTop)
        vbox.addWidget(self._power_management_card())
        vbox.addWidget(self._fast_startup_card())
        vbox.addWidget(self._mouse_accel_card())
        vbox.addWidget(self._startup_card())
        vbox.addWidget(self._accent_card())
        vbox.addWidget(self._logs_card())
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self._status = QLabel("")
        self._status.setFont(CF(12))
        self._status.setStyleSheet(f"color: {C['success']};")
        layout.addWidget(self._status)

    # ── Helpers ───────────────────────────────────────────────────
    def _card(self, title_text, subtitle=""):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 11px; }}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(12)
        t = QLabel(title_text)
        t.setFont(CF(14, True))
        t.setStyleSheet(f"color: {C['text']};")
        lay.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setFont(CF(12))
            s.setStyleSheet(f"color: {C['muted']};")
            s.setWordWrap(True)
            lay.addWidget(s)
        return card, lay

    def _combo_style(self):
        from ui.styles import _COMFORTAA
        return f"""
            QComboBox {{
                background: {C['surface2']}; color: {C['text']};
                border: 1px solid {C['border']}; border-radius: 7px;
                padding: 7px 14px; font-size: 14px;
                font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif;
            }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
        """

    def _show_status(self, msg, color=None):
        self._status.setText(msg)
        self._status.setStyleSheet(f"color: {color or C['success']};")
        QTimer.singleShot(5000, lambda: self._status.setText(""))

    def _is_laptop(self):
        try:
            result = subprocess.run(
                ["wmic", "path", "Win32_Battery", "get", "BatteryStatus"],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            return len(lines) > 1
        except Exception:
            return False

    # ── Carte alimentation ────────────────────────────────────────
    def _power_management_card(self):
        is_laptop = self._is_laptop()
        card, lay = self._card(
            TR.t("power_management_title"),
            TR.t("power_management_subtitle")
        )
        cs = self._combo_style()

        # Veille ecran
        screen_title = QLabel(TR.t("screen_sleep_title"))
        screen_title.setFont(CF(13, True))
        screen_title.setStyleSheet(f"color: {C['text']};")
        lay.addWidget(screen_title)

        row_screen = QHBoxLayout()
        lbl_screen = QLabel(TR.t("delay_ac"))
        lbl_screen.setFont(CF(12))
        self._screen_combo = QComboBox()
        self._screen_combo.setFont(CF(12))
        self._screen_combo.setStyleSheet(cs)
        items_time = [("1 minute", 1), ("5 minutes", 5), ("10 minutes", 10),
                      ("15 minutes", 15), ("30 minutes", 30), ("1 heure", 60), ("Jamais", 0)]
        self._screen_values = [v for _, v in items_time]
        for label, _ in items_time:
            self._screen_combo.addItem(label + " ▼")
        btn_screen = QPushButton(TR.t("apply_btn"))
        btn_screen.setFont(CF(11, True))
        btn_screen.setStyleSheet(btn_style(C["accent"]))
        btn_screen.clicked.connect(self._apply_screen_sleep)
        row_screen.addWidget(lbl_screen)
        row_screen.addWidget(self._screen_combo)
        row_screen.addWidget(btn_screen)
        row_screen.addStretch()
        lay.addLayout(row_screen)

        # Veille PC
        pc_title = QLabel(TR.t("pc_sleep_title"))
        pc_title.setFont(CF(13, True))
        pc_title.setStyleSheet(f"color: {C['text']};")
        lay.addWidget(pc_title)

        row_pc = QHBoxLayout()
        lbl_pc = QLabel(TR.t("delay_ac"))
        lbl_pc.setFont(CF(12))
        self._pc_combo = QComboBox()
        self._pc_combo.setFont(CF(12))
        self._pc_combo.setStyleSheet(cs)
        self._pc_values = [v for _, v in items_time]
        for label, _ in items_time:
            self._pc_combo.addItem(label + " ▼")
        btn_pc = QPushButton(TR.t("apply_btn"))
        btn_pc.setFont(CF(11, True))
        btn_pc.setStyleSheet(btn_style(C["warning"]))
        btn_pc.clicked.connect(self._apply_pc_sleep)
        row_pc.addWidget(lbl_pc)
        row_pc.addWidget(self._pc_combo)
        row_pc.addWidget(btn_pc)
        row_pc.addStretch()
        lay.addLayout(row_pc)

        # Bouton alimentation PC fixe
        if not is_laptop:
            btn_title = QLabel(TR.t("power_btn_desktop_title"))
            btn_title.setFont(CF(13, True))
            btn_title.setStyleSheet(f"color: {C['text']};")
            lay.addWidget(btn_title)

            row_btn = QHBoxLayout()
            lbl_btn = QLabel(TR.t("action_on_press"))
            lbl_btn.setFont(CF(12))
            self._button_combo = QComboBox()
            self._button_combo.setFont(CF(12))
            self._button_combo.setStyleSheet(cs)
            items_btn = [
                (TR.t("power_action_nothing"),   0),
                (TR.t("power_action_shutdown"),  1),
                (TR.t("power_action_sleep"),     2),
                (TR.t("power_action_hibernate"), 3),
            ]
            self._button_values = [v for _, v in items_btn]
            for label, _ in items_btn:
                self._button_combo.addItem(label + " ▼")
            btn_apply = QPushButton(TR.t("apply_btn"))
            btn_apply.setFont(CF(11, True))
            btn_apply.setStyleSheet(btn_style(C["danger"]))
            btn_apply.clicked.connect(self._apply_button_action)
            row_btn.addWidget(lbl_btn)
            row_btn.addWidget(self._button_combo)
            row_btn.addWidget(btn_apply)
            row_btn.addStretch()
            lay.addLayout(row_btn)

        # Batterie + bouton portable
        if is_laptop:
            battery_title = QLabel(TR.t("battery_sleep_title"))
            battery_title.setFont(CF(13, True))
            battery_title.setStyleSheet(f"color: {C['text']};")
            lay.addWidget(battery_title)

            row_batt_screen = QHBoxLayout()
            lbl_batt_screen = QLabel(TR.t("delay_screen_battery"))
            lbl_batt_screen.setFont(CF(12))
            self._batt_screen_combo = QComboBox()
            self._batt_screen_combo.setFont(CF(12))
            self._batt_screen_combo.setStyleSheet(cs)
            self._batt_screen_values = [v for _, v in items_time]
            for label, _ in items_time:
                self._batt_screen_combo.addItem(label + " ▼")
            btn_batt_screen = QPushButton(TR.t("apply_btn"))
            btn_batt_screen.setFont(CF(11, True))
            btn_batt_screen.setStyleSheet(btn_style(C["success"]))
            btn_batt_screen.clicked.connect(self._apply_batt_screen_sleep)
            row_batt_screen.addWidget(lbl_batt_screen)
            row_batt_screen.addWidget(self._batt_screen_combo)
            row_batt_screen.addWidget(btn_batt_screen)
            row_batt_screen.addStretch()
            lay.addLayout(row_batt_screen)

            row_batt_pc = QHBoxLayout()
            lbl_batt_pc = QLabel(TR.t("delay_pc_battery"))
            lbl_batt_pc.setFont(CF(12))
            self._batt_pc_combo = QComboBox()
            self._batt_pc_combo.setFont(CF(12))
            self._batt_pc_combo.setStyleSheet(cs)
            self._batt_pc_values = [v for _, v in items_time]
            for label, _ in items_time:
                self._batt_pc_combo.addItem(label + " ▼")
            btn_batt_pc = QPushButton(TR.t("apply_btn"))
            btn_batt_pc.setFont(CF(11, True))
            btn_batt_pc.setStyleSheet(btn_style(C["success"]))
            btn_batt_pc.clicked.connect(self._apply_batt_pc_sleep)
            row_batt_pc.addWidget(lbl_batt_pc)
            row_batt_pc.addWidget(self._batt_pc_combo)
            row_batt_pc.addWidget(btn_batt_pc)
            row_batt_pc.addStretch()
            lay.addLayout(row_batt_pc)

            # Bouton alimentation portable
            btn_lp_title = QLabel(TR.t("power_btn_laptop_title"))
            btn_lp_title.setFont(CF(13, True))
            btn_lp_title.setStyleSheet(f"color: {C['text']};")
            lay.addWidget(btn_lp_title)

            items_laptop_btn = [
                (TR.t("power_action_nothing"),   0),
                (TR.t("power_action_sleep"),     2),
                (TR.t("power_action_hibernate"), 3),
                (TR.t("power_action_shutdown"),  1),
            ]

            row_btn_ac = QHBoxLayout()
            lbl_btn_ac = QLabel(TR.t("on_ac"))
            lbl_btn_ac.setFont(CF(12))
            self._laptop_btn_ac_combo = QComboBox()
            self._laptop_btn_ac_combo.setFont(CF(12))
            self._laptop_btn_ac_combo.setStyleSheet(cs)
            self._laptop_btn_ac_values = [v for _, v in items_laptop_btn]
            for label, _ in items_laptop_btn:
                self._laptop_btn_ac_combo.addItem(label + " ▼")
            btn_apply_ac = QPushButton(TR.t("apply_btn"))
            btn_apply_ac.setFont(CF(11, True))
            btn_apply_ac.setStyleSheet(btn_style(C["danger"]))
            btn_apply_ac.clicked.connect(lambda: self._apply_laptop_button("ac"))
            row_btn_ac.addWidget(lbl_btn_ac)
            row_btn_ac.addWidget(self._laptop_btn_ac_combo)
            row_btn_ac.addWidget(btn_apply_ac)
            row_btn_ac.addStretch()
            lay.addLayout(row_btn_ac)

            row_btn_dc = QHBoxLayout()
            lbl_btn_dc = QLabel(TR.t("on_battery"))
            lbl_btn_dc.setFont(CF(12))
            self._laptop_btn_dc_combo = QComboBox()
            self._laptop_btn_dc_combo.setFont(CF(12))
            self._laptop_btn_dc_combo.setStyleSheet(cs)
            self._laptop_btn_dc_values = [v for _, v in items_laptop_btn]
            for label, _ in items_laptop_btn:
                self._laptop_btn_dc_combo.addItem(label + " ▼")
            btn_apply_dc = QPushButton(TR.t("apply_btn"))
            btn_apply_dc.setFont(CF(11, True))
            btn_apply_dc.setStyleSheet(btn_style(C["danger"]))
            btn_apply_dc.clicked.connect(lambda: self._apply_laptop_button("dc"))
            row_btn_dc.addWidget(lbl_btn_dc)
            row_btn_dc.addWidget(self._laptop_btn_dc_combo)
            row_btn_dc.addWidget(btn_apply_dc)
            row_btn_dc.addStretch()
            lay.addLayout(row_btn_dc)

        return card

    def _apply_screen_sleep(self):
        minutes = self._screen_values[self._screen_combo.currentIndex()]
        try:
            subprocess.run(["powercfg", "/change", "monitor-timeout-ac", str(minutes)], capture_output=True)
            self._show_status(f"✓ {self._screen_combo.currentText()}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    def _apply_pc_sleep(self):
        minutes = self._pc_values[self._pc_combo.currentIndex()]
        try:
            result = subprocess.run(["powercfg", "/change", "standby-timeout-ac", str(minutes)], capture_output=True)
            if result.returncode != 0:
                self._show_status(f"✗ powercfg ({result.returncode})", C["danger"])
            else:
                self._show_status(f"✓ {self._pc_combo.currentText()}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    def _apply_button_action(self):
        action = self._button_values[self._button_combo.currentIndex()]
        try:
            result = subprocess.run([
                "powercfg", "/setacvalueindex", "SCHEME_CURRENT",
                "4f971e89-eebd-4455-a8de-9e59040e7347",
                "7648efa3-dd9c-4e3e-b566-50f929386280",
                str(action)
            ], capture_output=True)
            subprocess.run(["powercfg", "/setactive", "SCHEME_CURRENT"], capture_output=True)
            if result.returncode != 0:
                self._show_status(f"✗ powercfg ({result.returncode})", C["danger"])
            else:
                self._show_status(f"✓ {self._button_combo.currentText()}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    def _apply_laptop_button(self, mode: str):
        SUBGROUP = "4f971e89-eebd-4455-a8de-9e59040e7347"
        SETTING  = "7648efa3-dd9c-4e3e-b566-50f929386280"
        if mode == "ac":
            action = self._laptop_btn_ac_values[self._laptop_btn_ac_combo.currentIndex()]
            flag   = "/setacvalueindex"
            label  = self._laptop_btn_ac_combo.currentText()
        else:
            action = self._laptop_btn_dc_values[self._laptop_btn_dc_combo.currentIndex()]
            flag   = "/setdcvalueindex"
            label  = self._laptop_btn_dc_combo.currentText()
        try:
            subprocess.run(["powercfg", flag, "SCHEME_CURRENT", SUBGROUP, SETTING, str(action)], capture_output=True)
            subprocess.run(["powercfg", "/setactive", "SCHEME_CURRENT"], capture_output=True)
            self._show_status(f"✓ {label}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    def _apply_batt_screen_sleep(self):
        minutes = self._batt_screen_values[self._batt_screen_combo.currentIndex()]
        try:
            subprocess.run(["powercfg", "/change", "monitor-timeout-dc", str(minutes)], capture_output=True)
            self._show_status(f"✓ {self._batt_screen_combo.currentText()}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    def _apply_batt_pc_sleep(self):
        minutes = self._batt_pc_values[self._batt_pc_combo.currentIndex()]
        try:
            result = subprocess.run(["powercfg", "/change", "standby-timeout-dc", str(minutes)], capture_output=True)
            if result.returncode != 0:
                self._show_status(f"✗ powercfg ({result.returncode})", C["danger"])
            else:
                self._show_status(f"✓ {self._batt_pc_combo.currentText()}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    # ── Carte démarrage rapide ────────────────────────────────────
    def _fast_startup_card(self):
        card, lay = self._card(
            TR.t("fast_startup_title"),
            TR.t("fast_startup_subtitle")
        )
        row = QHBoxLayout()

        self._fast_startup_lbl = QLabel()
        self._fast_startup_lbl.setFont(CF(12))
        self._fast_startup_lbl.setStyleSheet(f"color: {C['muted']};")
        row.addWidget(self._fast_startup_lbl, 1)

        btn_toggle = QPushButton()
        btn_toggle.setFont(CF(12, True))
        btn_toggle.setFixedHeight(38)

        def _refresh():
            enabled = self._get_fast_startup()
            self._fast_startup_lbl.setText(
                TR.t("fast_startup_enabled") if enabled else TR.t("fast_startup_disabled")
            )
            btn_toggle.setText(TR.t("fast_startup_disable") if enabled else TR.t("fast_startup_enable"))
            btn_toggle.setStyleSheet(btn_style(C["warning"]) if enabled else btn_style(C["success"]))

        def _toggle():
            enabled = self._get_fast_startup()
            self._set_fast_startup(not enabled)
            _refresh()

        btn_toggle.clicked.connect(_toggle)
        row.addWidget(btn_toggle)
        lay.addLayout(row)
        _refresh()
        return card

    def _get_fast_startup(self) -> bool:
        try:
            k = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
                0, winreg.KEY_READ
            )
            val, _ = winreg.QueryValueEx(k, "HiberbootEnabled")
            winreg.CloseKey(k)
            return bool(val)
        except Exception:
            return True

    def _set_fast_startup(self, enable: bool):
        try:
            k = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(k, "HiberbootEnabled", 0, winreg.REG_DWORD, int(enable))
            winreg.CloseKey(k)
            self._show_status(
                TR.t("fast_startup_on") if enable else TR.t("fast_startup_off"),
                C["success"]
            )
        except PermissionError:
            QMessageBox.warning(self, TR.t("permission_denied"),
                TR.t("permission_denied_msg").format(name="HiberbootEnabled"))
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    # ── Carte accélération souris ─────────────────────────────────
    def _mouse_accel_card(self):
        card, lay = self._card(
            TR.t("mouse_accel_title"),
            TR.t("mouse_accel_subtitle")
        )
        row = QHBoxLayout()

        self._mouse_accel_lbl = QLabel()
        self._mouse_accel_lbl.setFont(CF(12))
        self._mouse_accel_lbl.setStyleSheet(f"color: {C['muted']};")
        row.addWidget(self._mouse_accel_lbl, 1)

        btn_toggle = QPushButton()
        btn_toggle.setFont(CF(12, True))
        btn_toggle.setFixedHeight(38)

        def _refresh():
            enabled = self._get_mouse_accel()
            self._mouse_accel_lbl.setText(
                TR.t("mouse_accel_enabled") if enabled else TR.t("mouse_accel_disabled")
            )
            btn_toggle.setText(TR.t("mouse_accel_disable") if enabled else TR.t("mouse_accel_enable"))
            btn_toggle.setStyleSheet(btn_style(C["warning"]) if enabled else btn_style(C["success"]))

        def _toggle():
            enabled = self._get_mouse_accel()
            self._set_mouse_accel(not enabled)
            _refresh()

        btn_toggle.clicked.connect(_toggle)
        row.addWidget(btn_toggle)
        lay.addLayout(row)
        _refresh()
        return card

    def _get_mouse_accel(self) -> bool:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(k, "MouseSpeed")
            winreg.CloseKey(k)
            return str(val) != "0"
        except Exception:
            return True

    def _set_mouse_accel(self, enable: bool):
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(k, "MouseSpeed",      0, winreg.REG_SZ, "1")
                winreg.SetValueEx(k, "MouseThreshold1", 0, winreg.REG_SZ, "6")
                winreg.SetValueEx(k, "MouseThreshold2", 0, winreg.REG_SZ, "10")
            else:
                winreg.SetValueEx(k, "MouseSpeed",      0, winreg.REG_SZ, "0")
                winreg.SetValueEx(k, "MouseThreshold1", 0, winreg.REG_SZ, "0")
                winreg.SetValueEx(k, "MouseThreshold2", 0, winreg.REG_SZ, "0")
            winreg.CloseKey(k)
            import ctypes
            SPI_SETMOUSE = 0x0004
            params = (ctypes.c_int * 3)(0 if not enable else 6, 0 if not enable else 10, 1 if enable else 0)
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETMOUSE, 0, params, 3)
            self._show_status(
                TR.t("mouse_accel_on") if enable else TR.t("mouse_accel_off"),
                C["success"]
            )
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    # ── Carte démarrage Windows ───────────────────────────────────
    def _startup_card(self):
        card, lay = self._card(
            TR.t("startup_windows_title"),
            TR.t("startup_windows_subtitle")
        )

        top_row = QHBoxLayout()
        self._startup_count_lbl = QLabel("")
        self._startup_count_lbl.setFont(CF(11))
        self._startup_count_lbl.setStyleSheet(f"color: {C['muted']};")
        top_row.addWidget(self._startup_count_lbl)
        top_row.addStretch()

        btn_refresh = QPushButton(TR.t("startup_refresh"))
        btn_refresh.setFont(CF(11))
        btn_refresh.setStyleSheet(btn_style(outline=True))
        btn_refresh.setFixedHeight(32)
        btn_refresh.clicked.connect(self._refresh_startup_list)

        btn_tm = QPushButton(TR.t("startup_taskmgr"))
        btn_tm.setFont(CF(11))
        btn_tm.setStyleSheet(btn_style(C["accent"]))
        btn_tm.setFixedHeight(32)
        btn_tm.clicked.connect(lambda: subprocess.Popen(["taskmgr.exe"]))

        top_row.addWidget(btn_refresh)
        top_row.addWidget(btn_tm)
        lay.addLayout(top_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(320)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: 1px solid {C['border']}; border-radius: 8px; background: {C['bg']}; }}
            QWidget {{ background: {C['bg']}; }}
        """)
        self._startup_list_container = QWidget()
        self._startup_list_layout = QVBoxLayout(self._startup_list_container)
        self._startup_list_layout.setContentsMargins(8, 8, 8, 8)
        self._startup_list_layout.setSpacing(6)
        self._startup_list_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self._startup_list_container)
        lay.addWidget(scroll)

        self._refresh_startup_list()
        return card

    def _get_startup_entries(self):
        entries = []
        seen_names = set()

        approved_locations = [
            (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
            (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32"),
            (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"),
        ]
        disabled_names = set()
        for hive, kpath in approved_locations:
            try:
                k = winreg.OpenKey(hive, kpath, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        vname, vdata, _ = winreg.EnumValue(k, i)
                        if isinstance(vdata, bytes) and len(vdata) > 0 and vdata[0] == 3:
                            disabled_names.add(vname.lower())
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(k)
            except Exception:
                pass

        reg_locations = [
            (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Run",     winreg.KEY_READ,                              "Utilisateur"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run",     winreg.KEY_READ | winreg.KEY_WOW64_64KEY,     "Système"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run",     winreg.KEY_READ | winreg.KEY_WOW64_32KEY,     "Système (32)"),
            (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\RunOnce", winreg.KEY_READ,                              "Utilisateur (once)"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", winreg.KEY_READ | winreg.KEY_WOW64_64KEY,     "Système (once)"),
        ]

        for hive, kpath, flags, hive_label in reg_locations:
            try:
                k = winreg.OpenKey(hive, kpath, 0, flags)
                i = 0
                while True:
                    try:
                        vname, vdata, _ = winreg.EnumValue(k, i)
                        key = vname.lower()
                        if key not in seen_names:
                            seen_names.add(key)
                            entries.append({
                                "name": vname, "value": str(vdata),
                                "hive": hive, "key_path": kpath,
                                "hive_label": hive_label,
                                "enabled": key not in disabled_names,
                                "source": "registry",
                            })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(k)
            except Exception:
                pass

        startup_folders = []
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
                               0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(k, "Startup")
            winreg.CloseKey(k)
            startup_folders.append((Path(val), "Utilisateur"))
        except Exception:
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                startup_folders.append((Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup", "Utilisateur"))

        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
                               0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(k, "Common Startup")
            winreg.CloseKey(k)
            startup_folders.append((Path(val), "Système"))
        except Exception:
            prog_data = os.environ.get("PROGRAMDATA", "")
            if prog_data:
                startup_folders.append((Path(prog_data) / r"Microsoft\Windows\Start Menu\Programs\Startup", "Système"))

        for folder, label in startup_folders:
            if not folder.exists():
                continue
            for f in folder.iterdir():
                if f.suffix.lower() in (".lnk", ".url", ".bat", ".cmd", ".exe"):
                    fname = f.stem
                    key   = fname.lower()
                    if key not in seen_names:
                        seen_names.add(key)
                        entries.append({
                            "name": fname, "value": str(f),
                            "hive": None, "key_path": str(folder),
                            "hive_label": label,
                            "enabled": key not in disabled_names,
                            "source": "folder",
                            "folder_path": str(f),
                        })

        entries.sort(key=lambda e: (not e["enabled"], e["name"].lower()))
        return entries

    def _refresh_startup_list(self):
        while self._startup_list_layout.count():
            item = self._startup_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self._get_startup_entries()
        if not entries:
            empty = QLabel(TR.t("startup_none"))
            empty.setFont(CF(12))
            empty.setStyleSheet(f"color: {C['muted']}; padding: 20px;")
            empty.setAlignment(Qt.AlignCenter)
            self._startup_list_layout.addWidget(empty)
            self._startup_count_lbl.setText("")
            return

        enabled_count = sum(1 for e in entries if e["enabled"])
        self._startup_count_lbl.setText(
            TR.t("startup_count").format(count=len(entries), enabled=enabled_count)
        )
        for entry in entries:
            self._startup_list_layout.addWidget(self._make_startup_row(entry))

    def _make_startup_row(self, entry):
        row = QFrame()
        row.setFixedHeight(56)
        is_enabled = entry["enabled"]

        def _style(enabled):
            border = C["success"] if enabled else C["border"]
            bg     = C["surface"] if enabled else C["surface2"]
            return (f"QFrame {{ background: {bg}; border: 1px solid {border}; border-radius: 9px; }}"
                    f"QFrame:hover {{ border-color: {C['accent']}; }}")

        row.setStyleSheet(_style(is_enabled))
        h = QHBoxLayout(row)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(12)

        icon_lbl = QLabel(self._startup_icon(entry["name"]))
        icon_lbl.setFont(QFont("Segoe UI Emoji", 22))
        icon_lbl.setFixedWidth(36)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        h.addWidget(icon_lbl)

        name_lbl = QLabel(entry["name"])
        name_lbl.setFont(CF(12, True))
        name_lbl.setStyleSheet(f"color: {C['text']}; background: transparent; border: none;")
        name_lbl.setToolTip(entry["value"])
        h.addWidget(name_lbl, 1)

        badge = QLabel(entry["hive_label"])
        badge.setFont(CF(9, True))
        badge.setStyleSheet(
            f"background: {C['accent']}22; color: {C['accent']}; "
            f"border: 1px solid {C['accent']}44; border-radius: 8px; padding: 2px 8px;"
        )
        badge.setFixedHeight(22)
        h.addWidget(badge)

        toggle_btn = QPushButton(TR.t("startup_active") if is_enabled else TR.t("startup_inactive"))
        toggle_btn.setFont(CF(11, True))
        toggle_btn.setFixedSize(90, 34)
        toggle_btn.setStyleSheet(btn_style(C["success"]) if is_enabled else btn_style(outline=True))
        toggle_btn.setCursor(Qt.PointingHandCursor)

        def _toggle(btn=toggle_btn, e=entry, r=row, s=_style):
            self._toggle_startup_entry(e, btn, r, s)

        toggle_btn.clicked.connect(_toggle)
        h.addWidget(toggle_btn)
        return row

    def _startup_icon(self, name: str) -> str:
        n = name.lower()
        mapping = [
            (["steam"],                                     "🎮"),
            (["epic", "epicgames"],                        "🎮"),
            (["gog", "galaxy"],                            "🎮"),
            (["ubisoft", "uplay"],                         "🎮"),
            (["battle.net", "battlenet"],                  "🎮"),
            (["origin", "ea "],                            "🎮"),
            (["xbox"],                                     "🎮"),
            (["discord"],                                  "💬"),
            (["whatsapp"],                                 "💬"),
            (["telegram"],                                 "✈️"),
            (["signal"],                                   "💬"),
            (["skype"],                                    "📞"),
            (["teams", "msteams"],                         "👥"),
            (["zoom"],                                     "📹"),
            (["slack"],                                    "💼"),
            (["chrome"],                                   "🔵"),
            (["firefox"],                                  "🦊"),
            (["brave"],                                    "🦁"),
            (["edge", "msedge"],                           "🌐"),
            (["opera"],                                    "🔴"),
            (["tor"],                                      "🧅"),
            (["onedrive"],                                 "☁️"),
            (["dropbox"],                                  "📦"),
            (["googledrive", "google drive"],              "🟡"),
            (["icloud"],                                   "☁️"),
            (["spotify"],                                  "🎵"),
            (["itunes"],                                   "🎵"),
            (["vlc"],                                      "📺"),
            (["obs"],                                      "🎥"),
            (["defender", "msmpeng", "securityhealth"],    "🛡️"),
            (["avast", "avg", "bitdefender", "kaspersky",
              "malwarebytes", "norton", "eset", "mcafee"],  "🛡️"),
            (["nvidia", "nvcplui", "nvdisplay"],           "🖥️"),
            (["amd", "radeon"],                            "🔴"),
            (["intel", "igcc"],                            "🔵"),
            (["realtek"],                                  "🔊"),
            (["logitech", "lghub"],                        "🖱️"),
            (["razer"],                                    "🐍"),
            (["corsair", "icue"],                          "⌨️"),
            (["outlook"],                                  "📧"),
            (["word"],                                     "📝"),
            (["excel"],                                    "📊"),
            (["copilot"],                                  "🤖"),
            (["chatgpt"],                                  "🤖"),
            (["notion"],                                   "📓"),
            (["obsidian"],                                 "🟣"),
            (["powertoys"],                                "⚙️"),
            (["update", "updater", "autoupdate"],          "🔄"),
            (["vscode", "code"],                           "💜"),
            (["docker"],                                   "🐳"),
            (["keera", APP_NAME.lower()],                  "⚙️"),
        ]
        for keys, icon in mapping:
            if any(k in n for k in keys):
                return icon
        return "🖥️"

    def _toggle_startup_entry(self, entry, btn, row, style_fn):
        is_enabled = entry["enabled"]

        if entry.get("source") == "folder":
            folder_path    = Path(entry.get("folder_path", ""))
            disabled_folder = folder_path.parent / "disabled_startup_backup"
            try:
                if is_enabled:
                    disabled_folder.mkdir(exist_ok=True)
                    dest = disabled_folder / folder_path.name
                    shutil.move(str(folder_path), str(dest))
                    entry["folder_path"] = str(dest)
                    entry["enabled"] = False
                    btn.setText(TR.t("startup_inactive"))
                    btn.setStyleSheet(btn_style(outline=True))
                    self._show_status(f"✓ {entry['name']}", C["warning"])
                else:
                    dest = folder_path.parent.parent / folder_path.name
                    shutil.move(str(folder_path), str(dest))
                    entry["folder_path"] = str(dest)
                    entry["enabled"] = True
                    btn.setText(TR.t("startup_active"))
                    btn.setStyleSheet(btn_style(C["success"]))
                    self._show_status(f"✓ {entry['name']}", C["success"])
                row.setStyleSheet(style_fn(entry["enabled"]))
                self._refresh_startup_count()
            except PermissionError:
                QMessageBox.warning(self, TR.t("permission_denied"),
                    TR.t("permission_denied_msg").format(name=entry['name']))
            except Exception as e:
                self._show_status(f"✗ {e}", C["danger"])
            return

        approved_key_map = {
            winreg.HKEY_CURRENT_USER:  r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
            winreg.HKEY_LOCAL_MACHINE: r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
        }
        try:
            approved_path = approved_key_map.get(entry["hive"])
            if not approved_path:
                raise Exception("Clé de registre non supportée")
            try:
                k = winreg.OpenKey(entry["hive"], approved_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
            except FileNotFoundError:
                k = winreg.CreateKey(entry["hive"], approved_path)

            if is_enabled:
                winreg.SetValueEx(k, entry["name"], 0, winreg.REG_BINARY, bytes([3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
                entry["enabled"] = False
                btn.setText(TR.t("startup_inactive"))
                btn.setStyleSheet(btn_style(outline=True))
                self._show_status(f"✓ {entry['name']}", C["warning"])
            else:
                winreg.SetValueEx(k, entry["name"], 0, winreg.REG_BINARY, bytes([2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
                entry["enabled"] = True
                btn.setText(TR.t("startup_active"))
                btn.setStyleSheet(btn_style(C["success"]))
                self._show_status(f"✓ {entry['name']}", C["success"])
            winreg.CloseKey(k)
            row.setStyleSheet(style_fn(entry["enabled"]))
            self._refresh_startup_count()

        except PermissionError:
            QMessageBox.warning(self, TR.t("permission_denied"),
                TR.t("permission_denied_system").format(name=entry['name']))
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    def _refresh_startup_count(self):
        entries       = self._get_startup_entries()
        enabled_count = sum(1 for e in entries if e["enabled"])
        self._startup_count_lbl.setText(
            TR.t("startup_count").format(count=len(entries), enabled=enabled_count)
        )

    # ── Carte accent ──────────────────────────────────────────────
    def _accent_card(self):
        card, lay = self._card(
            TR.t("accent_title"),
            TR.t("accent_subtitle")
        )
        row = QHBoxLayout()

        self._accent_preview = QLabel()
        self._accent_preview.setFixedSize(36, 36)
        self._accent_preview.setStyleSheet(
            f"background: {C['accent']}; border-radius: 7px; border: 1px solid {C['border']};"
        )

        self._accent_label = QLabel(C["accent"])
        self._accent_label.setFont(CF(13))
        self._accent_label.setStyleSheet(f"color: {C['text']};")

        btn_pick = QPushButton(TR.t("accent_pick"))
        btn_pick.setFont(CF(12, True))
        btn_pick.setStyleSheet(btn_style(C["accent"]))
        btn_pick.setFixedHeight(38)

        def pick_color():
            color = QColorDialog.getColor(QColor(C["accent"]), None, TR.t("accent_title"))
            if color.isValid():
                hex_color = color.name()
                C["accent"] = hex_color
                APPDATA.set("accent_color", hex_color)
                self._accent_preview.setStyleSheet(
                    f"background: {hex_color}; border-radius: 7px; border: 1px solid {C['border']};"
                )
                self._accent_label.setText(hex_color)
                self._show_status(TR.t("accent_saved").format(color=hex_color), C["success"])

        btn_pick.clicked.connect(pick_color)
        row.addWidget(self._accent_preview)
        row.addWidget(self._accent_label)
        row.addWidget(btn_pick)
        row.addStretch()
        lay.addLayout(row)
        return card

    # ── Carte logs ────────────────────────────────────────────────
    def _logs_card(self):
        card, lay = self._card(
            TR.t("logs_title"),
            TR.t("logs_subtitle")
        )
        row       = QHBoxLayout()
        logs_path = str(APPDATA.logs_dir)

        lbl = QLabel(logs_path)
        lbl.setFont(CF(11))
        lbl.setStyleSheet(f"color: {C['muted']}; font-family: Consolas, monospace;")
        lbl.setWordWrap(True)

        btn_open = QPushButton(TR.t("logs_open"))
        btn_open.setFont(CF(12, True))
        btn_open.setStyleSheet(btn_style(outline=True))
        btn_open.setFixedHeight(38)
        btn_open.clicked.connect(lambda: subprocess.Popen(f'explorer "{logs_path}"'))

        row.addWidget(lbl, 1)
        row.addWidget(btn_open)
        lay.addLayout(row)
        return card