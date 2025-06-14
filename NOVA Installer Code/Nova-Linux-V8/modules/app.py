"""
Nova Installer App Class
Created by Nixiews
Last updated: 2025-06-14 19:31:13 UTC
"""

import os
import sys
import json
import logging
import tkinter as tk
from tkinter import messagebox, filedialog
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
        self.current_datetime = "2025-06-14 19:37:30"
        self.current_user = "Nixiews"
        logger.info(f"Starting Nova Installer - Time: {self.current_datetime} - User: {self.current_user}")

        # Initialize state variables
        self.selected_apps = set()
        self.selected_category = None
        self.apps_data = {}
        self.category_buttons = {}
        self.active_menu = None

        # Initialize managers
        self.theme_manager = ThemeManager()
        self.language_manager = LanguageManager()
        self.icon_manager = IconManager()

        # Load configuration and settings
        self.config = load_config()
        self.load_language()
        self.load_apps()

        # Setup UI
        self.setup_fonts()
        self.setup_window()

        # Apply theme after UI is created
        self.apply_theme()

        # Bind global click event to dismiss menus
        self.bind('<Button-1>', self.dismiss_active_menu)

        # Show initial category if available
        if self.apps_data:
            first_category = next(iter(self.apps_data))
            self.show_category(first_category)

    def load_language(self):
        """Load current language settings"""
        try:
            language = self.config.get("language", "en")
            self.language_manager.load_language(language)
            logger.info(f"Language loaded successfully: {language}")
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

    def setup_fonts(self):
        """Set up fonts"""
        self.fonts = {
            "title": ("Comfortaa", 20, "bold"),
            "header": ("Comfortaa", 16, "bold"),
            "normal": ("Comfortaa", 12),
            "small": ("Comfortaa", 10)
        }

    def setup_window(self):
        """Set up main window"""
        # Configure window
        self.title("Nova Installer")
        self.geometry("1000x600")
        self.minsize(800, 500)

        # Create frames using pack manager
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

        # Create sidebar frame
        self.sidebar = ctk.CTkFrame(self.main_container, width=200)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)

        # Create scrollable frame for categories
        self.categories_frame = ctk.CTkScrollableFrame(self.sidebar)
        self.categories_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create categories
        self.create_categories()

        # Content area
        self.content_area = ctk.CTkFrame(self.main_container)
        self.content_area.pack(side="left", fill="both", expand=True)

        # Title area
        self.title_area = ctk.CTkFrame(self.content_area)
        self.title_area.pack(fill="x", padx=10, pady=5)

        # Content frame
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
            font=self.fonts["normal"],
            state="disabled"
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

        # Store active menu
        self.active_menu = None

        # Get theme colors
        colors = self.get_theme_colors()

        # Create buttons with theme-aware styling
        button_style = {
            "width": 100,
            "font": self.fonts["normal"],
            "fg_color": "transparent",
            "hover_color": colors["button_hover"],
            "text_color": colors["text"]
        }

        # Create buttons with direct command binding
        self.file_button = ctk.CTkButton(
            menu_frame,
            text=self.tr("file"),
            command=self.show_file_menu,
            **button_style
        )
        self.file_button.pack(side="left", padx=5)

        self.options_button = ctk.CTkButton(
            menu_frame,
            text=self.tr("options"),
            command=self.show_options_menu,
            **button_style
        )
        self.options_button.pack(side="left", padx=5)

        self.help_button = ctk.CTkButton(
            menu_frame,
            text=self.tr("help"),
            command=self.show_help_menu,
            **button_style
        )
        self.help_button.pack(side="left", padx=5)

    def get_theme_colors(self):
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
            theme = self.config.get("theme", {})
            appearance_mode = theme.get("appearance_mode", "dark")
            return self.theme_manager.get_colors(appearance_mode) or default_colors
        except Exception as e:
            logger.warning(f"Using default colors due to: {e}")
            return default_colors

    def create_themed_menu(self):
        """Create a themed popup menu"""
        menu = tk.Menu(self, tearoff=0)
        colors = self.get_theme_colors()

        menu.configure(
            bg=colors["frame_low"],
            fg=colors["text"],
            activebackground=colors["button_hover"],
            activeforeground=colors["text"],
            bd=0
        )

        return menu

    def show_file_menu(self, event=None):
        """Show file menu popup"""
        menu = tk.Menu(self, tearoff=0)
        colors = self.get_theme_colors()

        # Configure menu style
        menu.configure(
            bg=colors["frame_low"],
            fg=colors["text"],
            activebackground=colors["button_hover"],
            activeforeground=colors["text"],
            bd=0
        )

        # Add menu items
        menu.add_command(label=self.tr("import"), command=self.import_selection)
        menu.add_command(label=self.tr("export"), command=self.export_selection)
        menu.add_separator()
        menu.add_command(label=self.tr("exit"), command=self.quit)

        # Show at button position
        x = self.file_button.winfo_rootx()
        y = self.file_button.winfo_rooty() + self.file_button.winfo_height()
        menu.post(x, y)

        # Store active menu
        if self.active_menu:
            self.active_menu.unpost()
        self.active_menu = menu

    def show_options_menu(self, event=None):
        """Show options menu popup"""
        menu = tk.Menu(self, tearoff=0)
        colors = self.get_theme_colors()

        # Configure menu style
        menu.configure(
            bg=colors["frame_low"],
            fg=colors["text"],
            activebackground=colors["button_hover"],
            activeforeground=colors["text"],
            bd=0
        )

        # Add menu items
        menu.add_command(label=self.tr("colors"), command=self.show_color_dialog)
        menu.add_command(label=self.tr("language"), command=self.show_language_dialog)

        # Show at button position
        x = self.options_button.winfo_rootx()
        y = self.options_button.winfo_rooty() + self.options_button.winfo_height()
        menu.post(x, y)

        # Store active menu
        if self.active_menu:
            self.active_menu.unpost()
        self.active_menu = menu

    def show_help_menu(self, event=None):
        """Show help menu popup"""
        menu = tk.Menu(self, tearoff=0)
        colors = self.get_theme_colors()

        # Configure menu style
        menu.configure(
            bg=colors["frame_low"],
            fg=colors["text"],
            activebackground=colors["button_hover"],
            activeforeground=colors["text"],
            bd=0
        )

        # Add menu items
        menu.add_command(label=self.tr("about"), command=self.show_about_dialog)
        menu.add_command(label=self.tr("logs"), command=self.open_logs)

        # Show at button position
        x = self.help_button.winfo_rootx()
        y = self.help_button.winfo_rooty() + self.help_button.winfo_height()
        menu.post(x, y)

        # Store active menu
        if self.active_menu:
            self.active_menu.unpost()
        self.active_menu = menu

    def dismiss_active_menu(self, event=None):
        """Dismiss active menu if exists"""
        if self.active_menu:
            self.active_menu.unpost()
            self.active_menu = None

    def create_categories(self):
        """Create category buttons"""
        # Clear existing category buttons
        for widget in self.categories_frame.winfo_children():
            widget.destroy()
        self.category_buttons.clear()

        # Create new category buttons
        for category in self.apps_data:
            button = ctk.CTkButton(
                self.categories_frame,
                text=self.tr(category),
                command=lambda c=category: self.show_category(c),
                font=self.fonts["normal"]
            )
            button.pack(fill="x", padx=5, pady=2)
            self.category_buttons[category] = button

    def show_category(self, category):
        """Display apps for selected category"""
        # Clear previous content
        for widget in self.title_area.winfo_children():
            widget.destroy()
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if category not in self.apps_data:
            return

        self.selected_category = category
        colors = self.get_theme_colors()

        # Update category buttons
        for cat, button in self.category_buttons.items():
            if cat == category:
                button.configure(fg_color=colors["button_hover"])
            else:
                button.configure(fg_color=colors["button"])

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

    def show_color_dialog(self):
        """Show color theme dialog"""
        try:
            # Dismiss any active menu before showing dialog
            self.dismiss_active_menu()

            # Import dialog here to avoid circular imports
            from .dialogs.color_dialog import ColorDialog

            dialog = ColorDialog(self, self.config)
            dialog.grab_set()  # Make dialog modal
            self.wait_window(dialog)

            if hasattr(dialog, 'result') and dialog.result:
                # Update config
                self.config["theme"] = dialog.result
                save_config(self.config)

                # Apply new theme
                self.apply_theme()

                logger.info("Theme updated successfully")
        except Exception as e:
            logger.error(f"Error in color dialog: {e}")
            messagebox.showerror(
                self.tr("error"),
                self.tr("theme_error")
            )

    def show_language_dialog(self):
        """Show language selection dialog"""
        try:
            # Dismiss any active menu before showing dialog
            self.dismiss_active_menu()

            # Import dialog here to avoid circular imports
            from .dialogs.language_dialog import LanguageDialog

            dialog = LanguageDialog(self, self.config)
            dialog.grab_set()  # Make dialog modal
            self.wait_window(dialog)

            if hasattr(dialog, 'result') and dialog.result:
                self.config["language"] = dialog.result
                save_config(self.config)
                self.language_manager.load_language(dialog.result)
                messagebox.showinfo(
                    self.tr("info"),
                    self.tr("restart_required")
                )
        except Exception as e:
            logger.error(f"Error in language dialog: {e}")
            messagebox.showerror(
                self.tr("error"),
                self.tr("language_error")
            )

    def show_about_dialog(self):
        """Show about dialog"""
        try:
            # Dismiss any active menu before showing dialog
            self.dismiss_active_menu()

            # Import dialog here to avoid circular imports
            from .dialogs.about_dialog import AboutDialog

            dialog = AboutDialog(self, self.config)
            dialog.grab_set()  # Make dialog modal
            self.wait_window(dialog)
        except Exception as e:
            logger.error(f"Error in about dialog: {e}")
            messagebox.showerror(
                self.tr("error"),
                self.tr("dialog_error")
            )

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
        try:
            # Dismiss any active menu before showing dialog
            self.dismiss_active_menu()

            if not self.selected_apps:
                messagebox.showinfo(
                    self.tr("info"),
                    self.tr("no_apps_selected")
                )
                return

            file_path = filedialog.asksaveasfilename(
                title=self.tr("export_selection"),
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                parent=self  # Make dialog modal
            )
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(list(self.selected_apps), f, indent=2)
                logger.info("Selection exported successfully")
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

    def apply_theme(self):
        """Apply current theme to all widgets"""
        try:
            colors = self.get_theme_colors()
            appearance_mode = self.config.get("theme", {}).get("appearance_mode", "dark")

            # Set global appearance
            ctk.set_appearance_mode(appearance_mode)

            # Update frames
            frames = [
                'main_container', 'sidebar', 'content_area',
                'title_area', 'header', 'status_bar'
            ]

            for frame_name in frames:
                if hasattr(self, frame_name):
                    frame = getattr(self, frame_name)
                    frame.configure(fg_color=colors["frame_high"])

            # Update special frames
            if hasattr(self, 'content_frame'):
                self.content_frame.configure(fg_color=colors["frame_low"])

            if hasattr(self, 'categories_frame'):
                self.categories_frame.configure(fg_color=colors["frame_low"])

            # Update menu buttons
            menu_buttons = [
                self.file_button,
                self.options_button,
                self.help_button
            ]

            for button in menu_buttons:
                button.configure(
                    hover_color=colors["button_hover"],
                    text_color=colors["text"]
                )

            # Update category buttons
            for button in self.category_buttons.values():
                if self.selected_category and button.cget("text") == self.tr(self.selected_category):
                    button.configure(fg_color=colors["button_hover"])
                else:
                    button.configure(fg_color=colors["button"])

            logger.info("Theme applied successfully")

        except Exception as e:
            logger.error(f"Error applying theme: {e}")
            # Continue without raising error to maintain functionality

    def quit(self):
        """Exit the application"""
        try:
            # Dismiss any active menu before quitting
            self.dismiss_active_menu()

            # Save current config
            save_config(self.config)

            # Destroy the window
            self.destroy()

            logger.info("Application closed successfully")
        except Exception as e:
            logger.error(f"Error while quitting: {e}")
            self.destroy()  # Force quit even if there's an error

    def tr(self, key):
        """Translate string key"""
        return self.language_manager.tr(key)

    def run(self):
        """Start the application"""
        self.mainloop()
