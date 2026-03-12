import sys
import os
import json
import subprocess
import re
from pathlib import Path
import ctypes
import winreg
import urllib.request
import urllib.error
from urllib.parse import urlparse
import logging
import shutil
import tempfile
import time
from urllib.request import urlopen, Request

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QCheckBox,
    QStackedWidget, QSizePolicy, QFileDialog, QMessageBox,
    QTextEdit, QDialog, QProgressBar, QComboBox, QSpinBox,
    QRadioButton, QButtonGroup, QTabWidget, QGridLayout,
    QProgressDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl
from PyQt5.QtGui import (
    QFont, QIcon, QPixmap, QColor, QPalette, QFontDatabase
)

# Le système de mise à jour est intégré directement
UPDATER_AVAILABLE = True

# ══════════════════════════════════════════════════════════════════
#  CHEMINS
# ══════════════════════════════════════════════════════════════════
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data"
APPS_JSON  = DATA_DIR / "apps.json"
TRAD_JSON  = DATA_DIR / "traduction.json"
ICON_BIG   = DATA_DIR / "icontest.png"
ICON_SMALL = DATA_DIR / "icon.ico"
FONT_PATH  = DATA_DIR / "Comfortaa-Regular.ttf"

# ══════════════════════════════════════════════════════════════════
#  APPDATA MANAGER  –  %LOCALAPPDATA%\KeeraTools
# ══════════════════════════════════════════════════════════════════
import datetime
import logging

class AppDataManager:
    """Gère le dossier %LOCALAPPDATA%\\KeeraTools et ses sous-dossiers."""

    APP_FOLDER   = "KeeraTools"
    LOG_SUBDIR   = "logs"
    SETTINGS_FILE = "settings.json"

    # Clés et valeurs par défaut des paramètres
    DEFAULT_SETTINGS = {
        "language": "fr",
        "accent_color": "#5B6CF9",
        "theme": "dark",
        "custom_theme": {},
    }

    def __init__(self):
        local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        self.root    = local_app_data / self.APP_FOLDER
        self.logs_dir = self.root / self.LOG_SUBDIR
        self.settings_path = self.root / self.SETTINGS_FILE

        self._first_run = not self.root.exists()
        self._ensure_dirs()
        self.settings = self._load_settings()
        self._setup_logger()

    # ── Initialisation ────────────────────────────────────────────
    def _ensure_dirs(self):
        """Crée le dossier racine et les sous-dossiers si absents."""
        self.root.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def _setup_logger(self):
        """Configure le logger Python vers un fichier daté dans logs/."""
        today = datetime.date.today().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"install_{today}.log"
        logging.basicConfig(
            filename=str(log_file),
            filemode="a",
            format="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
            level=logging.DEBUG,
            encoding="utf-8",
        )
        self._logger = logging.getLogger("KeeraTools")
        if self._first_run:
            self._logger.info("=== Premier démarrage — dossier KeeraTools créé ===")

    # ── Settings ──────────────────────────────────────────────────
    def _load_settings(self) -> dict:
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Fusionner avec les defaults pour les clés manquantes
                merged = dict(self.DEFAULT_SETTINGS)
                merged.update(data)
                return merged
            except Exception as e:
                print(f"[WARN] Impossible de lire settings.json : {e}")
        return dict(self.DEFAULT_SETTINGS)

    def save_settings(self):
        """Persiste les settings sur disque."""
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] Impossible d'écrire settings.json : {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    # ── Logs d'installation ───────────────────────────────────────
    def log_install(self, message: str, level: str = "info"):
        """Écrit un message dans le fichier de log d'installation du jour."""
        getattr(self._logger, level, self._logger.info)(message)

    @property
    def is_first_run(self) -> bool:
        return self._first_run


# Instance globale — initialisée avant tout le reste de l'UI
APPDATA = AppDataManager()


# ══════════════════════════════════════════════════════════════════
#  POLICE COMFORTAA
# ══════════════════════════════════════════════════════════════════
_COMFORTAA = "Segoe UI"

def load_comfortaa():
    global _COMFORTAA
    if FONT_PATH.exists():
        fid = QFontDatabase.addApplicationFont(str(FONT_PATH))
        if fid != -1:
            families = QFontDatabase.applicationFontFamilies(fid)
            if families:
                _COMFORTAA = families[0]

def CF(size, bold=False):
    f = QFont(_COMFORTAA, size)
    f.setBold(bold)
    return f

# ══════════════════════════════════════════════════════════════════
#  PALETTE
# ══════════════════════════════════════════════════════════════════
C = {
    "bg"       : "#0C0E14",
    "surface"  : "#13161F",
    "surface2" : "#181C27",
    "border"   : "#232840",
    "accent"   : "#5B6CF9",
    "accent2"  : "#7C3AED",
    "success"  : "#22C55E",
    "warning"  : "#F59E0B",
    "danger"   : "#EF4444",
    "text"     : "#E8ECFF",
    "muted"    : "#5A6080",
    "selected" : "#1E2340",
}

# ══════════════════════════════════════════════════════════════════
#  THÈMES PRÉDÉFINIS
# ══════════════════════════════════════════════════════════════════
THEMES = {
    "dark": {
        "name": "🌑  Dark (Défaut)",
        "bg"       : "#0C0E14",
        "surface"  : "#13161F",
        "surface2" : "#181C27",
        "border"   : "#232840",
        "accent"   : "#5B6CF9",
        "accent2"  : "#7C3AED",
        "success"  : "#22C55E",
        "warning"  : "#F59E0B",
        "danger"   : "#EF4444",
        "text"     : "#E8ECFF",
        "muted"    : "#5A6080",
        "selected" : "#1E2340",
    },
    "white": {
        "name": "☀️  Light / White",
        "bg"       : "#F4F6FB",
        "surface"  : "#FFFFFF",
        "surface2" : "#EEF1F8",
        "border"   : "#D0D5E8",
        "accent"   : "#5B6CF9",
        "accent2"  : "#7C3AED",
        "success"  : "#16A34A",
        "warning"  : "#D97706",
        "danger"   : "#DC2626",
        "text"     : "#1A1D2E",
        "muted"    : "#7A82A6",
        "selected" : "#E0E4F8",
    },
    "nord": {
        "name": "🧊  Nord / Arctic",
        "bg"       : "#1E2130",
        "surface"  : "#242837",
        "surface2" : "#2C3147",
        "border"   : "#3B4266",
        "accent"   : "#88C0D0",
        "accent2"  : "#5E81AC",
        "success"  : "#A3BE8C",
        "warning"  : "#EBCB8B",
        "danger"   : "#BF616A",
        "text"     : "#ECEFF4",
        "muted"    : "#7080A0",
        "selected" : "#2E3550",
    },
    "cyberpunk": {
        "name": "⚡  Cyberpunk / Neon",
        "bg"       : "#060810",
        "surface"  : "#0D0F1A",
        "surface2" : "#121525",
        "border"   : "#1A1F3A",
        "accent"   : "#00FFB2",
        "accent2"  : "#FF2D78",
        "success"  : "#00FFB2",
        "warning"  : "#FFD700",
        "danger"   : "#FF2D78",
        "text"     : "#E0FFF6",
        "muted"    : "#3A7060",
        "selected" : "#0D2020",
    },
    "mocha": {
        "name": "☕  Mocha / Warm",
        "bg"       : "#1A1512",
        "surface"  : "#231E1A",
        "surface2" : "#2C261F",
        "border"   : "#40342A",
        "accent"   : "#E08C4A",
        "accent2"  : "#C0522A",
        "success"  : "#7DBF72",
        "warning"  : "#E8C36A",
        "danger"   : "#D9534F",
        "text"     : "#F5ECD7",
        "muted"    : "#8A7060",
        "selected" : "#2A2018",
    },
    "midnight": {
        "name": "🌌  Midnight Purple",
        "bg"       : "#0D0B16",
        "surface"  : "#141020",
        "surface2" : "#1A152A",
        "border"   : "#2A2045",
        "accent"   : "#A855F7",
        "accent2"  : "#EC4899",
        "success"  : "#34D399",
        "warning"  : "#FBBF24",
        "danger"   : "#F87171",
        "text"     : "#F3EAFF",
        "muted"    : "#6050A0",
        "selected" : "#1E1535",
    },
    "custom": {
        "name": "🎨  Personnalisé",
        # Will be populated from saved settings
        "bg"       : "#0C0E14",
        "surface"  : "#13161F",
        "surface2" : "#181C27",
        "border"   : "#232840",
        "accent"   : "#5B6CF9",
        "accent2"  : "#7C3AED",
        "success"  : "#22C55E",
        "warning"  : "#F59E0B",
        "danger"   : "#EF4444",
        "text"     : "#E8ECFF",
        "muted"    : "#5A6080",
        "selected" : "#1E2340",
    },
}

THEME_COLOR_LABELS = {
    "bg":       "Fond principal",
    "surface":  "Surface / Panneaux",
    "surface2": "Surface secondaire",
    "border":   "Bordures",
    "accent":   "Couleur d'accent",
    "accent2":  "Accent secondaire",
    "success":  "Succès (vert)",
    "warning":  "Avertissement (orange)",
    "danger":   "Danger (rouge)",
    "text":     "Texte principal",
    "muted":    "Texte discret",
    "selected": "Fond sélection",
}

def apply_theme(theme_key: str, custom_overrides: dict = None):
    """Applique un thème dans la palette C globale."""
    theme_data = THEMES.get(theme_key, THEMES["dark"]).copy()
    if theme_key == "custom" and custom_overrides:
        theme_data.update(custom_overrides)
    for k, v in theme_data.items():
        if k != "name":
            C[k] = v

def apply_saved_settings():
    """Charge langue, thème et couleur d'accent depuis les settings persistants."""
    saved_lang = APPDATA.get("language")
    if saved_lang:
        TR.set_lang(saved_lang)
    saved_theme = APPDATA.get("theme", "dark")
    custom_data = APPDATA.get("custom_theme", {})
    # Merge custom theme saved data
    if custom_data and isinstance(custom_data, dict):
        THEMES["custom"].update(custom_data)
    apply_theme(saved_theme, custom_data if saved_theme == "custom" else None)
    # Legacy: respect accent_color override for non-custom themes
    if saved_theme != "custom":
        saved_accent = APPDATA.get("accent_color")
        if saved_accent:
            C["accent"] = saved_accent

APP_VERSION = "1.0"
APP_NAME    = "KeeraTools"

# ══════════════════════════════════════════════════════════════════
#  DONNÉES
# ══════════════════════════════════════════════════════════════════
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] {path}: {e}")
        return {}

def get_app_logo_url(app_name):
    """Récupère l'URL du logo depuis APPS_DATA"""
    for cat_apps in APPS_DATA.values():
        if app_name in cat_apps:
            app_data = cat_apps[app_name]
            if isinstance(app_data, dict) and "logo" in app_data:
                return app_data["logo"]
    return None

def get_winget_id(app_name):
    """Récupère l'ID winget depuis APPS_DATA"""
    for cat_apps in APPS_DATA.values():
        if app_name in cat_apps:
            app_data = cat_apps[app_name]
            if isinstance(app_data, dict) and "id" in app_data:
                return app_data["id"]
            elif isinstance(app_data, str):
                return app_data
    return None


APPS_DATA = load_json(APPS_JSON)
TRAD_DATA = load_json(TRAD_JSON)

class Translator:
    def __init__(self):
        self.lang = "fr"
    def t(self, key, **kwargs):
        val = TRAD_DATA.get(self.lang, {}).get(key, key)
        if kwargs:
            try: val = val.format(**kwargs)
            except: pass
        return val
    def set_lang(self, lang):
        self.lang = lang

