"""
Nova Installer Language Manager
Created by Nixiews
Last updated: 2025-08-16 21:05:55 UTC
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

class LanguageManager:
    def __init__(self):
        self.translations = {}
        self.load_languages()
        logger.info("Language Manager initialized")

    def load_languages(self):
        """Load language translations from JSON file"""
        try:
            # Get the path to the Languages.json file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(current_dir)
            lang_file = os.path.join(root_dir, "data", "Languages.json")

            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)

            logger.info(f"Successfully loaded languages from {lang_file}")
        except Exception as e:
            logger.error(f"Error loading languages: {e}")
            self.translations = {}

    def get_available_languages(self):
        """Get dictionary of available languages"""
        languages = {
            "en": "English",
            "fr": "Français",
            "es": "Español",
            "de": "Deutsch"
        }
        return languages

    def translate(self, key, language="en"):
        """
        Translate a key to the specified language
        Args:
            key (str): The translation key
            language (str): The target language code (default: "en")
        Returns:
            str: The translated text or the key if translation not found
        """
        try:
            # Get the translations for the specified language
            lang_data = self.translations.get(language, {})
            translations = lang_data.get("translations", {})

            # Return the translation or fall back to English if not found
            translation = translations.get(key)
            if translation is None and language != "en":
                en_translations = self.translations.get("en", {}).get("translations", {})
                translation = en_translations.get(key)

            # If still no translation found, return the key itself
            return translation if translation is not None else key

        except Exception as e:
            logger.error(f"Error translating key '{key}' to {language}: {e}")
            return key
