"""
Nova Installer App Class
Created by Nixiews
Last updated: 2025-06-15 08:43:33 UTC
"""

import os
import sys
import json
import logging
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from .theme_manager import ThemeManager
from .language_manager import LanguageManager
from .icon_manager import IconManager
from .menu_manager import MenuManager
from .ui_manager import UIManager
from .app_manager import AppManager
from .dialogs.about_dialog import AboutDialog
from .dialogs.color_dialog import ColorDialog
from .dialogs.install_dialog import InstallDialog
from .dialogs.language_dialog import LanguageDialog

logger = logging.getLogger(__name__)

# Constants
CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
APPS_FILE = os.path.join(CONFIG_DIR, "apps.json")

def load_config():
    """Load configuration from file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "language": "en",
            "theme": {
                "appearance_mode": "dark",
                "color_theme": "night-blue"
            }
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {
            "language": "en",
            "theme": {
                "appearance_mode": "dark",
                "color_theme": "night-blue"
            }
        }

def save_config(config):
    """Save configuration to file"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        messagebox.showerror(
            "Error",
            f"Failed to save configuration: {str(e)}"
        )

class NovaInstallerApp(ctk.CTk):
    def __init__(self):
        # Initialize CTk
        super().__init__()

        # Set metadata
        self.current_datetime = "2025-06-15 09:03:46"
        self.current_user = "Nixiews"
        logger.info(f"Starting Nova Installer - Time: {self.current_datetime} - User: {self.current_user}")

        # Load configuration first
        self.config = load_config()

        # Initialize managers with config
        self.theme_manager = ThemeManager(self.config)
        self.language_manager = LanguageManager()
        self.icon_manager = IconManager()
        self.menu_manager = MenuManager(self)

        # Synchronize config with theme manager's config
        if "theme" not in self.config:
            self.config["theme"] = {}
        self.config["theme"].update(self.theme_manager.theme_config)
        save_config(self.config)

        # Load settings
        self.load_language()
        self.load_apps()

        # Setup UI basics
        self.fonts = {
            "title": ("Comfortaa", 20, "bold"),
            "header": ("Comfortaa", 16, "bold"),
            "normal": ("Comfortaa", 12),
            "small": ("Comfortaa", 10)
        }

        # Initialize UI manager
        self.ui_manager = UIManager(self)

        # Initialize app manager
        self.app_manager = AppManager(self)

        # Setup window and UI
        self.ui_manager.setup_window()

        # Set window icon
        self.set_window_icon()

        # Create categories after UI is set up
        self.app_manager.create_categories()

        # Apply theme after UI is created
        self.apply_theme()

        # Bind global click event to dismiss menus
        self.bind('<Button-1>', self.menu_manager.dismiss_active_menu)

        # Show initial category if available
        if self.apps_data:
            first_category = next(iter(self.apps_data))
            self.app_manager.show_category(first_category)

    def load_language(self):
        """Load current language settings"""
        try:
            language = self.config.get("language", "en")
            self.language_manager.load_language(language)
            # Add debugging
            logger.info(f"Language loaded successfully: {language}")
            logger.info(f"Sample translations: file={self.tr('file')}, options={self.tr('options')}")
        except Exception as e:
            logger.error(f"Error loading language: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to load language: {str(e)}"
            )

    def load_apps(self):
        """Load applications data"""
        try:
            if os.path.exists(APPS_FILE):
                with open(APPS_FILE, 'r', encoding='utf-8') as f:
                    self.apps_data = json.load(f)
                logger.info("Applications data loaded successfully")
            else:
                self.apps_data = {}
                logger.warning(f"Apps file not found: {APPS_FILE}")
        except Exception as e:
            logger.error(f"Error loading apps: {e}")
            self.apps_data = {}

    def get_theme_colors(self):
        """Get current theme colors with fallbacks"""
        return self.theme_manager.get_theme_colors(self.config)

    def _update_menu_buttons(self, colors):
        """Update menu button colors"""
        menu_buttons = ['file_button', 'options_button', 'help_button']
        for btn_name in menu_buttons:
            if hasattr(self, btn_name):
                button = getattr(self, btn_name)
                button.configure(
                    fg_color=colors["button"],
                    hover_color=colors["button_hover"],
                    text_color=colors["text"]
                )

    def _update_category_buttons(self, colors):
        """Update category button colors"""
        if hasattr(self.app_manager, 'category_buttons'):
            for button in self.app_manager.category_buttons.values():
                if self.app_manager.selected_category and button.cget("text") == self.tr(self.app_manager.selected_category):
                    button.configure(fg_color=colors["button_hover"])
                else:
                    button.configure(fg_color=colors["button"])

    def show_color_dialog(self):
        """Show color theme dialog"""
        try:
            self.menu_manager.dismiss_active_menu()
            dialog = ColorDialog(self, self.config)
            dialog.title(self.tr("colors"))
            dialog.transient(self)
            dialog.grab_set()
            dialog.focus_set()

            # Center the dialog with larger initial size
            x = self.winfo_x() + (self.winfo_width() // 2) - (450 // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (600 // 2)
            dialog.geometry(f"450x600+{x}+{y}")  # Increased initial size

            self.wait_window(dialog)

            if hasattr(dialog, 'result') and dialog.result:
                self.config["theme"] = dialog.result
                self.theme_manager.config = self.config
                save_config(self.config)  # This will save both app config and theme
                self.apply_theme()
                logger.info("Theme updated successfully")

        except Exception as e:
            logger.error(f"Error in color dialog: {e}")
            if not self.tr("theme_error"):
                error_message = "An error occurred while applying the theme."
            else:
                error_message = self.tr("theme_error")
            messagebox.showerror(self.tr("error"), error_message)

    def show_language_dialog(self):
        """Show language selection dialog"""
        try:
            self.menu_manager.dismiss_active_menu()
            dialog = LanguageDialog(self, self.config)
            dialog.title(self.tr("language"))
            dialog.transient(self)
            dialog.grab_set()
            dialog.focus_set()

            x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (300 // 2)
            dialog.geometry(f"400x300+{x}+{y}")

            self.wait_window(dialog)

            if hasattr(dialog, 'result') and dialog.result:
                self.config["language"] = dialog.result
                save_config(self.config)
                self.language_manager.load_language(dialog.result)
                messagebox.showinfo(self.tr("info"), self.tr("restart_required"))
                logger.info(f"Language updated to: {dialog.result}")
        except Exception as e:
            logger.error(f"Error in language dialog: {e}")
            messagebox.showerror(self.tr("error"), self.tr("language_error"))

    def show_about_dialog(self):
        """Show about dialog"""
        try:
            self.menu_manager.dismiss_active_menu()
            dialog = AboutDialog(self, self.config)
            dialog.title(self.tr("about"))
            dialog.transient(self)
            dialog.grab_set()
            dialog.focus_set()

            x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (300 // 2)
            dialog.geometry(f"400x300+{x}+{y}")

            self.wait_window(dialog)
        except Exception as e:
            logger.error(f"Error in about dialog: {e}")
            messagebox.showerror(self.tr("error"), self.tr("dialog_error"))

    def open_logs(self):
        """Open logs viewer"""
        # This method should be implemented based on your logging setup
        pass

    def import_selection(self):
        """Import app selection from file"""
        try:
            file_path = filedialog.askopenfilename(
                title=self.tr("import_selection"),
                filetypes=[("JSON files", "*.json")]
            )
            if file_path:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.app_manager.selected_apps = set(data)
                    self.app_manager.update_selection_display()
                    if self.app_manager.selected_category:
                        self.app_manager.show_category(self.app_manager.selected_category)
        except Exception as e:
            logger.error(f"Error importing selection: {e}")
            messagebox.showerror(self.tr("error"), self.tr("import_error"))

    def export_selection(self):
        """Export app selection to file"""
        try:
            self.menu_manager.dismiss_active_menu()

            if not self.app_manager.selected_apps:
                messagebox.showinfo(self.tr("info"), self.tr("no_apps_selected"))
                return

            file_path = filedialog.asksaveasfilename(
                title=self.tr("export_selection"),
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                parent=self
            )
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(list(self.app_manager.selected_apps), f, indent=2)
                logger.info("Selection exported successfully")
        except Exception as e:
            logger.error(f"Error exporting selection: {e}")
            messagebox.showerror(self.tr("error"), self.tr("export_error"))

    def install_selected(self):
        """Install selected applications"""
        try:
            if not self.app_manager.selected_apps:
                messagebox.showinfo(self.tr("info"), self.tr("no_apps_selected"))
                return

            dialog = InstallDialog(self, list(self.app_manager.selected_apps), self.config)
            self.wait_window(dialog)

            # Clear selections after installation
            self.app_manager.selected_apps.clear()
            self.app_manager.update_selection_display()

            # Refresh current category
            if self.app_manager.selected_category:
                self.app_manager.show_category(self.app_manager.selected_category)

        except Exception as e:
            logger.error(f"Error installing applications: {e}")
            messagebox.showerror(self.tr("error"), f"Installation error: {str(e)}")

    def apply_theme(self):
        """Apply current theme to all widgets"""
        try:
            colors = self.get_theme_colors()
            appearance_mode = self.config.get("theme", {}).get("appearance_mode", "dark")
            color_theme = self.config.get("theme", {}).get("color_theme", "night-blue")

            # Set global appearance
            ctk.set_appearance_mode(appearance_mode)

            # Update root window
            self.configure(fg_color=colors["bg"])

            # Update all frames
            self._update_frame_colors(self, colors)

            # Update special frames and content
            self._update_special_frames(colors)

            # Update menu buttons
            self._update_menu_buttons(colors)

            # Update category buttons
            self._update_category_buttons(colors)

            logger.info(f"Theme applied successfully: {color_theme} ({appearance_mode})")

        except Exception as e:
            logger.error(f"Error applying theme: {e}")

    def set_window_icon(self):
        """Set the window icon for the taskbar"""
        try:
            # Get icon path from icon manager
            icon_path = self.icon_manager.get_app_icon_path()
            if icon_path:
                # For Windows
                if hasattr(self, 'iconbitmap'):
                    self.iconbitmap(icon_path)
                # For Linux
                self.tk.call('wm', 'iconphoto', self._w, tk.PhotoImage(file=icon_path))
                logger.info("Window icon set successfully")
        except Exception as e:
            logger.error(f"Error setting window icon: {e}")

    def _update_frame_colors(self, parent, colors):
        """Recursively update frame colors"""
        try:
            for child in parent.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    child.configure(fg_color=colors["frame"])
                if isinstance(child, ctk.CTkScrollableFrame):
                    child.configure(fg_color=colors["frame_low"])
                if hasattr(child, 'winfo_children'):
                    self._update_frame_colors(child, colors)
        except Exception as e:
            logger.error(f"Error updating frame colors: {e}")

    def _update_special_frames(self, colors):
        """Update special frames with specific colors"""
        special_frames = {
            'content_frame': colors["frame_low"],
            'categories_frame': colors["frame_low"],
            'sidebar': colors["frame_high"],
            'main_container': colors["frame"],
            'header': colors["frame_high"],
            'status_bar': colors["frame_high"]
        }

        for frame_name, color in special_frames.items():
            if hasattr(self, frame_name):
                frame = getattr(self, frame_name)
                frame.configure(fg_color=color)

    def quit(self):
        """Exit the application"""
        try:
            self.menu_manager.dismiss_active_menu()
            save_config(self.config)
            self.destroy()
            logger.info("Application closed successfully")
        except Exception as e:
            logger.error(f"Error while quitting: {e}")
            self.destroy()

    def tr(self, key):
        """Translate string key"""
        return self.language_manager.tr(key)

    def run(self):
        """Start the application"""
        self.mainloop()