TR = Translator()
apply_saved_settings()  # applique langue + accent sauvegardés

CAT_ICONS = {
    "Navigateurs": "🌐", "Bureautique": "📄", "Outils Multimédia": "🎬",
    "Outils Professionnel": "🔧", "Utilitaires Windows": "⚙️",
    "Outils Microsoft": "🪟", "Jeux": "🎮", "Developpements": "💻",
    "Communication": "💬",
}

APP_ICONS = {
    # Navigateurs
    "Brave": "🦁", "Firefox": "🦊", "Google Chrome": "🔵",
    "Chromium": "🟣", "Arc": "⚡", "Microsft Edge": "🔵",
    "Tor Browser": "🧅", "Falkon": "🦅", "LibreWolf": "🐺",
    "Waterfox": "🦊", "Floorp": "🦢",
    # Bureautique
    "LibreOffice": "📘", "Notepad++": "📝", "Adobe Acrobat Reader": "📕",
    "Obsidian": "🟣", "KDE Okular": "👁️", "Foxit PDF Reader": "📄",
    # Multimédia
    "VLC": "📺", "Krita": "🎨", "IMG Burn": "💿", "ImageGlass": "🖼️",
    "OBS Studio": "🎥", "AIMP": "🎵", "Paint.NET": "🖌️", "Blender": "🎭",
    "iTunes": "🎵", "Jellyfin Server": "📹", "Jellyfin Media Player": "▶️",
    "Audacity": "🎧", "KiCad": "⚡", "FFMpeg": "🎬",
    # Professionnel
    "Advance IP Scanner": "🔍", "WinSCP": "📤", "WireGuard": "🔐",
    "PuTTY": "💻", "OpenVPN Connect": "🔓", "WireShark": "🐠", "Ventoy": "💿",
    # Utilitaires
    "TeamViewer": "🖱️", "7-Zip": "📦", "WinRAR": "📦", "Rufus": "💿",
    "Recuva": "🗑️", "CCleaner": "🧹", "GPU-Z": "🎮", "CPU-Z": "⚙️",
    # Microsoft
    "Visual Studio Code": "💜", "Microsoft Office": "📊",
    # Jeux & Dev
    "Steam": "🎮", "Godot": "👽", "Unity": "🟠",
}

# ══════════════════════════════════════════════════════════════════
#  STYLES
# ══════════════════════════════════════════════════════════════════
def global_css():
    return f"""
* {{ font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif; }}
QMainWindow, QDialog {{ background: {C['bg']}; }}
QWidget {{ background: transparent; color: {C['text']}; font-size: 15px; }}
QScrollBar:vertical {{ background: {C['surface']}; width: 7px; border-radius: 3px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {C['border']}; border-radius: 3px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: {C['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 0; }}
QTextEdit {{
    background: {C['surface']}; border: 1px solid {C['border']};
    border-radius: 8px; color: {C['text']};
    font-family: 'Consolas', monospace; font-size: 13px; padding: 8px;
}}
QMessageBox {{ background: {C['surface']}; color: {C['text']}; }}
QMessageBox QLabel {{ color: {C['text']}; background: transparent; font-size: 14px; }}
QMessageBox QPushButton {{
    background: {C['accent']}; color: white; border: none;
    border-radius: 7px; padding: 7px 18px; font-size: 13px;
}}
QComboBox {{
    background: {C['bg']}; color: {C['text']};
    border: 1px solid {C['border']}; border-radius: 7px;
    padding: 7px 14px; min-width: 200px; font-size: 14px;
    font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif;
}}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox QAbstractItemView {{
    background: {C['surface']}; color: {C['text']};
    selection-background-color: {C['accent']};
    border: 1px solid {C['border']}; font-size: 14px;
}}
"""

def btn_style(color=None, outline=False):
    c = color or C["accent"]
    fam = _COMFORTAA
    if outline:
        return f"""QPushButton {{
            background: transparent; color: {c};
            border: 1.5px solid {c}; border-radius: 8px;
            padding: 8px 20px; font-size: 13px; font-weight: 600;
            font-family: '{fam}', 'Segoe UI', sans-serif;
        }}
        QPushButton:hover {{ background: {c}22; }}
        QPushButton:pressed {{ background: {c}44; }}
        QPushButton:disabled {{ color: {C['muted']}; border-color: {C['border']}; }}"""
    return f"""QPushButton {{
        background: {c}; color: white; border: none;
        border-radius: 8px; padding: 9px 22px;
        font-size: 13px; font-weight: 600;
        font-family: '{fam}', 'Segoe UI', sans-serif;
    }}
    QPushButton:hover {{ background: {c}DD; }}
    QPushButton:pressed {{ background: {c}99; }}
    QPushButton:disabled {{ background: {C['border']}; color: {C['muted']}; }}"""

def nav_btn_style(active=False):
    fam = _COMFORTAA
    if active:
        return f"""QPushButton {{
            background: {C['accent']}; color: white; border: none;
            border-radius: 9px; padding: 11px 28px;
            font-size: 14px; font-weight: 700;
            font-family: '{fam}', 'Segoe UI', sans-serif;
        }}"""
    return f"""QPushButton {{
        background: transparent; color: {C['muted']}; border: none;
        border-radius: 9px; padding: 11px 28px; font-size: 14px;
        font-family: '{fam}', 'Segoe UI', sans-serif;
    }}
    QPushButton:hover {{ background: {C['surface2']}; color: {C['text']}; }}"""

def cat_btn_style(active=False):
    fam = _COMFORTAA
    if active:
        return f"""QPushButton {{
            background: {C['selected']}; color: {C['accent']};
            border: 1px solid {C['accent']}55;
            border-left: 3px solid {C['accent']};
            border-radius: 7px; padding: 11px 16px;
            font-size: 13px; font-weight: 600; text-align: left;
            font-family: '{fam}', 'Segoe UI', sans-serif;
        }}"""
    return f"""QPushButton {{
        background: transparent; color: {C['muted']}; border: none;
        border-left: 3px solid transparent; border-radius: 7px;
        padding: 11px 16px; font-size: 13px; text-align: left;
        font-family: '{fam}', 'Segoe UI', sans-serif;
    }}
    QPushButton:hover {{
        background: {C['surface2']}; color: {C['text']};
        border-left: 3px solid {C['border']};
    }}"""

# ══════════════════════════════════════════════════════════════════
#  FLAG – mise à jour AppInstaller (une seule fois par session)
# ══════════════════════════════════════════════════════════════════
_WINGET_APPINSTALLER_UPDATED = False   # True après la 1ʳᵉ install winget

# ══════════════════════════════════════════════════════════════════
#  THREAD
# ══════════════════════════════════════════════════════════════════
class InstallThread(QThread):
    log_signal  = pyqtSignal(str)
    done_signal = pyqtSignal(list, list)
    prog_signal = pyqtSignal(int, int)

    def __init__(self, apps, mode="install", package_manager="winget"):
        super().__init__()
        self.apps = apps
        self.mode = mode
        self.package_manager = package_manager.lower()
        self._abort = False
        self._current_proc = None   # process winget en cours

    def abort(self):
        """Demande l'arrêt propre du thread et kill le process en cours."""
        self._abort = True
        if self._current_proc is not None:
            try:
                self._current_proc.kill()
            except Exception:
                pass

    def _update_app_installer(self):
        """Met à jour winget (Microsoft.AppInstaller) avant la 1ʳᵉ utilisation."""
        global _WINGET_APPINSTALLER_UPDATED
        if _WINGET_APPINSTALLER_UPDATED:
            return
        _WINGET_APPINSTALLER_UPDATED = True

        self.log_signal.emit(
            "\n" + "─" * 70 + "\n"
            "⟳  Mise à jour de Microsoft.AppInstaller (winget)…\n"
            + "─" * 70 + "\n"
        )
        APPDATA.log_install("Mise à jour de Microsoft.AppInstaller via winget")
        cmd = [
            "winget", "update", "Microsoft.AppInstaller",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]
        try:
            r = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True,
                stdin=subprocess.DEVNULL,   # évite tout prompt interactif
            )
            for line in r.stdout:
                self.log_signal.emit(line)
            r.wait()
            if r.returncode == 0:
                self.log_signal.emit("✓  Microsoft.AppInstaller est à jour.\n\n")
                APPDATA.log_install("  ✓ Microsoft.AppInstaller — succès")
            else:
                # Code 0x8A150056 = déjà à jour — pas bloquant
                self.log_signal.emit(
                    f"ℹ  Microsoft.AppInstaller — code {r.returncode} "
                    f"(déjà à jour ou non disponible, on continue).\n\n"
                )
                APPDATA.log_install(
                    f"  ℹ Microsoft.AppInstaller — code retour {r.returncode} (non bloquant)"
                )
        except Exception as e:
            self.log_signal.emit(f"⚠  Impossible de mettre à jour AppInstaller : {e}\n\n")
            APPDATA.log_install(f"  ⚠ Microsoft.AppInstaller — exception : {e}", level="warning")

    def run(self):
        global _WINGET_APPINSTALLER_UPDATED
        success, failed = [], []
        total = len(self.apps)
        
        # Commandes pour Winget
        winget_cmd_map = {
            "install"  : ["winget","install","--id","{id}",
                          "--accept-package-agreements","--accept-source-agreements"],
            "update"   : ["winget","upgrade","--id","{id}",
                          "--accept-package-agreements","--accept-source-agreements"],
            "uninstall": ["winget","uninstall","--id","{id}"],
        }
        
        # Commandes pour Chocolatey
        choco_cmd_map = {
            "install"  : ["choco","install","{id}","-y","--no-progress"],
            "update"   : ["choco","upgrade","{id}","-y","--no-progress"],
            "uninstall": ["choco","uninstall","{id}","-y"],
        }
        
        cmd_map = winget_cmd_map if self.package_manager == "winget" else choco_cmd_map
        pm_name = "Winget" if self.package_manager == "winget" else "Chocolatey (NOT WORK / NON FONCTIONNEL)"
        verb_map = {"install":"Installation","update":"Mise à jour","uninstall":"Désinstallation"}

        # ── Mise à jour AppInstaller avant la 1ʳᵉ install winget ──
        if self.package_manager == "winget" and not _WINGET_APPINSTALLER_UPDATED:
            self._update_app_installer()
        
        APPDATA.log_install(f"=== Début : {verb_map[self.mode]} de {total} application(s) via {pm_name} ===")
        for idx,(name,wid) in enumerate(self.apps):
            if self._abort:
                break
            self.prog_signal.emit(idx, total)
            self.log_signal.emit(f"\n{'='*70}\n>>> {verb_map[self.mode]} de {name}...\n{'='*70}\n")
            APPDATA.log_install(f"{verb_map[self.mode]} : {name}  (id={wid}, manager={pm_name})")
            cmd = [c.replace("{id}", wid) for c in cmd_map[self.mode]]
            try:
                # Exécuter le processus et afficher la sortie en temps réel
                self._current_proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, universal_newlines=True
                )
                
                # Lire la sortie ligne par ligne pour préserver \r
                for line in self._current_proc.stdout:
                    if self._abort:
                        self._current_proc.kill()
                        break
                    self.log_signal.emit(line)
                
                self._current_proc.wait()
                rc = self._current_proc.returncode
                self._current_proc = None

                if self._abort:
                    break

                if rc == 0:
                    success.append(name)
                    self.log_signal.emit(f"\n✓ {name} — OK\n")
                    APPDATA.log_install(f"  ✓ {name} — succès")
                else:
                    failed.append(name)
                    self.log_signal.emit(f"\n✗ {name} — code {rc}\n")
                    APPDATA.log_install(f"  ✗ {name} — code retour {rc}", level="error")
            except FileNotFoundError:
                failed.append(name)
                error_msg = f"✗ {self.package_manager} introuvable"
                self.log_signal.emit(f"\n{error_msg}\n")
                APPDATA.log_install(f"  {error_msg}", level="critical")
                break
            except Exception as e:
                if self._abort:
                    break
                failed.append(name)
                self.log_signal.emit(f"\n✗ Erreur : {e}\n")
                APPDATA.log_install(f"  ✗ {name} — exception : {e}", level="error")
        
        self.prog_signal.emit(total, total)
        self.done_signal.emit(success, failed)
        status = "ANNULÉ" if self._abort else "Fin"
        APPDATA.log_install(
            f"=== {status} : {len(success)} succès, {len(failed)} échec(s)"
            + (f" — {', '.join(failed)}" if failed else "") + " ==="
        )

