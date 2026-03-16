# Initialisation centralisée — à importer en premier dans main.py
from .appdata_manager import APPDATA
from .config import (
    C, THEMES, THEME_COLOR_LABELS, CAT_ICONS, APP_ICONS,
    APPS_JSON, TRAD_JSON, ICON_BIG, ICON_SMALL, FONT_PATH,
    APP_VERSION, APP_NAME, apply_theme, detect_windows_theme,
)
from .translator import load_json, Translator, get_app_logo_url, get_winget_id

# Chargement des données JSON
APPS_DATA = load_json(APPS_JSON)
TRAD_DATA = load_json(TRAD_JSON)

TR = Translator(TRAD_DATA)


def apply_saved_settings():
    """Charge langue, thème et couleur d'accent depuis les settings persistants."""
    saved_lang = APPDATA.get("language")
    if saved_lang:
        TR.set_lang(saved_lang)

    # Si aucun theme sauvegarde, detecter le theme Windows automatiquement
    default_theme = detect_windows_theme()
    saved_theme   = APPDATA.get("theme", default_theme)
    custom_data   = APPDATA.get("custom_theme", {})

    if custom_data and isinstance(custom_data, dict):
        THEMES["custom"].update(custom_data)

    apply_theme(saved_theme, custom_data if saved_theme == "custom" else None)

    if saved_theme != "custom":
        saved_accent = APPDATA.get("accent_color")
        if saved_accent:
            C["accent"] = saved_accent


apply_saved_settings()