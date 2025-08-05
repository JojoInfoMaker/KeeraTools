"""
Nova Installer Theme Manager
Created by Nixiews
Last updated: 2025-06-15 09:24:37 UTC
Version: 3.0.0
"""

import os
import json
import logging
import customtkinter as ctk

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

        # Define theme mappings
        self._initialize_themes()

        # Load saved theme configuration
        self._load_theme_config()

        # Set initial appearance
        ctk.set_appearance_mode(self.appearance_mode)
        ctk.set_default_color_theme("blue")  # Base theme

        # Legacy support
        self.COLORS = {"dark": self.themes[self.current_theme].copy()}

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
            },
            "amethyst": {
                "bg": "#2b1b3d",
                "sidebar": "#3b2654",
                "button": "#7042a2",
                "button_hover": "#8c55c2",
                "text": "#e9d5ff",
                "text_secondary": "#f4eaff"
            },
            "ember": {
                "bg": "#2e1810",
                "sidebar": "#432218",
                "button": "#943b24",
                "button_hover": "#b84b2e",
                "text": "#ffcbb8",
                "text_secondary": "#ffe5dc"
            },
            "nordic": {
                "bg": "#242933",
                "sidebar": "#2e3440",
                "button": "#4c566a",
                "button_hover": "#5e6881",
                "text": "#eceff4",
                "text_secondary": "#e5e9f0"
            },
            "midnight": {
                "bg": "#0f0f1b",
                "sidebar": "#161625",
                "button": "#282844",
                "button_hover": "#32325c",
                "text": "#c8c8e6",
                "text_secondary": "#9999cc"
            },
            "emerald": {
                "bg": "#0f2922",
                "sidebar": "#153f35",
                "button": "#1e5749",
                "button_hover": "#266d5c",
                "text": "#a8ffe6",
                "text_secondary": "#d4fff3"
            },
            "royal": {
                "bg": "#1a0f33",
                "sidebar": "#251547",
                "button": "#4a2b8c",
                "button_hover": "#5c36ab",
                "text": "#e6d5ff",
                "text_secondary": "#f3eaff"
            },
            "desert": {
                "bg": "#2b1f15",
                "sidebar": "#3d2c1f",
                "button": "#8c6543",
                "button_hover": "#ab7b52",
                "text": "#ffe6d5",
                "text_secondary": "#fff3ea"
            },
            "carbon": {
                "bg": "#151515",
                "sidebar": "#1f1f1f",
                "button": "#333333",
                "button_hover": "#404040",
                "text": "#f0f0f0",
                "text_secondary": "#cccccc"
            },
            "aurora": {
                "bg": "#0f1926",
                "sidebar": "#152536",
                "button": "#264668",
                "button_hover": "#315886",
                "text": "#adc7e6",
                "text_secondary": "#d6e3f3"
            }
        }

    def get_available_themes(self):
        """Get list of available themes"""
        return {
            "night-blue": "Night Blue",
            "cyber-punk": "Cyber Punk",
            "forest": "Forest",
            "deep-ocean": "Deep Ocean",
            "cherry-blossom": "Cherry Blossom",
            "amethyst": "Amethyst",
            "ember": "Ember",
            "nordic": "Nordic",
            "midnight": "Midnight",
            "emerald": "Emerald",
            "royal": "Royal",
            "desert": "Desert",
            "carbon": "Carbon",
            "aurora": "Aurora"
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
                self._save_theme_config()
                logger.info("Created new theme configuration with defaults")
        except Exception as e:
            logger.error(f"Error loading theme config: {e}")
            self.theme_config = {
                "appearance_mode": DEFAULT_MODE,
                "color_theme": DEFAULT_THEME
            }

        # Set current theme settings
        self.appearance_mode = self.theme_config.get("appearance_mode", DEFAULT_MODE)
        self.current_theme = self.theme_config.get("color_theme", DEFAULT_THEME)

    def _save_theme_config(self):
        """Save current theme configuration to file"""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(THEME_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.theme_config, f, indent=4)
            logger.info(f"Theme configuration saved to {THEME_CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error saving theme config: {e}")

    def apply_theme(self, app, theme_name):
        """Apply theme to application"""
        try:
            # Validate theme
            if theme_name not in self.themes:
                logger.warning(f"Theme {theme_name} not found, using {DEFAULT_THEME}")
                theme_name = DEFAULT_THEME

            # Update current theme
            self.current_theme = theme_name
            self.theme_config["color_theme"] = theme_name

            # Save immediately
            self._save_theme_config()

            # Get colors and update UI
            colors = self.get_theme_colors()

            # Configure root window
            app.configure(fg_color=colors["bg"])

            # Update all widgets and menus
            self._update_widgets(app, colors)
            self._update_menus(app, colors)

            # Update legacy support
            self.COLORS["dark"] = self.themes[theme_name].copy()

            logger.info(f"Applied theme: {theme_name}")

        except Exception as e:
            logger.error(f"Error applying theme: {e}")
            raise

    def get_theme_colors(self, config=None):
        """Get current theme colors with fallbacks"""
        try:
            if self.current_theme in self.themes:
                theme_colors = self.themes[self.current_theme]
                return {
                    "frame": theme_colors["bg"],
                    "frame_high": theme_colors["sidebar"],
                    "frame_low": theme_colors["bg"],
                    "button": theme_colors["button"],
                    "button_hover": theme_colors["button_hover"],
                    "text": theme_colors["text"],
                    "text_disabled": theme_colors["text_secondary"],
                    # Additional mappings for full coverage
                    "bg": theme_colors["bg"],
                    "sidebar": theme_colors["sidebar"]
                }
        except Exception as e:
            logger.warning(f"Error getting theme colors: {e}")

        # Fallback colors
        return {
            "frame": "#2B2B2B",
            "frame_high": "#333333",
            "frame_low": "#222222",
            "button": "#444444",
            "button_hover": "#4D4D4D",
            "text": "#FFFFFF",
            "text_disabled": "#888888",
            "bg": "#2B2B2B",
            "sidebar": "#333333"
        }

    def _update_widgets(self, parent, colors):
        """Update all widgets recursively"""
        try:
            for child in parent.winfo_children():
                self._apply_widget_colors(child, colors)

                # Recursively update children
                if hasattr(child, 'winfo_children'):
                    self._update_widgets(child, colors)
        except Exception as e:
            logger.error(f"Error updating widgets: {e}")

    def _apply_widget_colors(self, widget, colors):
        """Apply colors to a specific widget based on its type"""
        try:
            if isinstance(widget, ctk.CTkButton):
                widget.configure(
                    fg_color=colors["button"],
                    hover_color=colors["button_hover"],
                    text_color=colors["text"],
                    border_width=1,
                    border_color=colors["button_hover"]
                )

            elif isinstance(widget, ctk.CTkLabel):
                widget.configure(
                    text_color=colors["text"],
                    fg_color="transparent"
                )

            elif isinstance(widget, ctk.CTkFrame):
                is_sidebar = any(x in str(widget).lower()
                               for x in ["sidebar", "side_panel", "leftpanel"])
                is_app_item = "app_item" in str(widget).lower() or "application_frame" in str(widget).lower()

                if is_app_item:
                    # Special handling for application presentation frames
                    widget.configure(
                        fg_color=colors["sidebar"],  # Use sidebar color for better contrast
                        border_width=1,
                        border_color=colors["button"]
                    )
                else:
                    widget.configure(
                        fg_color=colors["sidebar"] if is_sidebar else colors["bg"],
                        border_width=1 if is_sidebar else 0,
                        border_color=colors["button"] if is_sidebar else "transparent"
                    )

            elif isinstance(widget, ctk.CTkScrollableFrame):
                is_sidebar = any(x in str(widget).lower()
                               for x in ["sidebar", "side_panel", "leftpanel"])
                is_content = "content_frame" in str(widget).lower()

                widget.configure(
                    fg_color=colors["sidebar"] if (is_sidebar or is_content) else colors["bg"],
                    border_width=1 if (is_sidebar or is_content) else 0,
                    border_color=colors["button"] if (is_sidebar or is_content) else "transparent"
                )

                # Fix for application items in content frame
                if is_content:
                    for child in widget.winfo_children():
                        if isinstance(child, (ctk.CTkFrame, ctk.CTkButton)):
                            # Apply theme colors to all application items
                            child.configure(
                                fg_color=colors["sidebar"],
                                border_width=1,
                                border_color=colors["button"]
                            )
                            # Recursively update any nested frames (app descriptions, etc.)
                            if hasattr(child, 'winfo_children'):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, (ctk.CTkFrame, ctk.CTkButton)):
                                        grandchild.configure(
                                            fg_color=colors["sidebar"],
                                            border_width=1,
                                            border_color=colors["button"]
                                        )

            elif isinstance(widget, (ctk.CTkRadioButton, ctk.CTkCheckBox)):
                widget.configure(
                    fg_color=colors["button"],
                    text_color=colors["text"],
                    hover_color=colors["button_hover"],
                    border_color=colors["text"],
                    border_width=2
                )

            elif isinstance(widget, ctk.CTkOptionMenu):
                widget.configure(
                    fg_color=colors["button"],
                    text_color=colors["text"],
                    button_color=colors["button_hover"],
                    button_hover_color=colors["button"],
                    border_width=1,
                    border_color=colors["button_hover"]
                )

        except Exception as e:
            logger.error(f"Error applying colors to {type(widget).__name__}: {e}")

    def _update_menus(self, app, colors):
        """Update menu colors"""
        try:
            if hasattr(app, 'menu_manager'):
                menu_manager = app.menu_manager
                if hasattr(menu_manager, 'cached_menus'):
                    for menu in menu_manager.cached_menus.values():
                        menu.configure(
                            bg=colors["frame_low"],
                            fg=colors["text"],
                            activebackground=colors["button_hover"],
                            activeforeground=colors["text"]
                        )
        except Exception as e:
            logger.error(f"Error updating menus: {e}")

    def get_available_themes(self):
        """Get list of available themes"""
        return {
            "night-blue": "Night Blue",
            "cyber-punk": "Cyber Punk",
            "forest": "Forest",
            "deep-ocean": "Deep Ocean",
            "cherry-blossom": "Cherry Blossom",
            "amethyst": "Amethyst",
            "ember": "Ember",
            "nordic": "Nordic",
            "midnight": "Midnight",
            "emerald": "Emerald",
            "royal": "Royal",
            "desert": "Desert",
            "carbon": "Carbon",
            "aurora": "Aurora",
            "purple-dream": "Purple Dream",
            "ocean": "Ocean",
            "sunset": "Sunset",
            "mint": "Mint"
        }

    def get_current_theme(self):
        """Get current theme settings"""
        return {
            "appearance_mode": self.appearance_mode,
            "color_theme": self.current_theme
        }
