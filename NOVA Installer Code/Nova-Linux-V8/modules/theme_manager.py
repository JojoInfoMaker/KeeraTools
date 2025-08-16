"""
Nova Installer Theme Manager
Created by Nixiews
Last updated: 2025-08-16 21:07:32 UTC
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

# Constants
CONFIG_DIR = "config"
THEME_CONFIG_FILE = os.path.join(CONFIG_DIR, "theme.json")
DEFAULT_THEME = "night-blue"
DEFAULT_MODE = "dark"

class ThemeManager:
    def __init__(self, config=None):
        """Initialize theme manager with optional config"""
        # Store initial config
        self.config = config or {}
        self.theme_config = self.config.get("theme", {})

        # Define theme mappings
        self._initialize_themes()

        # Load saved theme configuration
        self._load_theme_config()

        logger.info(
            f"Theme Manager initialized with theme: {self.current_theme} "
            f"({self.appearance_mode})"
        )

    def _initialize_themes(self):
        """Initialize theme color definitions"""
        self.themes = {
            "night-blue": {
                "bg": "#1a1b2e",
                "sidebar": "#232442",
                "button": "#2e3267",
                "button_hover": "#3d4288",
                "text": "#ffffff",
                "text_secondary": "#b3b3cc"
            },
            "cyber-punk": {
                "bg": "#0d0221",
                "sidebar": "#1e0443",
                "button": "#ff2975",
                "button_hover": "#ff71a3",
                "text": "#00fff9",
                "text_secondary": "#c7fcfa"
            },
            "forest": {
                "bg": "#1e2b1e",
                "sidebar": "#2a3c2a",
                "button": "#365436",
                "button_hover": "#446944",
                "text": "#e6ffe6",
                "text_secondary": "#b3ccb3"
            },
            "deep-ocean": {
                "bg": "#05161f",
                "sidebar": "#072a3b",
                "button": "#0c4d6c",
                "button_hover": "#116b96",
                "text": "#7fdbff",
                "text_secondary": "#bfeeff"
            },
            "cherry-blossom": {
                "bg": "#2d1922",
                "sidebar": "#3d2230",
                "button": "#cc4e83",
                "button_hover": "#e55c96",
                "text": "#ffd5e5",
                "text_secondary": "#ffecf3"
            }
        }

    def _load_theme_config(self):
        """Load theme configuration from file"""
        try:
            if os.path.exists(THEME_CONFIG_FILE):
                with open(THEME_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.theme_config = json.load(f)
                logger.info(f"Theme configuration loaded from {THEME_CONFIG_FILE}")
            else:
                self.theme_config = {
                    "appearance_mode": DEFAULT_MODE,
                    "color_theme": DEFAULT_THEME
                }
        except Exception as e:
            logger.error(f"Error loading theme config: {e}")
            self.theme_config = {
                "appearance_mode": DEFAULT_MODE,
                "color_theme": DEFAULT_THEME
            }

    def get_current_theme(self):
        """Get current theme colors"""
        theme_name = self.theme_config.get("color_theme", DEFAULT_THEME)
        return self.themes.get(theme_name, self.themes[DEFAULT_THEME])

    @property
    def current_theme(self):
        """Get current theme name"""
        return self.theme_config.get("color_theme", DEFAULT_THEME)

    @property
    def appearance_mode(self):
        """Get current appearance mode"""
        return self.theme_config.get("appearance_mode", DEFAULT_MODE)

    def get_available_themes(self):
        """Get dictionary of available themes"""
        return {
            "night-blue": "Night Blue",
            "cyber-punk": "Cyber Punk",
            "forest": "Forest",
            "deep-ocean": "Deep Ocean",
            "cherry-blossom": "Cherry Blossom"
        }

    def generate_stylesheet(self, theme):
        """Generate Qt stylesheet from theme colors"""
        return f"""
            QMainWindow {{
                background-color: {theme['bg']};
                color: {theme['text']};
            }}

            QFrame {{
                background-color: {theme['sidebar']};
                border: none;
            }}

            QPushButton {{
                background-color: {theme['button']};
                color: {theme['text']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}

            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}

            QPushButton:disabled {{
                background-color: {theme['sidebar']};
                color: {theme['text_secondary']};
            }}

            QLabel {{
                color: {theme['text']};
            }}

            QScrollArea {{
                border: none;
            }}

            QScrollArea > QWidget > QWidget {{
                background-color: {theme['bg']};
            }}

            QScrollBar:vertical {{
                border: none;
                background-color: {theme['sidebar']};
                width: 14px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {theme['button']};
                min-height: 30px;
                border-radius: 7px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {theme['button_hover']};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """

    def save_theme_config(self):
        """Save theme configuration to file"""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(THEME_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.theme_config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving theme config: {e}")
