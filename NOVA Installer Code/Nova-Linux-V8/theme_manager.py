"""
Nova Installer Theme Manager
Created by Nixiews
Last updated: 2025-06-13 14:44:45 UTC
"""

import customtkinter as ctk
import json
import os
import logging
import platform
from tkinter import font, messagebox, Canvas, Frame, Text
from datetime import datetime, UTC

# Initialize logger
logger = logging.getLogger("NovaInstaller")
current_user = "Nixiews"
logger.info(f"Theme Manager initialized - Date: 2025-06-13 14:44:45 - User: {current_user}")

class ThemeManager:
    _system_fonts = None
    _current_theme = None
    _themes_file = os.path.join("data", "themes.json")
    _settings_file = os.path.join("data", "theme_settings.json")
    _themes_cache = None
    _update_callbacks = []

    @staticmethod
    def ensure_theme_files():
        """Ensure theme files exist with default content."""
        os.makedirs("data", exist_ok=True)

        # Default themes
        default_themes = {
            "dark": {
                "bg": "#212121",
                "text": "#DCE4EE",
                "button": "#7B68EE",
                "button_hover": "#6a5acd",
                "input_bg": "#212121",
                "border": "#2b2b2b",
                "category_bg": "#212121",
                "category_hover": "#2b2b2b",
                "scroll_bg": "#212121",
                "description_bg": "#212121",
                "frame_bg": "#212121"
            },
            "oled": {
                "bg": "#000000",
                "text": "#ffffff",
                "button": "#7B68EE",
                "button_hover": "#6a5acd",
                "input_bg": "#000000",
                "border": "#1a1a1a",
                "category_bg": "#000000",
                "category_hover": "#1a1a1a",
                "scroll_bg": "#000000",
                "description_bg": "#000000",
                "frame_bg": "#000000"
            },
            "cyberpunk": {
                "bg": "#0D0221",
                "text": "#00FF9F",
                "button": "#FF00FF",
                "button_hover": "#B100B1",
                "input_bg": "#0D0221",
                "border": "#190934",
                "category_bg": "#0D0221",
                "category_hover": "#190934",
                "scroll_bg": "#0D0221",
                "description_bg": "#0D0221",
                "frame_bg": "#0D0221"
            },
            "matrix": {
                "bg": "#000000",
                "text": "#00FF41",
                "button": "#008F11",
                "button_hover": "#00FF41",
                "input_bg": "#000000",
                "border": "#003B00",
                "category_bg": "#000000",
                "category_hover": "#003B00",
                "scroll_bg": "#000000",
                "description_bg": "#000000",
                "frame_bg": "#000000"
            },
            "dracula": {
                "bg": "#282A36",
                "text": "#F8F8F2",
                "button": "#BD93F9",
                "button_hover": "#6272A4",
                "input_bg": "#282A36",
                "border": "#44475A",
                "category_bg": "#282A36",
                "category_hover": "#44475A",
                "scroll_bg": "#282A36",
                "description_bg": "#282A36",
                "frame_bg": "#282A36"
            },
            "nord": {
                "bg": "#2E3440",
                "text": "#ECEFF4",
                "button": "#88C0D0",
                "button_hover": "#81A1C1",
                "input_bg": "#2E3440",
                "border": "#3B4252",
                "category_bg": "#2E3440",
                "category_hover": "#3B4252",
                "scroll_bg": "#2E3440",
                "description_bg": "#2E3440",
                "frame_bg": "#2E3440"
            },
            "gruvbox": {
                "bg": "#282828",
                "text": "#EBDBB2",
                "button": "#B8BB26",
                "button_hover": "#98971A",
                "input_bg": "#282828",
                "border": "#3C3836",
                "category_bg": "#282828",
                "category_hover": "#3C3836",
                "scroll_bg": "#282828",
                "description_bg": "#282828",
                "frame_bg": "#282828"
            },
            "monokai": {
                "bg": "#272822",
                "text": "#F8F8F2",
                "button": "#A6E22E",
                "button_hover": "#66D9EF",
                "input_bg": "#272822",
                "border": "#3E3D32",
                "category_bg": "#272822",
                "category_hover": "#3E3D32",
                "scroll_bg": "#272822",
                "description_bg": "#272822",
                "frame_bg": "#272822"
            }
        }

        # Create themes.json if it doesn't exist
        if not os.path.exists(ThemeManager._themes_file):
            with open(ThemeManager._themes_file, 'w', encoding='utf-8') as f:
                json.dump(default_themes, f, indent=4)
            ThemeManager._themes_cache = default_themes

        # Create theme_settings.json if it doesn't exist
        if not os.path.exists(ThemeManager._settings_file):
            settings = {
                "theme": "dark",
                "last_updated": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                "user": current_user
            }
            with open(ThemeManager._settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)

    @staticmethod
    def register_update_callback(callback):
        """Register a callback to be called when theme is updated."""
        if callback not in ThemeManager._update_callbacks:
            ThemeManager._update_callbacks.append(callback)

    @staticmethod
    def unregister_update_callback(callback):
        """Unregister a theme update callback."""
        if callback in ThemeManager._update_callbacks:
            ThemeManager._update_callbacks.remove(callback)

    @staticmethod
    def notify_theme_update():
        """Notify all registered callbacks about theme update."""
        for callback in ThemeManager._update_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in theme update callback: {e}")

    @staticmethod
    def save_theme_settings(theme_name):
        """Save current theme settings to file."""
        try:
            settings = {
                "theme": theme_name,
                "last_updated": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                "user": current_user
            }

            os.makedirs(os.path.dirname(ThemeManager._settings_file), exist_ok=True)

            with open(ThemeManager._settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save theme settings: {e}")

    @staticmethod
    def load_theme_settings():
        """Load saved theme settings from file."""
        try:
            if os.path.exists(ThemeManager._settings_file):
                with open(ThemeManager._settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get("theme", "dark")
            return "dark"
        except Exception as e:
            logger.error(f"Failed to load theme settings: {e}")
            return "dark"

    @staticmethod
    def get_available_themes():
        """Get list of available themes."""
        try:
            # Ensure theme files exist
            ThemeManager.ensure_theme_files()

            if ThemeManager._themes_cache is None:
                with open(ThemeManager._themes_file, 'r', encoding='utf-8') as f:
                    ThemeManager._themes_cache = json.load(f)
            return list(ThemeManager._themes_cache.keys())
        except Exception as e:
            logger.error(f"Failed to load themes: {e}")
            return ["dark", "oled"]  # Fallback themes

    @staticmethod
    def get_theme_colors(theme_name):
        """Get color scheme for specified theme."""
        try:
            # Ensure theme files exist
            ThemeManager.ensure_theme_files()

            if ThemeManager._themes_cache is None:
                with open(ThemeManager._themes_file, 'r', encoding='utf-8') as f:
                    ThemeManager._themes_cache = json.load(f)

            return ThemeManager._themes_cache.get(theme_name, ThemeManager._themes_cache["dark"])
        except Exception as e:
            logger.error(f"Failed to load theme colors: {e}")
            # Fallback to dark theme colors
            return {
                "bg": "#212121",
                "text": "#DCE4EE",
                "button": "#7B68EE",
                "button_hover": "#6a5acd",
                "input_bg": "#212121",
                "border": "#2b2b2b",
                "category_bg": "#212121",
                "category_hover": "#2b2b2b",
                "scroll_bg": "#212121",
                "description_bg": "#212121",
                "frame_bg": "#212121"
            }

    @staticmethod
    def get_system_font():
        """Get the best available system font for the current platform."""
        if ThemeManager._system_fonts is None:
            system = platform.system()
            ThemeManager._system_fonts = {}

            available_fonts = font.families()

            if system == "Linux":
                preferred_fonts = [
                    "Ubuntu",
                    "Noto Sans",
                    "DejaVu Sans",
                    "Liberation Sans",
                    "Cantarell",
                    "Arial",
                    "Helvetica",
                    "Sans"
                ]
            else:
                preferred_fonts = [
                    "Segoe UI",
                    "Arial",
                    "Helvetica",
                    "Sans"
                ]

            for font_name in preferred_fonts:
                if font_name in available_fonts:
                    ThemeManager._system_fonts["primary"] = font_name
                    break
            else:
                ThemeManager._system_fonts["primary"] = "TkDefaultFont"

        return ThemeManager._system_fonts["primary"]

    @staticmethod
    def update_widget_colors(widget, colors):
        """Update colors of a widget and its children."""
        try:
            if isinstance(widget, ctk.CTkScrollableFrame):
                widget.configure(
                    fg_color=colors["bg"],
                    border_color=colors["border"],
                    corner_radius=6
                )
                if hasattr(widget, '_scrollbar'):
                    widget._scrollbar.configure(
                        fg_color=colors["bg"],
                        button_color=colors["bg"],
                        button_hover_color=colors["category_hover"]
                    )
                if hasattr(widget, '_canvas'):
                    widget._canvas.configure(bg=colors["bg"])
                if hasattr(widget, '_frame'):
                    if isinstance(widget._frame, (Frame, Canvas)):
                        widget._frame.configure(bg=colors["bg"])
                    else:
                        widget._frame.configure(fg_color=colors["bg"])

            elif isinstance(widget, ctk.CTkFrame):
                widget.configure(
                    fg_color=colors["bg"],
                    border_color=colors["border"],
                    corner_radius=6
                )

            elif isinstance(widget, ctk.CTkLabel):
                config = {
                    "text_color": colors["text"],
                    "corner_radius": 6
                }
                if widget.cget("fg_color") != "transparent":
                    config["fg_color"] = colors["bg"]
                widget.configure(**config)

            elif isinstance(widget, ctk.CTkButton):
                widget.configure(
                    fg_color=colors["button"],
                    hover_color=colors["button_hover"],
                    text_color=colors["text"],
                    border_color=colors["border"],
                    corner_radius=6
                )

            elif isinstance(widget, (Canvas, Frame)):
                widget.configure(bg=colors["bg"])
            elif isinstance(widget, Text):
                widget.configure(
                    bg=colors["bg"],
                    fg=colors["text"]
                )

            # Update children
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    ThemeManager.update_widget_colors(child, colors)

        except Exception as e:
            logger.error(f"Failed to update widget colors: {e}")

    @staticmethod
    def apply_theme(cfg, window=None):
        """Apply theme configuration to the application."""
        try:
            # Ensure theme files exist
            ThemeManager.ensure_theme_files()

            # Get theme name and save it
            theme_name = cfg["theme"].get("color_theme", "dark")
            ThemeManager.save_theme_settings(theme_name)
            ThemeManager._current_theme = theme_name

            # Get theme colors
            colors = ThemeManager.get_theme_colors(theme_name)

            # Set appearance mode
            appearance = "dark"  # Force dark mode for better consistency
            ctk.set_appearance_mode(appearance)

            # Set scaling for Linux
            if platform.system() == "Linux":
                ctk.set_widget_scaling(1.0)
                ctk.set_window_scaling(1.0)

            if window:
                try:
                    # Configure the main window
                    window.configure(fg_color=colors["bg"])

                    # Update all widgets
                    for widget in window.winfo_children():
                        ThemeManager.update_widget_colors(widget, colors)

                    # Force update the main window again to ensure consistency
                    window.configure(fg_color=colors["bg"])
                    window.update_idletasks()

                    # Notify all registered callbacks about the theme update
                    ThemeManager.notify_theme_update()

                except Exception as e:
                    logger.error(f"Failed to apply theme to window: {e}")
                    messagebox.showerror("Error", f"Failed to apply theme to window: {str(e)}")

        except Exception as e:
            logger.error(f"Theme application failed: {e}")
            messagebox.showerror("Error", f"Failed to apply theme: {str(e)}")

    @staticmethod
    def initialize_theme(window):
        """Initialize theme on startup."""
        if window:
            theme_name = ThemeManager.load_theme_settings()
            cfg = {"theme": {"color_theme": theme_name}}
            ThemeManager.apply_theme(cfg, window)
