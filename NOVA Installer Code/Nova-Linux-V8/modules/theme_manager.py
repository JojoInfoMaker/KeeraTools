"""
Nova Installer Theme Manager
Created by Nixiews
Last updated: 2025-06-15 08:48:08 UTC
Version: 3.0.0
"""

import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)

class ThemeManager:
    def __init__(self):
        # Initialize default appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Legacy support - MUST BE DEFINED FIRST
        self.COLORS = {
            "dark": {
                "bg": "#1a1b2e",
                "sidebar": "#232442",
                "button": "#2e3267",
                "button_hover": "#3d4288",
                "text": "#ffffff",
                "text_secondary": "#b3b3cc"
            }
        }

        # Theme definitions
        self.themes = {
            "night-blue": {
                "bg": "#1a1b2e",
                "sidebar": "#232442",
                "button": "#2e3267",
                "button_hover": "#3d4288",
                "text": "#ffffff",
                "text_secondary": "#b3b3cc"
            },
            "forest": {
                "bg": "#1e2b1e",
                "sidebar": "#2a3c2a",
                "button": "#365436",
                "button_hover": "#446944",
                "text": "#e6ffe6",
                "text_secondary": "#b3ccb3"
            },
            "purple-dream": {
                "bg": "#2b1b2e",
                "sidebar": "#3c2442",
                "button": "#543667",
                "button_hover": "#694488",
                "text": "#ffe6ff",
                "text_secondary": "#ccb3cc"
            },
            "ocean": {
                "bg": "#1b2b2e",
                "sidebar": "#24363c",
                "button": "#366054",
                "button_hover": "#447469",
                "text": "#e6ffff",
                "text_secondary": "#b3cccc"
            },
            "sunset": {
                "bg": "#2e1b1b",
                "sidebar": "#3c2424",
                "button": "#674836",
                "button_hover": "#885944",
                "text": "#ffe6e6",
                "text_secondary": "#ccb3b3"
            },
            "mint": {
                "bg": "#1b2e25",
                "sidebar": "#243c32",
                "button": "#367454",
                "button_hover": "#448869",
                "text": "#e6fff2",
                "text_secondary": "#b3ccbf"
            }
        }

        self.current_theme = "night-blue"
        logger.info("Theme Manager initialized")

    def get_theme_colors(self, config=None):
        """Get current theme colors with fallbacks"""
        default_colors = {
            "frame": "#2B2B2B",
            "frame_high": "#333333",
            "frame_low": "#222222",
            "button": "#444444",
            "button_hover": "#4D4D4D",
            "text": "#FFFFFF",
            "text_disabled": "#888888"
        }

        try:
            if config:
                theme = config.get("theme", {})
                color_theme = theme.get("color_theme", "night-blue")
                if color_theme in self.themes:
                    theme_colors = self.themes[color_theme]
                    return {
                        "frame": theme_colors["bg"],
                        "frame_high": theme_colors["sidebar"],
                        "frame_low": theme_colors["bg"],
                        "button": theme_colors["button"],
                        "button_hover": theme_colors["button_hover"],
                        "text": theme_colors["text"],
                        "text_disabled": theme_colors["text_secondary"]
                    }
            return default_colors
        except Exception as e:
            logger.warning(f"Using default colors due to: {e}")
            return default_colors

    def apply_theme(self, app, theme_name):
        """Apply theme to application"""
        try:
            if theme_name not in self.themes:
                logger.warning(f"Theme {theme_name} not found, using night-blue")
                theme_name = "night-blue"

            self.current_theme = theme_name
            colors = self.themes[theme_name]

            # Update legacy COLORS
            self.COLORS["dark"] = colors.copy()

            # Configure root window
            app.configure(fg_color=colors["bg"])

            # Update all widgets
            self._update_widgets(app, colors)

            logger.info(f"Applied theme: {theme_name}")

        except Exception as e:
            logger.error(f"Error applying theme: {e}")
            raise

    def _update_widgets(self, parent, colors):
        """Update all widgets recursively"""
        try:
            # Process all child widgets
            for child in parent.winfo_children():
                # Update current widget based on type
                if isinstance(child, ctk.CTkButton):
                    child.configure(
                        fg_color=colors["button"],
                        hover_color=colors["button_hover"],
                        text_color=colors["text"]
                    )

                elif isinstance(child, ctk.CTkLabel):
                    child.configure(
                        text_color=colors["text"],
                        fg_color="transparent"
                    )

                elif isinstance(child, ctk.CTkFrame):
                    # Check if this is a sidebar
                    if any(x in str(child).lower() for x in ["sidebar", "side_panel", "leftpanel"]):
                        child.configure(fg_color=colors["sidebar"])
                    else:
                        child.configure(fg_color=colors["bg"])

                elif isinstance(child, ctk.CTkScrollableFrame):
                    if any(x in str(child).lower() for x in ["sidebar", "side_panel", "leftpanel"]):
                        child.configure(fg_color=colors["sidebar"])
                    else:
                        child.configure(fg_color=colors["bg"])

                elif isinstance(child, (ctk.CTkRadioButton, ctk.CTkCheckBox)):
                    child.configure(
                        fg_color=colors["button"],
                        text_color=colors["text"],
                        hover_color=colors["button_hover"]
                    )

                elif isinstance(child, ctk.CTkOptionMenu):
                    child.configure(
                        fg_color=colors["button"],
                        text_color=colors["text"],
                        button_color=colors["button_hover"],
                        button_hover_color=colors["button"]
                    )

                # Recursively update child widgets
                self._update_widgets(child, colors)

        except Exception as e:
            logger.error(f"Error updating widgets: {e}")

    def get_available_themes(self):
        """Get list of available themes"""
        return {
            "night-blue": "Night Blue",
            "forest": "Forest",
            "purple-dream": "Purple Dream",
            "ocean": "Ocean",
            "sunset": "Sunset",
            "mint": "Mint"
        }

    def get_current_theme(self):
        """Get current theme settings"""
        return {
            "appearance_mode": "dark",
            "color_theme": self.current_theme
        }
