"""
Nova Installer App Class
Created by Nixiews
Last updated: 2025-06-14 17:25:40 UTC
"""

import os
import sys
import json
import logging
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import subprocess
from pathlib import Path

from .theme_manager import ThemeManager
from .language_manager import LanguageManager
from .icon_manager import IconManager
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
        else:
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
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize main window
        super().__init__()

        # Set metadata
        self.current_datetime = "2025-06-14 17:25:40"
        self.current_user = "Nixiews"
        logger.info(f"Starting Nova Installer - Time: {self.current_datetime} - User: {self.current_user}")

        # Initialize state variables
        self.selected_apps = set()
        self.selected_category = None
        self.apps_data = {}
        self.category_buttons = {}

        # Initialize managers
        self.theme_manager = ThemeManager()
        self.language_manager = LanguageManager()
        self.icon_manager = IconManager()

        # Load configuration
        self.config = load_config()

        # Setup UI
        self.setup_fonts()
        self.setup_window()
        self.load_apps()

        # Apply theme
        theme_name = self.config.get("theme", {}).get("color_theme", "night-blue")
        self.theme_manager.apply_theme(self, theme_name)

    def setup_window(self):
        """Set up main window"""
        # Configure window
        self.title("Nova Installer")
        self.geometry("1000x600")
        self.minsize(800, 500)

        # Create frames
        self.create_header()
        self.create_main_layout()
        self.create_status_bar()

    def create_header(self):
        """Create header with title and menus"""
        # Header frame
        self.header = ctk.CTkFrame(self)
        self.header.pack(fill="x", padx=20, pady=10)

        # Logo
        logo = self.icon_manager.get_app_icon((32, 32))
        if logo:
            ctk.CTkLabel(
                self.header,
                image=logo,
                text=""
            ).pack(side="left", padx=10)

        # Title
        ctk.CTkLabel(
            self.header,
            text="Nova Installer",
            font=self.fonts["title"]
        ).pack(side="left", padx=10)

        # Menu buttons
        self.create_menu_buttons()

    def create_main_layout(self):
        """Create main layout with sidebar and content"""
        # Main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Sidebar
        self.create_sidebar()

        # Main content
        self.create_main_content()

    def create_sidebar(self):
        """Create sidebar with categories"""
        self.sidebar = ctk.CTkFrame(self.main_container, width=200)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)

        # Categories
        for category, data in self.apps_data.items():
            self.create_category_button(category, data)

    def create_category_button(self, category, data):
        """Create a category button"""
        button = ctk.CTkButton(
            self.sidebar,
            text=self.tr(category),
            command=lambda c=category: self.show_category(c),
            font=self.fonts["normal"]
        )
        button.pack(fill="x", padx=5, pady=2)
        self.category_buttons[category] = button

    def create_main_content(self):
        """Create main content area"""
        self.content_area = ctk.CTkFrame(self.main_container)
        self.content_area.pack(side="left", fill="both", expand=True)

        # Title area
        self.title_area = ctk.CTkFrame(self.content_area)
        self.title_area.pack(fill="x", padx=10, pady=5)

        # Scrollable content
        self.content_frame = ctk.CTkScrollableFrame(self.content_area)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ctk.CTkFrame(self)
        self.status_bar.pack(fill="x", padx=20, pady=(0, 10))

        # Install button
        self.install_button = ctk.CTkButton(
            self.status_bar,
            text=self.tr("install"),
            command=self.install_selected,
            font=self.fonts["normal"]
        )
        self.install_button.pack(side="right", padx=10, pady=5)

        # Selection counter
        self.selection_label = ctk.CTkLabel(
            self.status_bar,
            text=self.tr("no_apps_selected"),
            font=self.fonts["normal"]
        )
        self.selection_label.pack(side="left", padx=10, pady=5)

    def create_menu_buttons(self):
        """Create menu buttons in header"""
        menu_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        menu_frame.pack(side="right", padx=10)

        # File menu
        self.file_menu = ctk.CTkOptionMenu(
            menu_frame,
            values=[self.tr("import"), self.tr("export"), self.tr("exit")],
            command=self.handle_file_menu,
            width=100
        )
        self.file_menu.pack(side="left", padx=5)
        self.file_menu.set(self.tr("file"))

        # Options menu
        self.options_menu = ctk.CTkOptionMenu(
            menu_frame,
            values=[self.tr("colors"), self.tr("language")],
            command=self.handle_options_menu,
            width=100
        )
        self.options_menu.pack(side="left", padx=5)
        self.options_menu.set(self.tr("options"))

        # Help menu
        self.help_menu = ctk.CTkOptionMenu(
            menu_frame,
            values=[self.tr("about"), self.tr("logs")],
            command=self.handle_help_menu,
            width=100
        )
        self.help_menu.pack(side="left", padx=5)
        self.help_menu.set(self.tr("help"))

    def setup_fonts(self):
        """Set up fonts"""
        self.fonts = {
            "title": ("Comfortaa", 20, "bold"),
            "header": ("Comfortaa", 16, "bold"),
            "normal": ("Comfortaa", 12),
            "small": ("Comfortaa", 10)
        }

    def show_category(self, category):
        """Display apps for selected category"""
        self.selected_category = category

        # Clear current content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if category not in self.apps_data:
            return

        # Update category buttons
        for cat, button in self.category_buttons.items():
            if cat == category:
                button.configure(fg_color=self.theme_manager.COLORS["dark"]["button_hover"])
            else:
                button.configure(fg_color=self.theme_manager.COLORS["dark"]["button"])

        # Add category title
        ctk.CTkLabel(
            self.title_area,
            text=self.tr(category),
            font=self.fonts["header"]
        ).pack(pady=5)

        # Add apps
        if "apps" in self.apps_data[category]:
            for app_name, app_data in self.apps_data[category]["apps"].items():
                self.create_app_item(app_name, app_data)

    def create_app_item(self, app_name, app_data):
        """Create an app item in the content area"""
        frame = ctk.CTkFrame(self.content_frame)
        frame.pack(fill="x", padx=5, pady=2)

        var = tk.BooleanVar(value=app_data["id"] in self.selected_apps)

        checkbox = ctk.CTkCheckBox(
            frame,
            text=app_name,
            variable=var,
            command=lambda a=app_data["id"]: self.toggle_app(a),
            font=self.fonts["normal"]
        )
        checkbox.pack(side="left", padx=10, pady=5)

        if "description" in app_data:
            desc_label = ctk.CTkLabel(
                frame,
                text=app_data["description"],
                font=self.fonts["small"],
                text_color="gray",
                wraplength=600
            )
            desc_label.pack(side="left", padx=10, pady=5, fill="x", expand=True)

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

    def toggle_app(self, app_id):
        """Toggle app selection"""
        if app_id in self.selected_apps:
            self.selected_apps.remove(app_id)
        else:
            self.selected_apps.add(app_id)
        self.update_selection_display()

    def update_selection_display(self):
        """Update the selection counter display"""
        count = len(self.selected_apps)
        if count == 0:
            self.selection_label.configure(text=self.tr("no_apps_selected"))
            self.install_button.configure(state="disabled")
        else:
            self.selection_label.configure(text=f"{self.tr('selected')}: {count}")
            self.install_button.configure(state="normal")

    def handle_file_menu(self, choice):
        """Handle file menu selections"""
        try:
            if choice == self.tr("import"):
                self.import_selection()
            elif choice == self.tr("export"):
                self.export_selection()
            elif choice == self.tr("exit"):
                self.quit()
        finally:
            self.after(100, lambda: self.file_menu.set(self.tr("file")))

    def handle_options_menu(self, choice):
        """Handle options menu selections"""
        try:
            if choice == self.tr("colors"):
                self.show_color_dialog()
            elif choice == self.tr("language"):
                self.show_language_dialog()
        finally:
            self.after(100, lambda: self.options_menu.set(self.tr("options")))

    def handle_help_menu(self, choice):
        """Handle help menu selections"""
        try:
            if choice == self.tr("about"):
                self.show_about_dialog()
            elif choice == self.tr("logs"):
                self.open_logs()
        finally:
            self.after(100, lambda: self.help_menu.set(self.tr("help")))

    def show_color_dialog(self):
        """Show color theme dialog"""
        dialog = ColorDialog(self, self.config)
        self.wait_window(dialog)
        if hasattr(dialog, 'result') and dialog.result:
            self.config["theme"] = dialog.result
            save_config(self.config)
            theme_name = dialog.result.get("color_theme", "night-blue")
            self.theme_manager.apply_theme(self, theme_name)

    def show_language_dialog(self):
        """Show language selection dialog"""
        dialog = LanguageDialog(self, self.config)
        self.wait_window(dialog)
        if hasattr(dialog, 'result') and dialog.result:
            self.config["language"] = dialog.result
            save_config(self.config)
            self.language_manager.load_language(dialog.result)
            messagebox.showinfo(
                self.tr("info"),
                self.tr("restart_required")
            )

    def show_about_dialog(self):
        """Show about dialog"""
        dialog = AboutDialog(self, self.config)
        self.wait_window(dialog)

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
                    self.selected_apps = set(data)
                    self.update_selection_display()
                    if self.selected_category:
                        self.show_category(self.selected_category)
        except Exception as e:
            logger.error(f"Error importing selection: {e}")
            messagebox.showerror(
                self.tr("error"),
                self.tr("import_error")
            )

    def export_selection(self):
        """Export app selection to file"""
        if not self.selected_apps:
            messagebox.showinfo(
                self.tr("info"),
                self.tr("no_apps_selected")
            )
            return

        try:
            file_path = filedialog.asksaveasfilename(
                title=self.tr("export_selection"),
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(list(self.selected_apps), f, indent=2)
        except Exception as e:
            logger.error(f"Error exporting selection: {e}")
            messagebox.showerror(
                self.tr("error"),
                self.tr("export_error")
            )

    def install_selected(self):
        """Install selected applications"""
        try:
            if not self.selected_apps:
                messagebox.showinfo(
                    self.tr("info"),
                    self.tr("no_apps_selected")
                )
                return

            dialog = InstallDialog(self, list(self.selected_apps), self.config)
            self.wait_window(dialog)

            # Clear selections after installation
            self.selected_apps.clear()
            self.update_selection_display()

            # Refresh current category
            if self.selected_category:
                self.show_category(self.selected_category)

        except Exception as e:
            logger.error(f"Error installing applications: {e}")
            messagebox.showerror(
                self.tr("error"),
                f"Installation error: {str(e)}"
            )

    def tr(self, key):
        """Translate string key"""
        return self.language_manager.tr(key)

    def run(self):
        """Start the application"""
        self.mainloop()