# ══════════════════════════════════════════════════════════════════
#  DIALOGUE INSTALLATION
# ══════════════════════════════════════════════════════════════════
class InstallDialog(QDialog):
    def __init__(self, apps, mode="install", parent=None, package_manager="winget"):
        super().__init__(parent)
        self.package_manager = package_manager.lower()
        self.current_line = ""  # Buffer pour la ligne actuelle
        labels = {"install":TR.t("install_in_progress"),"update":TR.t("update_in_progress"),"uninstall":TR.t("uninstall_in_progress")}
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
        
        # Créer le thread avec le gestionnaire sélectionné
        self.thread = InstallThread(apps, mode, self.package_manager)
        self.thread.log_signal.connect(self._on_log_message)
        self.thread.prog_signal.connect(lambda cur, tot: None)  # Ignorer la progression
        self.thread.done_signal.connect(self._on_done)
        self.thread.start()
    
    def _on_log_message(self, message):
        """Gère les messages de log avec support pour les retours chariot (animation fluide)."""
        if not message:
            return
        
        # Obtenir le curseur à la fin du document
        cursor = self.log_box.textCursor()
        cursor.movePosition(cursor.End)
        
        # Diviser sur les retours chariot
        parts = message.split('\r')
        
        for i, part in enumerate(parts):
            if i == 0:
                # Première partie : ajouter au document
                cursor.insertText(part)
            else:
                # Pour chaque \r, on sélectionne et remplace la dernière ligne
                # Aller au début de la dernière ligne
                cursor.movePosition(cursor.StartOfLine)
                # Sélectionner jusqu'à la fin de la ligne
                cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)
                # Remplacer le texte sélectionné
                cursor.insertText(part)
        
        # Placer le curseur à la fin pour le prochain message
        cursor.movePosition(cursor.End)
        self.log_box.setTextCursor(cursor)
        
        # Auto-scroll vers le bas
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
        """Demande confirmation si une installation est encore en cours."""
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
            # L'utilisateur confirme → on kill
            self.log_box.append("\n⛔  Annulation en cours…")
            self.thread.abort()
            self.thread.wait(3000)   # max 3 s pour que le thread se termine proprement
        event.accept()

# ══════════════════════════════════════════════════════════════════
#  THREAD CHARGEMENT IMAGES
# ══════════════════════════════════════════════════════════════════
class IconLoaderThread(QThread):
    icon_loaded = pyqtSignal(str, QPixmap)  # (app_name, pixmap)
    
    def __init__(self, app_name, url, size=96):
        super().__init__()
        self.app_name = app_name
        self.url = url
        self.size = size
    
    def run(self):
        if not self.url:
            return
        try:
            response = urllib.request.urlopen(self.url, timeout=5)
            image_data = response.read()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            if not pixmap.isNull():
                scaled = pixmap.scaledToWidth(self.size, Qt.SmoothTransformation)
                self.icon_loaded.emit(self.app_name, scaled)
        except Exception as e:
            print(f"[WARN] Impossible de charger {self.url}: {e}")

