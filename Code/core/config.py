from pathlib import Path

# ── Chemins ───────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.parent
DATA_DIR   = BASE_DIR / "data"
APPS_JSON  = DATA_DIR / "apps.json"
TRAD_JSON  = DATA_DIR / "traduction.json"
ICON_BIG   = DATA_DIR / "icontest.png"
ICON_SMALL = DATA_DIR / "icon.ico"
FONT_PATH  = DATA_DIR / "Comfortaa-Regular.ttf"

# ── Version ───────────────────────────────────────────────────────
APP_VERSION = "1.1"
APP_NAME    = "KeeraTools"

# ── Palette active (modifiée par apply_theme) ─────────────────────
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

# ── Thèmes prédéfinis ─────────────────────────────────────────────
THEMES = {
    "dark": {
        "name": "🌑  Dark (Défaut)",
        "bg": "#0C0E14", "surface": "#13161F", "surface2": "#181C27",
        "border": "#232840", "accent": "#5B6CF9", "accent2": "#7C3AED",
        "success": "#22C55E", "warning": "#F59E0B", "danger": "#EF4444",
        "text": "#E8ECFF", "muted": "#5A6080", "selected": "#1E2340",
    },
    "white": {
        "name": "☀️  Light / White",
        "bg": "#F4F6FB", "surface": "#FFFFFF", "surface2": "#EEF1F8",
        "border": "#D0D5E8", "accent": "#5B6CF9", "accent2": "#7C3AED",
        "success": "#16A34A", "warning": "#D97706", "danger": "#DC2626",
        "text": "#1A1D2E", "muted": "#7A82A6", "selected": "#E0E4F8",
    },
    "nord": {
        "name": "🧊  Nord / Arctic",
        "bg": "#1E2130", "surface": "#242837", "surface2": "#2C3147",
        "border": "#3B4266", "accent": "#88C0D0", "accent2": "#5E81AC",
        "success": "#A3BE8C", "warning": "#EBCB8B", "danger": "#BF616A",
        "text": "#ECEFF4", "muted": "#7080A0", "selected": "#2E3550",
    },
    "cyberpunk": {
        "name": "⚡  Cyberpunk / Neon",
        "bg": "#060810", "surface": "#0D0F1A", "surface2": "#121525",
        "border": "#1A1F3A", "accent": "#00FFB2", "accent2": "#FF2D78",
        "success": "#00FFB2", "warning": "#FFD700", "danger": "#FF2D78",
        "text": "#E0FFF6", "muted": "#3A7060", "selected": "#0D2020",
    },
    "mocha": {
        "name": "☕  Mocha / Warm",
        "bg": "#1A1512", "surface": "#231E1A", "surface2": "#2C261F",
        "border": "#40342A", "accent": "#E08C4A", "accent2": "#C0522A",
        "success": "#7DBF72", "warning": "#E8C36A", "danger": "#D9534F",
        "text": "#F5ECD7", "muted": "#8A7060", "selected": "#2A2018",
    },
    "midnight": {
        "name": "🌌  Midnight Purple",
        "bg": "#0D0B16", "surface": "#141020", "surface2": "#1A152A",
        "border": "#2A2045", "accent": "#A855F7", "accent2": "#EC4899",
        "success": "#34D399", "warning": "#FBBF24", "danger": "#F87171",
        "text": "#F3EAFF", "muted": "#6050A0", "selected": "#1E1535",
    },
    "custom": {
        "name": "🎨  Personnalisé",
        "bg": "#0C0E14", "surface": "#13161F", "surface2": "#181C27",
        "border": "#232840", "accent": "#5B6CF9", "accent2": "#7C3AED",
        "success": "#22C55E", "warning": "#F59E0B", "danger": "#EF4444",
        "text": "#E8ECFF", "muted": "#5A6080", "selected": "#1E2340",
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

# ── Icônes catégories / apps ──────────────────────────────────────
CAT_ICONS = {
    "Navigateurs": "🌐", "Bureautique": "📄", "Outils Multimédia": "🎬",
    "Outils Professionnel": "🔧", "Utilitaires Windows": "⚙️",
    "Outils Microsoft": "🪟", "Jeux": "🎮", "Developpements": "💻",
    "Communication": "💬",
}

APP_ICONS = {
    "Brave": "🦁", "Firefox": "🦊", "Google Chrome": "🔵",
    "Chromium": "🟣", "Arc": "⚡", "Microsft Edge": "🔵",
    "Tor Browser": "🧅", "Falkon": "🦅", "LibreWolf": "🐺",
    "Waterfox": "🦊", "Floorp": "🦢",
    "LibreOffice": "📘", "Notepad++": "📝", "Adobe Acrobat Reader": "📕",
    "Obsidian": "🟣", "KDE Okular": "👁️", "Foxit PDF Reader": "📄",
    "VLC": "📺", "Krita": "🎨", "IMG Burn": "💿", "ImageGlass": "🖼️",
    "OBS Studio": "🎥", "AIMP": "🎵", "Paint.NET": "🖌️", "Blender": "🎭",
    "iTunes": "🎵", "Jellyfin Server": "📹", "Jellyfin Media Player": "▶️",
    "Audacity": "🎧", "KiCad": "⚡", "FFMpeg": "🎬",
    "Advance IP Scanner": "🔍", "WinSCP": "📤", "WireGuard": "🔐",
    "PuTTY": "💻", "OpenVPN Connect": "🔓", "WireShark": "🐠", "Ventoy": "💿",
    "TeamViewer": "🖱️", "7-Zip": "📦", "WinRAR": "📦", "Rufus": "💿",
    "Recuva": "🗑️", "CCleaner": "🧹", "GPU-Z": "🎮", "CPU-Z": "⚙️",
    "Visual Studio Code": "💜", "Microsoft Office": "📊",
    "Steam": "🎮", "Godot": "👽", "Unity": "🟠",
}


def apply_theme(theme_key: str, custom_overrides: dict = None):
    """Applique un theme dans la palette C globale."""
    theme_data = THEMES.get(theme_key, THEMES["dark"]).copy()
    if theme_key == "custom" and custom_overrides:
        theme_data.update(custom_overrides)
    for k, v in theme_data.items():
        if k != "name":
            C[k] = v


def detect_windows_theme() -> str:
    """
    Lit le registre Windows pour detecter si l'utilisateur
    utilise le mode sombre ou clair.
    Retourne "dark" ou "white".
    """
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            0, winreg.KEY_READ
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        # 0 = mode sombre, 1 = mode clair
        return "white" if value == 1 else "dark"
    except Exception:
        return "dark"  # fallback dark si le registre est inaccessible