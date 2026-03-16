import os
import json
import datetime
import logging
from pathlib import Path


class AppDataManager:
    """Gère le dossier %LOCALAPPDATA%\\KeeraTools et ses sous-dossiers."""

    APP_FOLDER    = "KeeraTools"
    LOG_SUBDIR    = "logs"
    SETTINGS_FILE = "settings.json"

    DEFAULT_SETTINGS = {
        "language":     "fr",
        "accent_color": "#5B6CF9",
        "theme":        "dark",
        "custom_theme": {},
    }

    def __init__(self):
        local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        self.root          = local_app_data / self.APP_FOLDER
        self.logs_dir      = self.root / self.LOG_SUBDIR
        self.settings_path = self.root / self.SETTINGS_FILE

        self._first_run = not self.root.exists()
        self._ensure_dirs()
        self.settings = self._load_settings()
        self._setup_logger()

    # ── Initialisation ────────────────────────────────────────────
    def _ensure_dirs(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def _setup_logger(self):
        today    = datetime.date.today().strftime("%Y-%m-%d")
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
                merged = dict(self.DEFAULT_SETTINGS)
                merged.update(data)
                return merged
            except Exception as e:
                print(f"[WARN] Impossible de lire settings.json : {e}")
        return dict(self.DEFAULT_SETTINGS)

    def save_settings(self):
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
        getattr(self._logger, level, self._logger.info)(message)

    @property
    def is_first_run(self) -> bool:
        return self._first_run


# Instance globale
APPDATA = AppDataManager()