# ══════════════════════════════════════════════════════════════════
#  CARTE APPLICATION (GRILLE)
# ══════════════════════════════════════════════════════════════════
class AppCard(QFrame):
    """Carré sélectionnable pour une application"""
    clicked = pyqtSignal(str, str)  # (app_name, winget_id)
    
    def __init__(self, app_name, winget_id, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.winget_id = winget_id
        self.is_selected = False
        self.icon_label = None
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
        
        # Logo/Icône
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Charger le logo depuis l'URL
        logo_url = get_app_logo_url(self.app_name)
        if logo_url:
            self._icon_thread = IconLoaderThread(self.app_name, logo_url, 96)
            self._icon_thread.icon_loaded.connect(self._on_icon_loaded)
            self._icon_thread.start()
        else:
            # Fallback : emoji
            emoji = APP_ICONS.get(self.app_name, "📦")
            self.icon_label.setText(emoji)
            self.icon_label.setFont(QFont("Arial", 48))
        
        layout.addWidget(self.icon_label)
        
        # Nom de l'application
        name_label = QLabel(self.app_name)
        name_label.setFont(CF(11, True))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"color: {C['text']}; background: transparent;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        self._update_style()
    
    def _on_icon_loaded(self, app_name, pixmap):
        """Affiche l'icône une fois chargée"""
        if app_name == self.app_name and self.icon_label:
            self.icon_label.setPixmap(pixmap)
    
    def _update_style(self):
        """Mets à jour le style en fonction de l'état de sélection"""
        if self.is_selected:
            border_color = C['success']  # Vert pour sélectionné
            border_width = "3px"
            bg_color = C['selected']
            hover_bg = "#1a2540"
            hover_border = C['success']
        else:
            border_color = C['border']
            border_width = "1px"
            bg_color = C['surface']
            hover_bg = C['surface2']
            hover_border = C['accent']
        
        self.setStyleSheet(f"""QFrame {{
            background: {bg_color};
            border: {border_width} solid {border_color};
            border-radius: 12px;
        }}
        QFrame:hover {{
            border-color: {hover_border};
            background: {hover_bg};
        }}""")

    
    def set_selected(self, selected):
        """Change l'état de sélection"""
        self.is_selected = selected
        self._update_style()
    
    def mousePressEvent(self, event):
        """Bascule la sélection au clic"""
        self.is_selected = not self.is_selected
        self._update_style()
        self.clicked.emit(self.app_name, self.winget_id)
        super().mousePressEvent(event)

# ══════════════════════════════════════════════════════════════════
#  ONGLET APPLICATIONS
# ══════════════════════════════════════════════════════════════════
class AppsTab(QWidget):
    def __init__(self):
        super().__init__()
        self._selected = {}
        self._cat_buttons = {}
        self._current_cat = ""
        self._app_cards = {}  # {app_name: AppCard}
        self._app_cards_list = []  # Liste pour _toggle_select_all
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Panneau gauche
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
        self._sel_counter.setStyleSheet(f"color: {C['accent']}; padding: 7px 10px; background: {C['accent']}18; border-radius: 7px;")
        self._sel_counter.setAlignment(Qt.AlignCenter)
        ll.addWidget(self._sel_counter)
        root.addWidget(left)

        # Panneau droit
        right = QWidget()
        right.setStyleSheet(f"background: {C['bg']};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self._cat_header = QFrame()
        self._cat_header.setFixedHeight(60)
        self._cat_header.setStyleSheet(f"QFrame {{ background: {C['surface2']}; border-bottom: 1px solid {C['border']}; }}")
        hh = QHBoxLayout(self._cat_header)
        hh.setContentsMargins(22, 0, 22, 0)

        self._cat_label = QLabel(TR.t("select_category"))
        self._cat_label.setFont(CF(14, True))
        self._cat_label.setStyleSheet(f"color: {C['text']};")

        # Sélecteur de gestionnaire de paquets
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

        # ZONE APPS — Grille avec AppCard
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
        self._action_bar.setStyleSheet(f"QFrame {{ background: {C['surface']}; border-top: 1px solid {C['border']}; }}")
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

        for btn in [self._btn_install, self._btn_update, self._btn_uninstall, self._btn_export, self._btn_import]:
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

    def _select_category(self, cat):
        for c, btn in self._cat_buttons.items():
            btn.setStyleSheet(cat_btn_style(c == cat))
        self._current_cat = cat
        icon = CAT_ICONS.get(cat, "📦")
        self._cat_label.setText(f"{icon}  {cat}")
        self._sel_all_btn.setVisible(True)

        # Vider la grille
        self._app_cards.clear()
        self._app_cards_list.clear()
        while self._apps_grid.count():
            item = self._apps_grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        # Ajouter les AppCard en grille
        apps = APPS_DATA.get(cat, {})
        row, col = 0, 0
        cols = 5  # 5 colonnes pour une meilleure utilisation de l'espace
        
        for app_name in apps.keys():
            winget_id = get_winget_id(app_name)
            card = AppCard(app_name, winget_id)
            # Restaurer l'état de sélection
            if app_name in self._selected:
                card.set_selected(True)
            # Connecter le signal de sélection
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
        """Gère le clic sur une AppCard"""
        card = self._app_cards.get(name)
        if not card:
            return
        
        if card.is_selected:
            self._selected[name] = winget_id
        else:
            self._selected.pop(name, None)
        
        self._update_counter()

    def _on_check(self, state, name, winget_id):
        if state == Qt.Checked:
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
        cat_apps = set(APPS_DATA.get(self._current_cat, {}).keys())
        sel_in = cat_apps & set(self._selected.keys())
        self._sel_all_btn.setText(
            TR.t("deselect_all") if sel_in == cat_apps and cat_apps else TR.t("select_all")
        )

    def _toggle_select_all(self):
        cat_apps = APPS_DATA.get(self._current_cat, {})
        all_sel = all(n in self._selected for n in cat_apps)
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
            if len(self._selected) > 4: names += "…"
            if QMessageBox.question(self, "Confirmer",
               f"Désinstaller :\n{names}\n\nContinuer ?",
               QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
        # Récupérer le gestionnaire sélectionné
        package_manager = self._pm_selector.currentText().lower()
        InstallDialog(list(self._selected.items()), mode, self, package_manager).exec_()

    def _export_selection(self):
        if not self._selected:
            QMessageBox.information(self, "Info", TR.t("no_app_selected_export")); return
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

# ══════════════════════════════════════════════════════════════════
#  ONGLET PERSONNALISATION
# ══════════════════════════════════════════════════════════════════
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
        vbox.addWidget(self._startup_card())
        vbox.addWidget(self._accent_card())
        vbox.addWidget(self._logs_card())
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
        self._status = QLabel("")
        self._status.setFont(CF(12))
        self._status.setStyleSheet(f"color: {C['success']};")
        layout.addWidget(self._status)

    def _card(self, title_text, subtitle=""):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 11px; }}")
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

    def _is_laptop(self):
        """Détecte si le PC est un portable (via batterie)."""
        try:
            result = subprocess.run(["powercfg", "/list"], capture_output=True, text=True)
            # Vérifier si les schémas de batterie existent
            return "battery" in result.stdout.lower() or len(result.stdout.split('\n')) > 4
        except:
            return False

    def _power_management_card(self):
        """Carte de gestion de l'alimentation du PC (détection portable/fixe)."""
        is_laptop = self._is_laptop()
        title = "🔋  Gestion de l'alimentation du PC"
        subtitle = "Configurez les paramètres de mise en veille de votre appareil."
        card, lay = self._card(title, subtitle)
        
        # Section Écran
        screen_title = QLabel("📺  Mise en veille de l'écran")
        screen_title.setFont(CF(13, True))
        screen_title.setStyleSheet(f"color: {C['text']};")
        lay.addWidget(screen_title)
        
        row_screen = QHBoxLayout()
        lbl_screen = QLabel("Délai sur secteur :")
        lbl_screen.setFont(CF(12))
        self._screen_combo = QComboBox()
        self._screen_combo.setFont(CF(12))
        self._screen_combo.setStyleSheet(f"""
            QComboBox {{
                background: {C['surface2']}; color: {C['text']};
                border: 1px solid {C['border']}; border-radius: 7px;
                padding: 7px 14px; font-size: 14px;
                font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif;
            }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
        """)
        items_screen = [("1 minute",1),("5 minutes",5),("10 minutes",10),
                        ("15 minutes",15),("30 minutes",30),("1 heure",60),("Jamais",0)]
        self._screen_values = [v for _,v in items_screen]
        for label,_ in items_screen: self._screen_combo.addItem(label + " ▼")
        btn_screen = QPushButton("Appliquer")
        btn_screen.setFont(CF(11, True))
        btn_screen.setStyleSheet(btn_style(C["accent"]))
        btn_screen.clicked.connect(self._apply_screen_sleep)
        row_screen.addWidget(lbl_screen); row_screen.addWidget(self._screen_combo); 
        row_screen.addWidget(btn_screen); row_screen.addStretch()
        lay.addLayout(row_screen)
        
        # Section PC
        pc_title = QLabel("💤  Mise en veille du PC")
        pc_title.setFont(CF(13, True))
        pc_title.setStyleSheet(f"color: {C['text']};")
        lay.addWidget(pc_title)
        
        row_pc = QHBoxLayout()
        lbl_pc = QLabel("Délai sur secteur :")
        lbl_pc.setFont(CF(12))
        self._pc_combo = QComboBox()
        self._pc_combo.setFont(CF(12))
        self._pc_combo.setStyleSheet(f"""
            QComboBox {{
                background: {C['surface2']}; color: {C['text']};
                border: 1px solid {C['border']}; border-radius: 7px;
                padding: 7px 14px; font-size: 14px;
                font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif;
            }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
        """)
        items_pc = [("1 minute",1),("5 minutes",5),("10 minutes",10),
                    ("15 minutes",15),("30 minutes",30),("1 heure",60),("Jamais",0)]
        self._pc_values = [v for _,v in items_pc]
        for label,_ in items_pc: self._pc_combo.addItem(label + " ▼")
        btn_pc = QPushButton("Appliquer")
        btn_pc.setFont(CF(11, True))
        btn_pc.setStyleSheet(btn_style(C["warning"]))
        btn_pc.clicked.connect(self._apply_pc_sleep)
        row_pc.addWidget(lbl_pc); row_pc.addWidget(self._pc_combo);
        row_pc.addWidget(btn_pc); row_pc.addStretch()
        lay.addLayout(row_pc)
        
        # Section Bouton d'alimentation si PC fixe
        if not is_laptop:
            button_title = QLabel("🔴  Bouton d'alimentation (tour)")
            button_title.setFont(CF(13, True))
            button_title.setStyleSheet(f"color: {C['text']};")
            lay.addWidget(button_title)
            
            row_btn = QHBoxLayout()
            lbl_btn = QLabel("Action en cas d'appui :")
            lbl_btn.setFont(CF(12))
            self._button_combo = QComboBox()
            self._button_combo.setFont(CF(12))
            self._button_combo.setStyleSheet(f"""
                QComboBox {{
                    background: {C['surface2']}; color: {C['text']};
                    border: 1px solid {C['border']}; border-radius: 7px;
                    padding: 7px 14px; font-size: 14px;
                    font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif;
                }}
                QComboBox::drop-down {{ border: none; width: 28px; }}
            """)
            items_btn = [("Rien", 0), ("Arrêt", 1), ("Veille", 2), ("Hibernation", 3)]
            self._button_values = [v for _,v in items_btn]
            for label,_ in items_btn: self._button_combo.addItem(label + " ▼")
            btn_apply = QPushButton("Appliquer")
            btn_apply.setFont(CF(11, True))
            btn_apply.setStyleSheet(btn_style(C["danger"]))
            btn_apply.clicked.connect(self._apply_button_action)
            row_btn.addWidget(lbl_btn); row_btn.addWidget(self._button_combo);
            row_btn.addWidget(btn_apply); row_btn.addStretch()
            lay.addLayout(row_btn)
        
        # Section Batterie pour les portables
        if is_laptop:
            battery_title = QLabel("🔋  Mise en veille sur batterie")
            battery_title.setFont(CF(13, True))
            battery_title.setStyleSheet(f"color: {C['text']};")
            lay.addWidget(battery_title)
            
            row_batt_screen = QHBoxLayout()
            lbl_batt_screen = QLabel("Délai écran sur batterie :")
            lbl_batt_screen.setFont(CF(12))
            self._batt_screen_combo = QComboBox()
            self._batt_screen_combo.setFont(CF(12))
            self._batt_screen_combo.setStyleSheet(f"""
                QComboBox {{
                    background: {C['surface2']}; color: {C['text']};
                    border: 1px solid {C['border']}; border-radius: 7px;
                    padding: 7px 14px; font-size: 14px;
                    font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif;
                }}
                QComboBox::drop-down {{ border: none; width: 28px; }}
            """)
            items_batt = [("1 minute",1),("5 minutes",5),("10 minutes",10),
                          ("15 minutes",15),("30 minutes",30),("1 heure",60),("Jamais",0)]
            self._batt_screen_values = [v for _,v in items_batt]
            for label,_ in items_batt: self._batt_screen_combo.addItem(label + " ▼")
            btn_batt_screen = QPushButton("Appliquer")
            btn_batt_screen.setFont(CF(11, True))
            btn_batt_screen.setStyleSheet(btn_style(C["success"]))
            btn_batt_screen.clicked.connect(self._apply_batt_screen_sleep)
            row_batt_screen.addWidget(lbl_batt_screen); row_batt_screen.addWidget(self._batt_screen_combo);
            row_batt_screen.addWidget(btn_batt_screen); row_batt_screen.addStretch()
            lay.addLayout(row_batt_screen)
            
            row_batt_pc = QHBoxLayout()
            lbl_batt_pc = QLabel("Délai PC sur batterie :")
            lbl_batt_pc.setFont(CF(12))
            self._batt_pc_combo = QComboBox()
            self._batt_pc_combo.setFont(CF(12))
            self._batt_pc_combo.setStyleSheet(f"""
                QComboBox {{
                    background: {C['surface2']}; color: {C['text']};
                    border: 1px solid {C['border']}; border-radius: 7px;
                    padding: 7px 14px; font-size: 14px;
                    font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif;
                }}
                QComboBox::drop-down {{ border: none; width: 28px; }}
            """)
            for label,_ in items_batt: self._batt_pc_combo.addItem(label)
            self._batt_pc_values = [v for _,v in items_batt]
            btn_batt_pc = QPushButton("Appliquer")
            btn_batt_pc.setFont(CF(11, True))
            btn_batt_pc.setStyleSheet(btn_style(C["success"]))
            btn_batt_pc.clicked.connect(self._apply_batt_pc_sleep)
            row_batt_pc.addWidget(lbl_batt_pc); row_batt_pc.addWidget(self._batt_pc_combo);
            row_batt_pc.addWidget(btn_batt_pc); row_batt_pc.addStretch()
            lay.addLayout(row_batt_pc)
        
        return card
    
    def _apply_screen_sleep(self):
        minutes = self._screen_values[self._screen_combo.currentIndex()]
        try:
            subprocess.run(["powercfg","/change","monitor-timeout-ac",str(minutes)], capture_output=True)
            self._show_status(f"✓ Veille écran configurée : {self._screen_combo.currentText()}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])
    
    def _apply_pc_sleep(self):
        minutes = self._pc_values[self._pc_combo.currentIndex()]
        try:
            result = subprocess.run(["powercfg","/change","standby-timeout-ac",str(minutes)], capture_output=True)
            if result.returncode != 0:
                self._show_status(f"✗ Erreur powercfg (code {result.returncode})", C["danger"])
            else:
                self._show_status(f"✓ Veille PC configurée : {self._pc_combo.currentText()}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])
    
    def _apply_batt_screen_sleep(self):
        minutes = self._batt_screen_values[self._batt_screen_combo.currentIndex()]
        try:
            subprocess.run(["powercfg","/change","monitor-timeout-dc",str(minutes)], capture_output=True)
            self._show_status(f"✓ Veille batterie (écran) configurée : {self._batt_screen_combo.currentText()}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])
    
    def _apply_batt_pc_sleep(self):
        minutes = self._batt_pc_values[self._batt_pc_combo.currentIndex()]
        try:
            result = subprocess.run(["powercfg","/change","standby-timeout-dc",str(minutes)], capture_output=True)
            if result.returncode != 0:
                self._show_status(f"✗ Erreur powercfg (code {result.returncode})", C["danger"])
            else:
                self._show_status(f"✓ Veille batterie (PC) configurée : {self._batt_pc_combo.currentText()}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])
    
    def _apply_button_action(self):
        action = self._button_values[self._button_combo.currentIndex()]
        actions = {0: "Ne rien faire", 1: "Arrêt", 2: "Veille", 3: "Hibernation"}
        # GUIDs: SUB_BUTTONS = 4f971e89-eebd-4455-a8de-9e59040e7347
        # PBUTTONACTION = 7648efa3-dd9c-4e3e-b566-50f929386280
        try:
            result = subprocess.run([
                "powercfg", "/setacvalueindex", "SCHEME_CURRENT",
                "4f971e89-eebd-4455-a8de-9e59040e7347",
                "7648efa3-dd9c-4e3e-b566-50f929386280",
                str(action)
            ], capture_output=True)
            subprocess.run(["powercfg", "/setactive", "SCHEME_CURRENT"], capture_output=True)
            if result.returncode != 0:
                self._show_status(f"✗ Erreur powercfg (code {result.returncode})", C["danger"])
            else:
                self._show_status(f"✓ Action bouton configurée : {actions[action]}", C["success"])
        except Exception as e:
            self._show_status(f"✗ {e}", C["danger"])

    # ── GESTIONNAIRE DE DÉMARRAGE WINDOWS ─────────────────────────
    def _startup_card(self):
        """Carte de gestion du démarrage Windows : liste toutes les apps et permet activer/désactiver."""
        card, lay = self._card(
            "🚀  Démarrage Windows",
            "Gérez les applications qui démarrent automatiquement avec Windows. "
            "Cliquez sur une application pour l'activer ou la désactiver."
        )

        # Barre de refresh + info
        top_row = QHBoxLayout()
        self._startup_count_lbl = QLabel("")
        self._startup_count_lbl.setFont(CF(11))
        self._startup_count_lbl.setStyleSheet(f"color: {C['muted']};")
        top_row.addWidget(self._startup_count_lbl)
        top_row.addStretch()

        btn_refresh = QPushButton("🔄  Actualiser")
        btn_refresh.setFont(CF(11))
        btn_refresh.setStyleSheet(btn_style(outline=True))
        btn_refresh.setFixedHeight(32)
        btn_refresh.clicked.connect(self._refresh_startup_list)

        btn_tm = QPushButton("📋  Gestionnaire de tâches")
        btn_tm.setFont(CF(11))
        btn_tm.setStyleSheet(btn_style(C["accent"]))
        btn_tm.setFixedHeight(32)
        btn_tm.clicked.connect(lambda: subprocess.Popen(["taskmgr.exe"]))

        top_row.addWidget(btn_refresh)
        top_row.addWidget(btn_tm)
        lay.addLayout(top_row)

        # Zone scrollable pour la liste
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

        # Charger la liste au premier affichage
        self._refresh_startup_list()
        return card

    def _get_startup_entries(self):
        """Lit TOUTES les entrées de démarrage comme le Gestionnaire de tâches Windows.
        Sources : registre HKCU + HKLM (32 et 64 bit) + dossiers Startup utilisateur et commun.
        Retourne une liste de dicts : {name, value, hive, key_path, hive_label, enabled, source}
        """
        entries = []
        seen_names = set()  # éviter les doublons

        # ── 1. Lire les états activé/désactivé depuis StartupApproved ──────────
        # Windows stocke ici un flag binaire pour chaque entrée du registre Run
        approved_locations = [
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32"),
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"),
        ]
        # disabled_names : set de noms (lowercase) dont le flag commence par 03
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

        # ── 2. Clés registre Run (HKCU + HKLM, 64-bit et 32-bit WOW64) ─────────
        reg_locations = [
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\Run",
             winreg.KEY_READ,
             "Utilisateur"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\Microsoft\Windows\CurrentVersion\Run",
             winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
             "Système"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\Microsoft\Windows\CurrentVersion\Run",
             winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
             "Système (32)"),
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
             winreg.KEY_READ,
             "Utilisateur (once)"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
             winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
             "Système (once)"),
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
                            enabled = key not in disabled_names
                            entries.append({
                                "name": vname,
                                "value": str(vdata),
                                "hive": hive,
                                "key_path": kpath,
                                "hive_label": hive_label,
                                "enabled": enabled,
                                "source": "registry",
                            })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(k)
            except Exception:
                pass

        # ── 3. Dossiers Startup (utilisateur + commun) ───────────────────────
        startup_folders = []
        # Dossier Startup de l'utilisateur courant
        try:
            k = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
                0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(k, "Startup")
            winreg.CloseKey(k)
            startup_folders.append((Path(val), "Utilisateur"))
        except Exception:
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                startup_folders.append((
                    Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup",
                    "Utilisateur"))

        # Dossier Startup commun (tous les utilisateurs)
        try:
            k = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
                0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(k, "Common Startup")
            winreg.CloseKey(k)
            startup_folders.append((Path(val), "Système"))
        except Exception:
            prog_data = os.environ.get("PROGRAMDATA", "")
            if prog_data:
                startup_folders.append((
                    Path(prog_data) / r"Microsoft\Windows\Start Menu\Programs\Startup",
                    "Système"))

        for folder, label in startup_folders:
            if not folder.exists():
                continue
            for f in folder.iterdir():
                if f.suffix.lower() in (".lnk", ".url", ".bat", ".cmd", ".exe"):
                    fname = f.stem  # nom sans extension
                    key = fname.lower()
                    if key not in seen_names:
                        seen_names.add(key)
                        enabled = key not in disabled_names
                        entries.append({
                            "name": fname,
                            "value": str(f),
                            "hive": None,
                            "key_path": str(folder),
                            "hive_label": label,
                            "enabled": enabled,
                            "source": "folder",
                            "folder_path": str(f),
                        })

        # Trier : actifs en premier, puis alphabétique
        entries.sort(key=lambda e: (not e["enabled"], e["name"].lower()))
        return entries

    def _refresh_startup_list(self):
        """Vide et re-peuple la liste des apps de démarrage."""
        # Vider l'ancien contenu
        while self._startup_list_layout.count():
            item = self._startup_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self._get_startup_entries()

        if not entries:
            empty = QLabel("Aucune application de démarrage trouvée.")
            empty.setFont(CF(12))
            empty.setStyleSheet(f"color: {C['muted']}; padding: 20px;")
            empty.setAlignment(Qt.AlignCenter)
            self._startup_list_layout.addWidget(empty)
            self._startup_count_lbl.setText("0 application(s)")
            return

        enabled_count = sum(1 for e in entries if e["enabled"])
        self._startup_count_lbl.setText(
            f"{len(entries)} application(s)  •  {enabled_count} active(s)"
        )

        for entry in entries:
            row = self._make_startup_row(entry)
            self._startup_list_layout.addWidget(row)

    def _make_startup_row(self, entry):
        """Crée une ligne pour une entrée de démarrage."""
        row = QFrame()
        row.setFixedHeight(56)
        is_enabled = entry["enabled"]

        def _style(enabled):
            border = C['success'] if enabled else C['border']
            bg = C['surface'] if enabled else C['surface2']
            return (f"QFrame {{ background: {bg}; border: 1px solid {border}; "
                    f"border-radius: 9px; }}"
                    f"QFrame:hover {{ border-color: {C['accent']}; }}")

        row.setStyleSheet(_style(is_enabled))

        h = QHBoxLayout(row)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(12)

        # Icône emoji
        icon_lbl = QLabel(self._startup_icon(entry["name"]))
        icon_lbl.setFont(QFont("Segoe UI Emoji", 22))
        icon_lbl.setFixedWidth(36)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        h.addWidget(icon_lbl)

        # Nom de l'app uniquement (pas de chemin)
        name_lbl = QLabel(entry["name"])
        name_lbl.setFont(CF(12, True))
        name_lbl.setStyleSheet(f"color: {C['text']}; background: transparent; border: none;")
        name_lbl.setToolTip(entry["value"])  # chemin visible au survol
        h.addWidget(name_lbl, 1)

        # Badge source
        badge = QLabel(entry["hive_label"])
        badge.setFont(CF(9, True))
        badge.setStyleSheet(
            f"background: {C['accent']}22; color: {C['accent']}; "
            f"border: 1px solid {C['accent']}44; border-radius: 8px; "
            f"padding: 2px 8px;"
        )
        badge.setFixedHeight(22)
        h.addWidget(badge)

        # Bouton toggle
        toggle_btn = QPushButton("✓ Actif" if is_enabled else "✗ Inactif")
        toggle_btn.setFont(CF(11, True))
        toggle_btn.setFixedSize(90, 34)
        toggle_btn.setStyleSheet(
            btn_style(C["success"]) if is_enabled else btn_style(outline=True)
        )
        toggle_btn.setCursor(Qt.PointingHandCursor)

        def _toggle(btn=toggle_btn, e=entry, r=row, s=_style):
            self._toggle_startup_entry(e, btn, r, s)

        toggle_btn.clicked.connect(_toggle)
        h.addWidget(toggle_btn)

        return row

    def _startup_icon(self, name: str) -> str:
        """Retourne un emoji adapté pour une entrée de démarrage."""
        n = name.lower()
        mapping = [
            # Jeux & Gaming
            (["steam"],                      "🎮"),
            (["epic", "epicgames"],          "🎮"),
            (["gog", "galaxy"],              "🎮"),
            (["ubisoft", "uplay"],           "🎮"),
            (["battle.net", "battlenet"],    "🎮"),
            (["origin", "ea "],              "🎮"),
            (["xbox"],                       "🎮"),
            # Communication
            (["discord"],                    "💬"),
            (["whatsapp"],                   "💬"),
            (["telegram"],                   "✈️"),
            (["signal"],                     "💬"),
            (["skype"],                      "📞"),
            (["teams", "msteams"],           "👥"),
            (["zoom"],                       "📹"),
            (["slack"],                      "💼"),
            (["viber"],                      "📞"),
            # Navigateurs
            (["chrome"],                     "🔵"),
            (["chromium"],                   "🔵"),
            (["firefox"],                    "🦊"),
            (["brave"],                      "🦁"),
            (["edge", "msedge"],             "🌐"),
            (["opera"],                      "🔴"),
            (["vivaldi"],                    "🎵"),
            (["tor"],                        "🧅"),
            # Cloud / Stockage
            (["onedrive"],                   "☁️"),
            (["dropbox"],                    "📦"),
            (["googledrive", "google drive", "googledrivesync"], "🟡"),
            (["box"],                        "📦"),
            (["icloud"],                     "☁️"),
            (["mega"],                       "📦"),
            # Musique / Média
            (["spotify"],                    "🎵"),
            (["itunes"],                     "🎵"),
            (["deezer"],                     "🎵"),
            (["vlc"],                        "📺"),
            (["obs"],                        "🎥"),
            (["aimp"],                       "🎵"),
            # Sécurité / Antivirus
            (["defender", "msmpeng", "securityhealthservice"], "🛡️"),
            (["avast"],                      "🛡️"),
            (["avg"],                        "🛡️"),
            (["bitdefender"],                "🛡️"),
            (["kaspersky"],                  "🛡️"),
            (["malwarebytes"],               "🛡️"),
            (["norton"],                     "🛡️"),
            (["eset"],                       "🛡️"),
            (["mcafee"],                     "🛡️"),
            # Drivers & Système constructeur
            (["nvidia", "nvcplui", "nvdisplay", "nv "], "🖥️"),
            (["amd", "radeon", "amdow"],     "🔴"),
            (["intel", "igcc"],              "🔵"),
            (["realtek"],                    "🔊"),
            (["lenovo", "lenovovantage"],    "💻"),
            (["dell", "dellcommand"],        "💻"),
            (["hp", "hpjumpstart"],          "💻"),
            (["asus", "armourycrate"],       "💻"),
            (["msi"],                        "💻"),
            (["acer"],                       "💻"),
            (["logitech", "lghub"],          "🖱️"),
            (["razer"],                      "🐍"),
            (["corsair", "icue"],            "⌨️"),
            (["steelseries"],                "🎮"),
            # Microsoft Office & outils MS
            (["outlook"],                    "📧"),
            (["word"],                       "📝"),
            (["excel"],                      "📊"),
            (["onenote"],                    "📒"),
            (["teams"],                      "👥"),
            (["copilot"],                    "🤖"),
            # IA / Productivité
            (["chatgpt"],                    "🤖"),
            (["notion"],                     "📓"),
            (["obsidian"],                   "🟣"),
            (["todoist"],                    "✅"),
            (["notion"],                     "📓"),
            (["evernote"],                   "🐘"),
            # Utilitaires
            (["7zip", "7-zip"],              "📦"),
            (["winrar"],                     "📦"),
            (["everything"],                 "🔍"),
            (["powertoys"],                  "⚙️"),
            (["autohotkey", "ahk"],          "⌨️"),
            (["rainmeter"],                  "🌧️"),
            (["sharex"],                     "📸"),
            (["greenshot"],                  "📸"),
            (["flux", "f.lux"],              "🌙"),
            (["taskbarx"],                   "📌"),
            (["eartrumpet"],                 "🔊"),
            (["terminal", "windowsterminal"],"⬛"),
            (["qshelper", "qs"],             "🔍"),
            (["applemobiledevice", "bonjour","apple"], "🍎"),
            (["appareils mobiles", "phone link", "yourphone"], "📱"),
            # Dev
            (["vscode", "code"],             "💜"),
            (["git"],                        "🔧"),
            (["python"],                     "🐍"),
            (["java", "jre", "jdk"],         "☕"),
            (["docker"],                     "🐳"),
            (["node"],                       "🟩"),
            # Mises à jour
            (["update", "updater", "autoupdate", "update.exe"], "🔄"),
            (["patch"],                      "🔄"),
            # KeeraTools lui-même
            (["keera", APP_NAME.lower()],    "⚙️"),
        ]
        for keys, icon in mapping:
            if any(k in n for k in keys):
                return icon
        return "🖥️"

    def _toggle_startup_entry(self, entry, btn, row, style_fn):
        """Active ou désactive une entrée de démarrage."""
        is_enabled = entry["enabled"]

        # ── Entrées issues du dossier Startup (raccourcis .lnk etc.) ──────────
        if entry.get("source") == "folder":
            folder_path = Path(entry.get("folder_path", ""))
            disabled_folder = folder_path.parent / "disabled_startup_backup"
            try:
                if is_enabled:
                    # Déplacer vers un sous-dossier de backup
                    disabled_folder.mkdir(exist_ok=True)
                    dest = disabled_folder / folder_path.name
                    shutil.move(str(folder_path), str(dest))
                    entry["folder_path"] = str(dest)
                    entry["enabled"] = False
                    btn.setText("✗ Inactif")
                    btn.setStyleSheet(btn_style(outline=True))
                    self._show_status(f"✓ {entry['name']} désactivé au démarrage.", C["warning"])
                else:
                    # Restaurer depuis le backup
                    dest = folder_path.parent.parent / folder_path.name
                    shutil.move(str(folder_path), str(dest))
                    entry["folder_path"] = str(dest)
                    entry["enabled"] = True
                    btn.setText("✓ Actif")
                    btn.setStyleSheet(btn_style(C["success"]))
                    self._show_status(f"✓ {entry['name']} activé au démarrage.", C["success"])
                row.setStyleSheet(style_fn(entry["enabled"]))
                self._refresh_startup_count()
            except PermissionError:
                QMessageBox.warning(self, "Permission refusée",
                    f"Impossible de modifier '{entry['name']}'.\n"
                    "Relancez en tant qu'administrateur.")
            except Exception as e:
                self._show_status(f"✗ Erreur : {e}", C["danger"])
            return

        # ── Entrées registre : via StartupApproved ────────────────────────────
        approved_key_map = {
            winreg.HKEY_CURRENT_USER:
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
            winreg.HKEY_LOCAL_MACHINE:
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
        }
        try:
            approved_path = approved_key_map.get(entry["hive"])
            if not approved_path:
                raise Exception("Clé de registre non supportée")

            try:
                k = winreg.OpenKey(entry["hive"], approved_path, 0,
                                   winreg.KEY_SET_VALUE | winreg.KEY_READ)
            except FileNotFoundError:
                k = winreg.CreateKey(entry["hive"], approved_path)

            if is_enabled:
                # 03 = désactivé
                data = bytes([3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                winreg.SetValueEx(k, entry["name"], 0, winreg.REG_BINARY, data)
                entry["enabled"] = False
                btn.setText("✗ Inactif")
                btn.setStyleSheet(btn_style(outline=True))
                self._show_status(f"✓ {entry['name']} désactivé au démarrage.", C["warning"])
            else:
                # 02 = activé
                data = bytes([2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                winreg.SetValueEx(k, entry["name"], 0, winreg.REG_BINARY, data)
                entry["enabled"] = True
                btn.setText("✓ Actif")
                btn.setStyleSheet(btn_style(C["success"]))
                self._show_status(f"✓ {entry['name']} activé au démarrage.", C["success"])
            winreg.CloseKey(k)

            row.setStyleSheet(style_fn(entry["enabled"]))
            self._refresh_startup_count()

        except PermissionError:
            QMessageBox.warning(
                self, "Permission refusée",
                f"Impossible de modifier '{entry['name']}'.\n"
                "Relancez KeeraTools en tant qu'administrateur pour modifier les entrées système (HKLM)."
            )
        except Exception as e:
            self._show_status(f"✗ Erreur : {e}", C["danger"])

    def _refresh_startup_count(self):
        """Met à jour uniquement le compteur sans reconstruire toute la liste."""
        entries = self._get_startup_entries()
        enabled_count = sum(1 for e in entries if e["enabled"])
        self._startup_count_lbl.setText(
            f"{len(entries)} application(s)  •  {enabled_count} active(s)"
        )

    def _accent_card(self):
        """Carte de sélection de la couleur d'accent."""
        from PyQt5.QtWidgets import QColorDialog
        card, lay = self._card(
            "🎨  Couleur d'accent",
            "Choisissez la couleur principale de l'interface. "
            "Un redémarrage est nécessaire pour appliquer le changement."
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

        btn_pick = QPushButton("Choisir…")
        btn_pick.setFont(CF(12, True))
        btn_pick.setStyleSheet(btn_style(C["accent"]))
        btn_pick.setFixedHeight(38)

        def pick_color():
            color = QColorDialog.getColor(QColor(C["accent"]), None, "Couleur d'accent")
            if color.isValid():
                hex_color = color.name()
                C["accent"] = hex_color
                APPDATA.set("accent_color", hex_color)
                self._accent_preview.setStyleSheet(
                    f"background: {hex_color}; border-radius: 7px; border: 1px solid {C['border']};"
                )
                self._accent_label.setText(hex_color)
                self._show_status(
                    f"✓ Couleur d'accent enregistrée : {hex_color} — redémarrer pour l'appliquer.",
                    C["success"]
                )

        btn_pick.clicked.connect(pick_color)
        row.addWidget(self._accent_preview)
        row.addWidget(self._accent_label)
        row.addWidget(btn_pick)
        row.addStretch()
        lay.addLayout(row)
        return card

    def _logs_card(self):
        """Carte d'accès rapide aux logs."""
        card, lay = self._card(
            "📋  Journaux d'installation",
            "En cas de problème lors d'une installation, consultez les logs pour identifier la cause."
        )
        row = QHBoxLayout()
        logs_path = str(APPDATA.logs_dir)

        lbl = QLabel(logs_path)
        lbl.setFont(CF(11))
        lbl.setStyleSheet(f"color: {C['muted']}; font-family: Consolas, monospace;")
        lbl.setWordWrap(True)

        btn_open = QPushButton("📂  Ouvrir le dossier")
        btn_open.setFont(CF(12, True))
        btn_open.setStyleSheet(btn_style(outline=True))
        btn_open.setFixedHeight(38)
        btn_open.clicked.connect(lambda: subprocess.Popen(f'explorer "{logs_path}"'))

        row.addWidget(lbl, 1)
        row.addWidget(btn_open)
        lay.addLayout(row)
        return card

    def _show_status(self, msg, color=None):
        self._status.setText(msg)
        self._status.setStyleSheet(f"color: {color or C['success']};")
        QTimer.singleShot(5000, lambda: self._status.setText(""))

# ══════════════════════════════════════════════════════════════════
#  ONGLET CLÉ USB BOOTABLE - COMING SOON
# ══════════════════════════════════════════════════════════════════
class USBBootableTab(QWidget):
    """Onglet Clé USB avec interface blurry et message centré"""
    def __init__(self):
        super().__init__()
        self._build()
    
    def _build(self):
        from PyQt5.QtWidgets import QGraphicsBlurEffect
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Conteneur principal avec fond
        main_frame = QFrame()
        main_frame.setStyleSheet(f"QFrame {{ background: {C['bg']}; }}")
        main_lay = QVBoxLayout(main_frame)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        
        # Zone du contenu flou (arrière-plan)
        blur_zone = QFrame()
        blur_zone.setStyleSheet(f"QFrame {{ background: {C['surface']}; }}")
        blur_zone_lay = QVBoxLayout(blur_zone)
        blur_zone_lay.setContentsMargins(30, 30, 30, 30)
        blur_zone_lay.setSpacing(20)
        blur_zone_lay.setAlignment(Qt.AlignTop)
        
        # Créer du pseudo-contenu qui sera flou
        cards_data = [
            ("💾 Sélectionner une clé USB", "Choisissez le périphérique USB"),
            ("🎯 Mode de création", "Windows Bootable / Linux Bootable"),
            ("📀 Image ISO", "Fichier local ou téléchargement"),
            ("⚙️ Options avancées", "Système de fichiers et cluster"),
        ]
        
        for title, subtitle in cards_data:
            card = QFrame()
            card.setFixedHeight(80)
            card.setStyleSheet(f"QFrame {{ background: {C['surface2']}; border: 1px solid {C['border']}; border-radius: 10px; }}")
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
            
            blur_zone_lay.addWidget(card)
        
        # Ajouter du stretch
        blur_zone_lay.addStretch()
        
        # Appliquer un effet de blur sur la zone
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(12)
        blur_zone.setGraphicsEffect(blur_effect)
        
        main_lay.addWidget(blur_zone, 1)
        
        # Overlay centré avec le message
        overlay = QFrame()
        overlay.setStyleSheet("background: transparent;")
        overlay_lay = QVBoxLayout(overlay)
        overlay_lay.setContentsMargins(0, 0, 0, 0)
        overlay_lay.setSpacing(0)
        overlay_lay.setAlignment(Qt.AlignCenter)
        
        # Message centré clair
        msg_container = QWidget()
        msg_container.setStyleSheet("background: transparent;")
        msg_lay = QVBoxLayout(msg_container)
        msg_lay.setContentsMargins(0, 0, 0, 0)
        msg_lay.setSpacing(20)
        msg_lay.setAlignment(Qt.AlignCenter)
        
        # Récupérer le texte de traduction
        coming_soon_text = TR.t("clefbootabletext")
        
        # Texte du message
        msg = QLabel(coming_soon_text)
        msg.setFont(CF(16, True))
        msg.setAlignment(Qt.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {C['accent']}; background: transparent;")
        msg.setMaximumWidth(600)
        msg_lay.addWidget(msg)
        
        overlay_lay.addWidget(msg_container, alignment=Qt.AlignCenter)
        
        main_lay.addWidget(overlay, 1)
        layout.addWidget(main_frame, 1)
        
        # Barre de footer (non floue)
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet(f"QFrame {{ background: {C['surface']}; border-top: 1px solid {C['border']}; }}")
        footer_lay = QHBoxLayout(footer)
        footer_lay.setContentsMargins(22, 0, 22, 0)
        
        footer_text = QLabel("Fonctionnalité en développement • V" + APP_VERSION)
        footer_text.setFont(CF(10))
        footer_text.setStyleSheet(f"color: {C['muted']};")
        
        footer_lay.addStretch()
        footer_lay.addWidget(footer_text)
        footer_lay.addStretch()
        layout.addWidget(footer)

# ══════════════════════════════════════════════════════════════════
#  DIALOGUE À PROPOS
# ══════════════════════════════════════════════════════════════════
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"À propos de {APP_NAME} ™")
        self.setMinimumSize(580, 480)
        self.resize(620, 520)
        self.setStyleSheet(f"background: {C['surface']}; color: {C['text']};")
        if ICON_SMALL.exists(): self.setWindowIcon(QIcon(str(ICON_SMALL)))
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

        # Zone de texte avec scroll pour ne rien couper
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"background: transparent; border: none;")
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

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {C['border']}; background: {C['border']}; max-height: 1px;")
        layout.addWidget(sep)

        # Boutons GitHub + Discord
        links_row = QHBoxLayout()
        links_row.setSpacing(14)

        btn_github = QPushButton("  GitHub")
        btn_github.setFont(CF(13, True))
        btn_github.setFixedHeight(44)
        btn_github.setStyleSheet(btn_style(outline=True))
        btn_github.setCursor(Qt.PointingHandCursor)
        btn_github.clicked.connect(lambda: QUrl and __import__('webbrowser').open("https://github.com/JojoInfoMaker/KeeraTools"))

        btn_discord = QPushButton("  Discord")
        btn_discord.setFont(CF(13, True))
        btn_discord.setFixedHeight(44)
        btn_discord.setStyleSheet(btn_style("#5865F2"))
        btn_discord.setCursor(Qt.PointingHandCursor)
        btn_discord.clicked.connect(lambda: __import__('webbrowser').open("https://discord.gg/UJzAqHPCs8"))

        links_row.addWidget(btn_github)
        links_row.addWidget(btn_discord)
        layout.addLayout(links_row)

        # Bouton Fermer
        btn = QPushButton("Fermer")
        btn.setFont(CF(13, True))
        btn.setStyleSheet(btn_style(C["accent"]))
        btn.setFixedHeight(42)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

# ══════════════════════════════════════════════════════════════════
#  DIALOGUE THÈME
# ══════════════════════════════════════════════════════════════════
class ThemeDialog(QDialog):
    theme_applied = pyqtSignal()  # Signal pour rafraîchir la fenêtre principale

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

        # Titre
        title = QLabel("🎨  Choisissez votre thème")
        title.setFont(CF(16, True))
        title.setStyleSheet(f"color: {C['text']};")
        root.addWidget(title)

        sub = QLabel("Le thème sera appliqué immédiatement après confirmation.")
        sub.setFont(CF(11))
        sub.setStyleSheet(f"color: {C['muted']};")
        root.addWidget(sub)

        # Grille des thèmes prédéfinis
        themes_frame = QFrame()
        themes_frame.setStyleSheet(f"QFrame {{ background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 10px; }}")
        themes_grid_lay = QGridLayout(themes_frame)
        themes_grid_lay.setContentsMargins(16, 14, 16, 14)
        themes_grid_lay.setSpacing(10)

        self._theme_btns = {}
        preset_keys = [k for k in THEMES if k != "custom"]
        for i, key in enumerate(preset_keys):
            theme = THEMES[key]
            btn = self._make_theme_btn(key, theme)
            self._theme_btns[key] = btn
            themes_grid_lay.addWidget(btn, i // 3, i % 3)

        root.addWidget(themes_frame)

        # Section Custom
        custom_label = QLabel("🎨  Mode Personnalisé — Couleur par couleur")
        custom_label.setFont(CF(13, True))
        custom_label.setStyleSheet(f"color: {C['text']};")
        root.addWidget(custom_label)

        custom_scroll = QScrollArea()
        custom_scroll.setWidgetResizable(True)
        custom_scroll.setFixedHeight(200)
        custom_scroll.setStyleSheet(f"background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 8px;")
        custom_container = QWidget()
        custom_container.setStyleSheet(f"background: {C['bg']};")
        custom_grid = QGridLayout(custom_container)
        custom_grid.setContentsMargins(12, 10, 12, 10)
        custom_grid.setSpacing(8)

        color_keys = list(THEME_COLOR_LABELS.keys())
        for i, key in enumerate(color_keys):
            label_text = THEME_COLOR_LABELS[key]
            row_lay = QHBoxLayout()

            lbl = QLabel(label_text)
            lbl.setFont(CF(11))
            lbl.setFixedWidth(170)
            lbl.setStyleSheet(f"color: {C['text']};")

            preview = QLabel()
            preview.setFixedSize(28, 28)
            current_val = self._custom_colors.get(key, C.get(key, "#888888"))
            preview.setStyleSheet(f"background: {current_val}; border-radius: 5px; border: 1px solid {C['border']};")
            preview.setCursor(Qt.PointingHandCursor)

            hex_lbl = QLabel(current_val)
            hex_lbl.setFont(CF(10))
            hex_lbl.setStyleSheet(f"color: {C['muted']};")
            hex_lbl.setFixedWidth(80)

            def make_picker(k, prev_widget, hex_widget):
                def pick():
                    from PyQt5.QtWidgets import QColorDialog
                    current = self._custom_colors.get(k, "#888888")
                    color = QColorDialog.getColor(QColor(current), self, f"Couleur : {THEME_COLOR_LABELS.get(k, k)}")
                    if color.isValid():
                        hex_val = color.name()
                        self._custom_colors[k] = hex_val
                        prev_widget.setStyleSheet(f"background: {hex_val}; border-radius: 5px; border: 1px solid {C['border']};")
                        hex_widget.setText(hex_val)
                        # Auto-select custom theme
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

        # Bouton pour copier le thème actif comme base custom
        copy_btn = QPushButton("📋  Copier le thème actif comme base personnalisée")
        copy_btn.setFont(CF(11))
        copy_btn.setStyleSheet(btn_style(outline=True))
        copy_btn.setFixedHeight(34)
        copy_btn.clicked.connect(self._copy_active_to_custom)
        root.addWidget(copy_btn, alignment=Qt.AlignLeft)

        # Boutons bas
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

        # Sélectionner le thème actif
        self._select_theme(self._current_theme_key)

    def _make_theme_btn(self, key, theme):
        """Crée un bouton de prévisualisation de thème."""
        btn = QFrame()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(190, 70)
        btn.setProperty("theme_key", key)

        lay = QHBoxLayout(btn)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(10)

        # Mini preview: rectangles colorés
        preview_widget = QWidget()
        preview_widget.setFixedSize(36, 36)
        preview_widget.setStyleSheet(f"background: {theme.get('bg', '#000')}; border-radius: 6px; border: 2px solid {theme.get('border', '#333')};")

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
            btn.setStyleSheet(f"QFrame {{ background: {C['selected']}; border: 2px solid {C['accent']}; border-radius: 9px; }}")
        else:
            btn.setStyleSheet(f"QFrame {{ background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 9px; }}"
                              f"QFrame:hover {{ border: 1px solid {C['accent']}55; background: {C['surface2']}; }}")

    def _select_theme(self, key):
        self._current_theme_key = key
        for k, btn in self._theme_btns.items():
            self._update_btn_style(btn, k == key)

    def _copy_active_to_custom(self):
        """Copie les couleurs du thème actif dans le mode custom."""
        active_key = APPDATA.get("theme", "dark")
        base = THEMES.get(active_key, THEMES["dark"])
        for key in THEME_COLOR_LABELS.keys():
            val = base.get(key, C.get(key, "#888888"))
            self._custom_colors[key] = val
            if key in self._color_pickers:
                prev, hex_lbl = self._color_pickers[key]
                prev.setStyleSheet(f"background: {val}; border-radius: 5px; border: 1px solid {C['border']};")
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


# ══════════════════════════════════════════════════════════════════
#  SYSTÈME DE MISE À JOUR (INTÉGRÉ)
# ══════════════════════════════════════════════════════════════════
class AppUpdater:
    """
    Gère la vérification et l'installation des mises à jour depuis GitHub
    """

    GITHUB_REPO = "JojoInfoMaker/KeeraTools"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    EXE_NAME = "KeeraTools.exe"
    TIMEOUT = 10

    def __init__(self, current_version: str, app_dir: Path = None):
        """Initialise l'updater"""
        self.current_version = current_version
        
        # Déterminer le répertoire de l'exécutable réel
        if app_dir:
            self.app_dir = Path(app_dir)
        else:
            # Si exécuté via PyInstaller, sys.argv[0] contient le chemin de l'exe
            # Sinon, utiliser le répertoire du script
            exe_location = Path(sys.argv[0]).resolve() if sys.argv[0] else Path(__file__).resolve()
            self.app_dir = exe_location.parent if exe_location.is_file() else exe_location
        
        # Chercher l'exe dans le répertoire (par nom standard ou par script Python)
        self.exe_path = self.app_dir / self.EXE_NAME
        
        # Si l'exe standard n'existe pas, essayer de détecter le vrai exe
        if not self.exe_path.exists() and sys.argv[0]:
            exe_from_argv = Path(sys.argv[0]).resolve()
            if exe_from_argv.exists() and (exe_from_argv.suffix.lower() == '.exe' or exe_from_argv.name == 'python.exe'):
                self.exe_path = exe_from_argv
        
        self.latest_info = None

    def check_for_updates(self, timeout=TIMEOUT) -> dict:
        """Vérifie s'il existe une nouvelle version sur GitHub"""
        try:
            headers = {
                'User-Agent': 'KeeraTools-Updater',
                'Accept': 'application/vnd.github.v3+json'
            }
            req = Request(self.GITHUB_API_URL, headers=headers)
            
            with urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            latest_version_tag = data.get('tag_name', '').lstrip('v')
            
            # Trouver l'asset exe
            exe_asset = None
            for asset in data.get('assets', []):
                if asset['name'].endswith('.exe'):
                    exe_asset = asset
                    break
            
            if not exe_asset:
                return {
                    'has_update': False,
                    'error': 'Aucun fichier .exe trouvé dans la release'
                }
            
            # Comparer les versions
            def parse_version(v_str):
                """Parse une version comme "1.0.5", "v1.0.5", "V1.0.5" en tuple (1, 0, 5)"""
                try:
                    # Convertir en minuscules et supprimer les préfixes v ou V
                    cleaned = v_str.lower().lstrip('v')
                    if not cleaned:
                        return (0,)
                    parts = cleaned.split('.')
                    # Extraire les chiffres et convertir en entiers
                    result = []
                    for p in parts:
                        match = re.match(r'^\d+', p)
                        if match:
                            result.append(int(match.group()))
                    return tuple(result) if result else (0,)
                except:
                    return (0,)
            
            latest_ver = parse_version(latest_version_tag)
            current_ver = parse_version(self.current_version)
            has_update = latest_ver > current_ver
            
            result = {
                'has_update': has_update,
                'latest_version': latest_version_tag,
                'download_url': exe_asset['browser_download_url'],
                'current_version': self.current_version,
                'release_notes': data.get('body', ''),
                'file_size': exe_asset.get('size', 0),
                'created_at': data.get('created_at', ''),
                'download_count': exe_asset.get('download_count', 0)
            }
            
            self.latest_info = result
            return result
            
        except urllib.error.URLError as e:
            return {
                'has_update': False,
                'error': f'Erreur réseau: {str(e)}'
            }
        except Exception as e:
            return {
                'has_update': False,
                'error': f'Erreur: {str(e)}'
            }

    def download_update(self, progress_callback=None) -> tuple:
        """Télécharge la dernière version depuis GitHub"""
        if not self.latest_info or not self.latest_info.get('download_url'):
            return False, "Pas d'URL de téléchargement disponible"
        
        download_url = self.latest_info['download_url']
        temp_dir = Path(tempfile.gettempdir())
        temp_exe = temp_dir / self.EXE_NAME
        
        try:
            req = Request(download_url, headers={'User-Agent': 'KeeraTools-Updater'})
            
            with urlopen(req, timeout=self.TIMEOUT) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192
                
                with open(temp_exe, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)
            
            return True, str(temp_exe)
            
        except Exception as e:
            if temp_exe.exists():
                temp_exe.unlink()
            return False, f"Erreur de téléchargement: {str(e)}"

    def install_update(self, temp_exe_path: str) -> tuple:
        """Installe la mise à jour (remplace l'exécutable au même endroit)"""
        try:
            temp_exe = Path(temp_exe_path)
            if not temp_exe.exists():
                return False, "Fichier temporaire introuvable"
            
            # S'assurer que le répertoire de destination existe
            self.exe_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Créer une sauvegarde de l'ancienne version
            backup_exe = self.exe_path.parent / f"{self.exe_path.stem}.bak"
            if self.exe_path.exists():
                try:
                    if backup_exe.exists():
                        backup_exe.unlink()
                    shutil.copy2(self.exe_path, backup_exe)
                except Exception as e:
                    # Continuer même si la sauvegarde échoue
                    pass
            
            # Remplacer par la nouvelle version
            # Supprimer l'ancienne version d'abord si elle existe
            if self.exe_path.exists():
                try:
                    self.exe_path.unlink()
                except PermissionError:
                    # Le fichier est peut-être en cours d'utilisation
                    # Essayer un renommage temporaire
                    temp_old = self.exe_path.parent / f"{self.exe_path.stem}.old"
                    try:
                        self.exe_path.rename(temp_old)
                    except:
                        pass
            
            shutil.copy2(temp_exe, self.exe_path)
            
            # Supprimer le fichier temporaire
            try:
                temp_exe.unlink()
            except:
                pass
            
            return True, "Mise à jour installée avec succès"
            
        except Exception as e:
            return False, f"Erreur d'installation: {str(e)}"

    def apply_update_and_restart(self, temp_exe_path: str) -> bool:
        """Installe la mise à jour et redémarre l'application"""
        try:
            success, msg = self.install_update(temp_exe_path)
            
            if not success:
                return False
            
            # Redémarrer l'application
            if self.exe_path.exists():
                subprocess.Popen([str(self.exe_path)])
                return True
            else:
                return False
                
        except Exception as e:
            return False

    def restore_backup(self) -> tuple:
        """Restaure la sauvegarde de l'ancienne version"""
        try:
            backup_exe = self.app_dir / f"{self.EXE_NAME}.bak"
            
            if not backup_exe.exists():
                return False, "Pas de sauvegarde disponible"
            
            shutil.copy2(backup_exe, self.exe_path)
            return True, "Sauvegarde restaurée avec succès"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"


# ══════════════════════════════════════════════════════════════════
#  DIALOGUE DE MISE À JOUR
# ══════════════════════════════════════════════════════════════════
class UpdateWorker(QThread):
    """Thread pour vérifier et télécharger les mises à jour"""
    progress = pyqtSignal(int, int)  # bytes_downloaded, total_bytes
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, updater, download=False):
        super().__init__()
        self.updater = updater
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
    """Dialogue pour afficher et installer les mises à jour"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄 Vérifier les mises à jour")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        self.setStyleSheet(f"QDialog {{ background: {C['bg']}; }}")
        if ICON_SMALL.exists():
            self.setWindowIcon(QIcon(str(ICON_SMALL)))
        
        # Passer le répertoire réel où se trouve l'application
        app_dir = Path(sys.argv[0]).resolve().parent if sys.argv[0] else None
        self.updater = AppUpdater(APP_VERSION, app_dir=app_dir) if UPDATER_AVAILABLE else None
        self.update_info = None
        self.downloaded_file = None
        
        self._build()
        self._check_updates()
    
    def _build(self):
        """Construit l'interface du dialogue"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Titre
        title = QLabel("🔄 Vérification des mises à jour")
        title.setFont(CF(14, True))
        title.setStyleSheet(f"color: {C['text']}; background: transparent;")
        layout.addWidget(title)
        
        # Zone d'info
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
        
        # Barre de progression
        self._progress = QProgressBar()
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 6px;
                text-align: center;
                color: {C['text']};
            }}
            QProgressBar::chunk {{
                background: {C['accent']};
            }}
        """)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)
        
        # Boutons
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
        """Lance la vérification des mises à jour en arrière-plan"""
        if not UPDATER_AVAILABLE:
            self._info_text.setText(
                "❌ Erreur: Module de mise à jour non disponible\n\n"
                "Le module 'updater' n'a pas pu être chargé."
            )
            self._btn_update.setEnabled(False)
            return
        
        self._info_text.setText("⏳ Vérification en cours...\n\nVeuillez patienter...")
        
        self._worker = UpdateWorker(self.updater, download=False)
        self._worker.finished.connect(self._on_check_finished)
        self._worker.start()
    
    def _on_check_finished(self, success, data):
        """Appelé quand la vérification est terminée"""
        if not success:
            self._info_text.setText(
                f"❌ Erreur lors de la vérification:\n{data}"
            )
            self._btn_update.setEnabled(False)
            return
        
        self.update_info = json.loads(data)
        
        if not self.update_info.get('has_update'):
            self._info_text.setText(
                f"✅ Vous utilisez la dernière version!\n\n"
                f"Version actuelle: v{self.update_info.get('current_version', '?')}"
            )
            self._btn_update.setEnabled(False)
            return
        
        # Il y a une mise à jour
        info = self.update_info
        text = (
            f"🎉 Une nouvelle version est disponible!\n\n"
            f"Version actuelle: v{info.get('current_version', '?')}\n"
            f"Nouvelle version: v{info.get('latest_version', '?')}\n"
            f"Taille: {info.get('file_size', 0) / (1024*1024):.1f} MB\n\n"
            f"📝 Notes de mise à jour:\n"
            f"{info.get('release_notes', 'Pas de notes')[:500]}"
        )
        self._info_text.setText(text)
        self._btn_update.setEnabled(True)
    
    def _start_download(self):
        """Lance le téléchargement de la mise à jour"""
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
        """Mise à jour de la barre de progression"""
        if total > 0:
            percent = int((downloaded / total) * 100)
            self._progress.setValue(percent)
    
    def _on_download_finished(self, success, result):
        """Appelé quand le téléchargement est terminé"""
        self._progress.setVisible(False)
        self._btn_cancel.setEnabled(True)
        
        if not success:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors du téléchargement:\n{result}"
            )
            self._btn_update.setEnabled(True)
            return
        
        # Téléchargement réussi
        self.downloaded_file = result
        reply = QMessageBox.question(
            self,
            "Installation",
            "La mise à jour a été téléchargée avec succès.\n\n"
            "Voulez-vous redémarrer l'application pour installer la mise à jour?\n\n"
            "L'application sera automatiquement fermée et la nouvelle version sera lancée.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # Installer et redémarrer
            APPDATA.log_install(f"Installation de la mise à jour v{self.update_info.get('latest_version')}")
            self.updater.apply_update_and_restart(result)
            QApplication.quit()
        else:
            # L'utilisateur a choisi de ne pas redémarrer maintenant
            self._info_text.setText(
                "📥 Mise à jour téléchargée et prête à être installée.\n\n"
                "Cliquez sur 'Redémarrer maintenant' pour installer,\n"
                "ou fermez cette fenêtre pour continuer avec la version actuelle."
            )
            self._btn_update.setText("🔄 Redémarrer maintenant")
            self._btn_update.clicked.disconnect()
            self._btn_update.clicked.connect(self._install_now)
            self._btn_update.setEnabled(True)
    
    def _install_now(self):
        """Installe immédiatement la mise à jour"""
        if self.downloaded_file and Path(self.downloaded_file).exists():
            self.updater.apply_update_and_restart(self.downloaded_file)
            QApplication.quit()


# ══════════════════════════════════════════════════════════════════
#  FENÊTRE PRINCIPALE
# ══════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} ™")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 860)
        if ICON_SMALL.exists(): self.setWindowIcon(QIcon(str(ICON_SMALL)))
        self.setStyleSheet(global_css() + f"QMainWindow {{ background: {C['bg']}; }}")
        self._build()

    def _build(self):
        # Supprimer l'ancien widget central s'il existe
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
        header.setStyleSheet(f"QFrame {{ background: {C['surface']}; border-bottom: 1px solid {C['border']}; }}")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 10, 24, 10)
        h.setSpacing(16)
        h.setAlignment(Qt.AlignVCenter)

        if ICON_BIG.exists():
            logo_lbl = QLabel()
            # Charge l'image PNG directement
            px = QPixmap(str(ICON_BIG))
            # Redimensionne à 110px en conservant les proportions
            px = px.scaled(110, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(px)
            logo_lbl.setFixedSize(110, 110)
            logo_lbl.setAlignment(Qt.AlignCenter)
            h.addWidget(logo_lbl)

        ver_badge = QLabel(f"v{APP_VERSION}")
        ver_badge.setFont(CF(11))
        ver_badge.setStyleSheet(f"background: {C['accent']}22; color: {C['accent']}; border: 1px solid {C['accent']}44; border-radius: 11px; padding: 2px 10px;")
        h.addWidget(ver_badge)

        h.addStretch()

        nav_frame = QFrame()
        nav_frame.setStyleSheet(f"QFrame {{ background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 10px; }}")
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

        self._lang_btn = QPushButton("🇫🇷 FR" if TR.lang == "fr" else "🇬🇧 EN")
        self._lang_btn.setFont(CF(12))
        self._lang_btn.setFixedHeight(38)
        self._lang_btn.setStyleSheet(btn_style(outline=True))
        self._lang_btn.clicked.connect(self._toggle_lang)

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

        h.addWidget(self._lang_btn)

        about_btn = QPushButton("ℹ")
        about_btn.setFont(CF(13, True))
        about_btn.setFixedSize(38, 38)
        about_btn.setStyleSheet(btn_style(outline=True))
        about_btn.clicked.connect(lambda: AboutDialog(self).exec_())
        h.addWidget(about_btn)
        return header

    def closeEvent(self, event):
        """Nettoyer les ressources avant la fermeture"""
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
        # Le bouton affiche la langue ACTUELLE (celle dans laquelle on est)
        self._lang_btn.setText("🇫🇷 FR" if new_lang == "fr" else "🇬🇧 EN")
        QMessageBox.information(self, "Info", TR.t("restart_to_apply_lang"))

    def _open_update_dialog(self):
        """Ouvre le dialogue de vérification des mises à jour"""
        if UPDATER_AVAILABLE:
            dlg = UpdateDialog(self)
            dlg.exec_()

    def _open_theme_dialog(self):
        dlg = ThemeDialog(self)
        dlg.theme_applied.connect(self._refresh_theme)
        dlg.exec_()

    def _refresh_theme(self):
        """Recharge tous les styles de l'application après changement de thème."""
        # Mettre à jour la palette Qt globale
        app = QApplication.instance()
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
        # Reconstruire l'interface
        self.setStyleSheet(global_css() + f"QMainWindow {{ background: {C['bg']}; }}")
        self._build()
        self.show()

# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Laisser Windows gérer le DPI (125%) — ne pas ajouter un second facteur
    os.environ.pop("QT_SCALE_FACTOR", None)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    load_comfortaa()

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

    window = MainWindow()
    window.show()
    
    # Vérification automatique des mises à jour au démarrage (après 1 seconde)
    if UPDATER_AVAILABLE:
        def check_startup_updates():
            try:
                # Passer le répertoire réel où se trouve l'application
                app_dir = Path(sys.argv[0]).resolve().parent if sys.argv[0] else None
                updater = AppUpdater(APP_VERSION, app_dir=app_dir)
                info = updater.check_for_updates(timeout=5)
                if info.get('has_update'):
                    # Il y a une mise à jour disponible
                    APPDATA.log_install(f"Mise à jour disponible: v{info.get('latest_version')}")
                    # Afficher une notification discrète
                    reply = QMessageBox.information(
                        window,
                        "🔄 Mise à jour disponible",
                        f"Une nouvelle version ({info.get('latest_version')}) est disponible.\n\n"
                        f"Cliquez sur le bouton 🔄 dans la barre d'outils pour mettre à jour.",
                        QMessageBox.Ok,
                        QMessageBox.Ok
                    )
            except:
                pass  # Silencieusement ignorer les erreurs de vérification
        
        # Programmer la vérification pour qu'elle s'exécute après 2 secondes
        QTimer.singleShot(2000, check_startup_updates)
    
    sys.exit(app.exec_())