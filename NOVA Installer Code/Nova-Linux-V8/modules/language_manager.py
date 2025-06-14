"""
Nova Installer Language Manager
Created by Nixiews
Last updated: 2025-06-14 16:48:21 UTC
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LanguageManager:
    def __init__(self):
        """Initialize language manager"""
        self.current_language = "en"
        self.translations = {}
        self.languages = {}
        self.data_dir = Path(__file__).parent.parent / "data"
        self.languages_file = self.data_dir / "Languages.json"
        self.load_languages()
        logger.info("Language Manager initialized")

    def load_languages(self):
        """Load available languages"""
        try:
            if self.languages_file.exists():
                with open(self.languages_file, 'r', encoding='utf-8') as f:
                    self.languages = json.load(f)
                logger.info(f"Successfully loaded languages from {self.languages_file}")
            else:
                logger.warning(f"Languages file not found: {self.languages_file}")
                self.languages = {
                    "en": {
                        "name": "English",
                        "translations": {
                            "file": "File",
                            "import": "Import",
                            "export": "Export",
                            "exit": "Exit",
                            "options": "Options",
                            "colors": "Colors",
                            "language": "Language",
                            "help": "Help",
                            "about": "About",
                            "logs": "Logs",
                            "install": "Install",
                            "no_apps_selected": "No apps selected",
                            "selected": "Selected",
                            "info": "Information",
                            "error": "Error",
                            "cancel": "Cancel",
                            "language_changed": "Language Changed",
                            "restart_required": "Please restart the application to apply changes",
                            "import_selection": "Import Selection",
                            "export_selection": "Export Selection",
                            "import_error": "Error importing selection",
                            "export_error": "Error exporting selection"
                        }
                    }
                }
        except Exception as e:
            logger.error(f"Error loading languages: {e}")
            self.languages = {"en": {"name": "English", "translations": {}}}

    def load_language(self, language_code):
        """Load specific language"""
        try:
            if language_code in self.languages:
                self.current_language = language_code
                self.translations = self.languages[language_code].get("translations", {})
                logger.info(f"Successfully loaded language: {language_code}")
            else:
                logger.warning(f"Language not found: {language_code}, falling back to English")
                self.current_language = "en"
                self.translations = self.languages["en"].get("translations", {})
        except Exception as e:
            logger.error(f"Error loading language {language_code}: {e}")
            self.current_language = "en"
            self.translations = self.languages["en"].get("translations", {})

    def save_language(self, language_code):
        """Save language preference"""
        try:
            if language_code in self.languages:
                self.current_language = language_code
                logger.info(f"Language preference saved: {language_code}")
            else:
                logger.warning(f"Invalid language code: {language_code}")
        except Exception as e:
            logger.error(f"Error saving language preference: {e}")

    def get_available_languages(self):
        """Get list of available languages"""
        try:
            return {
                code: data["name"]
                for code, data in self.languages.items()
            }
        except Exception as e:
            logger.error(f"Error getting available languages: {e}")
            return {"en": "English"}

    def get_language_name(self, code):
        """Get language name from code"""
        try:
            return self.languages.get(code, {}).get("name", code)
        except Exception as e:
            logger.error(f"Error getting language name for code {code}: {e}")
            return code

    def tr(self, key):
        """Translate string using current language"""
        try:
            if key in self.translations:
                return self.translations[key]

            # If translation not found, try English
            if key in self.languages.get("en", {}).get("translations", {}):
                logger.warning(f"Translation missing for key '{key}' in {self.current_language}, using English")
                return self.languages["en"]["translations"][key]

            # If still not found, return the key itself
            logger.warning(f"Translation key not found: {key}")
            return key

        except Exception as e:
            logger.error(f"Error translating key '{key}': {e}")
            return key
