import json
from pathlib import Path


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] {path}: {e}")
        return {}


def get_app_logo_url(app_name: str, apps_data: dict) -> str | None:
    for cat_apps in apps_data.values():
        if app_name in cat_apps:
            app_data = cat_apps[app_name]
            if isinstance(app_data, dict) and "logo" in app_data:
                return app_data["logo"]
    return None


def get_winget_id(app_name: str, apps_data: dict) -> str | None:
    for cat_apps in apps_data.values():
        if app_name in cat_apps:
            app_data = cat_apps[app_name]
            if isinstance(app_data, dict) and "id" in app_data:
                return app_data["id"]
            elif isinstance(app_data, str):
                return app_data
    return None


class Translator:
    def __init__(self, trad_data: dict):
        self.lang      = "fr"
        self.trad_data = trad_data

    def t(self, key, **kwargs) -> str:
        val = self.trad_data.get(self.lang, {}).get(key, key)
        if kwargs:
            try:
                val = val.format(**kwargs)
            except Exception:
                pass
        return val

    def set_lang(self, lang: str):
        self.lang = lang
