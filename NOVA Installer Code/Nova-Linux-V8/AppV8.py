"""
Nova Installer V8
Created by Nixiews
Last updated: 2025-06-13 21:09:46 UTC
"""

import os
import sys
import json
import shutil
import ctypes
import webbrowser
import subprocess
from datetime import datetime
from threading import Thread
from PIL import Image, ImageTk
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

# Constants
CONFIG_FILE = os.path.join("config", "config.json")
DATA_DIR = os.path.join("data")
CONFIG_TRAD = os.path.join(DATA_DIR, "Languages.json")
LOGO_PATH_INFO = os.path.join(DATA_DIR, "icon.png")
LOGO_DIR = os.path.join(DATA_DIR, "icon.png")
GITHUB_REPO = "Nixiews/Nova-Installer"
CURRENT_VERSION = "V8"  # Updated for Linux V8

# Load translations
with open(CONFIG_TRAD, encoding="utf-8") as f:
    LANGUAGES = json.load(f)

current_lang = "fr"  # Default language

# --- Constants and Setup ---
CURRENT_USER = "Nixiews"
CURRENT_DATETIME = "2025-06-13 21:09:46"

# Set app-wide appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Ensure base directories exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "language": "en",
    "theme": {
        "appearance_mode": "dark",
        "color_theme": "dark",
        "custom": {"background": None, "button": None}
    },
    "flatpak": {
        "auto_add_flathub": True,
        "installation_timeout": 300
    }
}

# --- Helper Functions ---
def load_json(path, default=None):
    """Load JSON file with proper error handling."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {path}: {e}")
        return default

def save_json(path, data):
    """Save JSON file with proper error handling."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Create backup of existing file
        if os.path.exists(path):
            backup_path = f"{path}.backup"
            shutil.copy2(path, backup_path)

        # Write new data
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Remove backup if write was successful
        if os.path.exists(f"{path}.backup"):
            os.remove(f"{path}.backup")

    except Exception as e:
        logger.error(f"Error saving JSON to {path}: {e}")
        # Restore from backup if available
        if os.path.exists(f"{path}.backup"):
            shutil.copy2(f"{path}.backup", path)
            os.remove(f"{path}.backup")
        raise

def load_languages():
    """Load language files from data directory"""
    try:
        if not os.path.exists(LANG_FILE):
            logger.error(f"Language file not found: {LANG_FILE}")
            return {"en": {}, "fr": {}}  # Minimal fallback

        with open(LANG_FILE, 'r', encoding='utf-8') as f:
            langs = json.load(f)

            # Get available languages from metadata
            available_langs = langs.get("metadata", {}).get("supported_languages", [])
            if not available_langs:
                logger.error("No supported languages found in metadata")
                return {"en": {}, "fr": {}}

            # Check if language entries exist
            for lang in available_langs:
                for key in langs:
                    if key != "metadata":  # Skip metadata section
                        if lang not in langs[key]:
                            logger.warning(f"Missing translation for '{key}' in language '{lang}'")

            # Log available languages
            logger.info(f"Loaded {len(available_langs)} languages: {', '.join(available_langs)}")

            return langs

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in language file: {e}")
        return {"en": {}, "fr": {}}
    except Exception as e:
        logger.error(f"Error loading languages: {e}")
        return {"en": {}, "fr": {}}

def set_language(self, lang):
    global current_lang
    lang_marker_path = os.path.join(os.path.expanduser("~"), "Documents", "Nova Installer", "lang_marker.txt")
    current_lang = lang

    # Make sure the directory exists
    os.makedirs(os.path.dirname(lang_marker_path), exist_ok=True)

    # Write the language selection with proper encoding
    try:
        with open(lang_marker_path, "w", encoding="utf-8") as f:
            f.write(lang)
    except Exception as e:
        print(f"Error saving language selection: {e}")

    # Restart the application to apply the new language
    python = sys.executable
    try:
        subprocess.Popen([python] + sys.argv)
        self.quit()  # Use quit() instead of destroy() for cleaner exit
    except Exception as e:
        print(f"Error restarting application: {e}")

def load_config():
    """Load and merge configuration with defaults."""
    config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
    merged = DEFAULT_CONFIG.copy()
    merged.update(config)
    merged["theme"] = {**DEFAULT_CONFIG["theme"], **config.get("theme", {})}
    merged["theme"]["custom"] = {**DEFAULT_CONFIG["theme"]["custom"],
                               **config.get("theme", {}).get("custom", {})}
    merged["flatpak"] = {**DEFAULT_CONFIG["flatpak"], **config.get("flatpak", {})}
    return merged

# Load configuration and languages
config = load_config()
LANGUAGES = load_languages()

# Load configuration
config = load_config()

# Load languages from file
LANGUAGES = load_languages()

# --- Flatpak Installation Functions ---
def verify_flatpak_installation(app_id):
    """Verify if a Flatpak application is actually installed."""
    try:
        result = subprocess.run(
            ['flatpak', 'list', '--app', '--columns=application'],
            capture_output=True, text=True, check=True
        )
        installed_apps = result.stdout.strip().split('\n')
        return app_id in installed_apps
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to verify installation of {app_id}: {e}")
        return False

def get_flatpak_info(app_id):
    """Get detailed information about a Flatpak application."""
    try:
        result = subprocess.run(
            ['flatpak', 'info', app_id],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else None
    except subprocess.CalledProcessError:
        return None

def install_flatpak(app_id, system_wide=False, progress_callback=None):
    """Install an application using Flatpak with proper error handling and progress tracking."""
    try:
        # Check if already installed
        if verify_flatpak_installation(app_id):
            if progress_callback:
                progress_callback("Application is already installed")
            return True, "Application is already installed"

        # Check Flatpak installation
        requirements = check_system_requirements()
        if not setup_system_requirements(requirements):
            if progress_callback:
                progress_callback("Failed to set up system requirements")
            return False, "Failed to set up system requirements"

        # Prepare installation command
        install_cmd = ['flatpak', 'install', 'flathub', app_id, '-y']
        if system_wide:
            install_cmd.insert(2, '--system')
        else:
            install_cmd.insert(2, '--user')

        if progress_callback:
            progress_callback(f"Running command: {' '.join(install_cmd)}")

        # Start installation process with real-time output
        process = subprocess.Popen(
            install_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                output_lines.append(line)
                if progress_callback:
                    progress_callback(line)

        # Get the return code
        return_code = process.wait()

        if return_code == 0:
            if verify_flatpak_installation(app_id):
                if progress_callback:
                    progress_callback("Installation verified successfully")
                return True, "\n".join(output_lines)
            else:
                if progress_callback:
                    progress_callback("Installation verification failed")
                return False, "Installation verification failed"
        else:
            if progress_callback:
                progress_callback(f"Installation failed with return code {return_code}")
            return False, "\n".join(output_lines)

    except Exception as e:
        error_msg = f"Installation error: {str(e)}"
        if progress_callback:
            progress_callback(error_msg)
        return False, error_msg

# --- System Check Functions ---
def check_system_requirements():
    """Check if all required system components are available."""
    requirements = {
        "flatpak": False,
        "flathub": False
    }

    try:
        # Check Flatpak
        result = subprocess.run(['flatpak', '--version'],
                             capture_output=True, text=True)
        requirements["flatpak"] = result.returncode == 0

        # Check Flathub repository
        if requirements["flatpak"]:
            result = subprocess.run(['flatpak', 'remotes'],
                                 capture_output=True, text=True)
            requirements["flathub"] = "flathub" in result.stdout.lower()

    except FileNotFoundError:
        pass

    return requirements

def setup_system_requirements(requirements):
    """Set up missing system requirements."""
    if not requirements["flatpak"]:
        logger.warning("Flatpak not found. Please install Flatpak first.")
        messagebox.showwarning(
            tr("warning"),
            tr("flatpak_not_found")
        )
        return False

    if not requirements["flathub"]:
        try:
            subprocess.run([
                'flatpak', 'remote-add', '--if-not-exists',
                'flathub', 'https://flathub.org/repo/flathub.flatpakrepo'
            ], check=True)
            logger.info("Successfully added Flathub repository")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add Flathub repository: {e}")
            return False

    return True

def tr(key, **kwargs):
    txt = LANGUAGES.get(current_lang, {}).get(key, key)
    if kwargs:
        return txt.format(**kwargs)
    return txt

# Font configuration
default_font = ("Comfortaa", 12)
title_font = ("Comfortaa", 20, "bold")
big_title_font = ("Comfortaa", 32, "bold")

selected_apps = []

def center_window(win, width=None, height=None):
    win.update_idletasks()
    if width is None or height is None:
        width = win.winfo_width()
        height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

class ThemeManager:
    """Manages consistent theme across the application"""
    COLORS = {
        "background": "#2b2b2b",
        "topbar": "#23272e",
        "frame": "#2b2b2b",
        "button": "#1f538d",
        "button_hover": "#1a4578",
        "text": "#ffffff"
    }

    @classmethod
    def apply_theme(cls, widget):
        """Recursively applies theme to widget and its children"""
        if isinstance(widget, ctk.CTkFrame):
            widget.configure(fg_color=cls.COLORS["frame"])
        elif isinstance(widget, ctk.CTkButton):
            widget.configure(fg_color=cls.COLORS["button"],
                           hover_color=cls.COLORS["button_hover"])
        elif isinstance(widget, ctk.CTkLabel):
            widget.configure(text_color=cls.COLORS["text"])

        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                cls.apply_theme(child)

class LanguageManager:
    """Manages language selection and persistence"""
    @staticmethod
    def get_language_path():
        return os.path.join(os.path.expanduser("~"), "Documents", "Nova Installer", "lang_marker.txt")

    @staticmethod
    def load_language():
        global current_lang
        lang_path = LanguageManager.get_language_path()
        try:
            if os.path.exists(lang_path):
                with open(lang_path, "r", encoding="utf-8") as f:
                    current_lang = f.read().strip()
            return current_lang
        except Exception:
            return "fr"  # Default to French if there's an error

    @staticmethod
    def save_language(lang):
        lang_path = LanguageManager.get_language_path()
        os.makedirs(os.path.dirname(lang_path), exist_ok=True)
        with open(lang_path, "w", encoding="utf-8") as f:
            f.write(lang)

class LanguageManager:
    """Manages language selection and persistence"""
    @staticmethod
    def get_language_path():
        return os.path.join(os.path.expanduser("~"), "Documents", "Nova Installer", "lang_marker.txt")

    @staticmethod
    def load_language():
        global current_lang
        lang_path = LanguageManager.get_language_path()
        try:
            if os.path.exists(lang_path):
                with open(lang_path, "r", encoding="utf-8") as f:
                    current_lang = f.read().strip()
            return current_lang
        except Exception:
            return "fr"  # Default to French if there's an error

    @staticmethod
    def save_language(lang):
        lang_path = LanguageManager.get_language_path()
        os.makedirs(os.path.dirname(lang_path), exist_ok=True)
        with open(lang_path, "w", encoding="utf-8") as f:
            f.write(lang)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager
        self.setup_window()
        self.setup_language()
        self.create_widgets()
        self.load_config()
        self.refresh_texts()
        self.after(1000, self.check_for_update)

    def setup_window(self):
        self.title("Nova Installer")
        self.geometry("1280x760")
        self.minsize(960, 540)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_language(self):
        global current_lang
        lang_marker_path = LanguageManager.get_language_path()

        if not os.path.exists(lang_marker_path):
            self.show_language_picker()
        else:
            current_lang = LanguageManager.load_language()

    def show_language_picker(self):
        lang_win = ctk.CTkToplevel(self)
        lang_win.title("Choix de la langue / Language selection")
        lang_win.geometry("350x200")
        center_window(lang_win, 350, 200)
        lang_win.resizable(False, False)
        lang_win.attributes("-topmost", True)

        ctk.CTkLabel(
            lang_win,
            text="Veuillez choisir une langue\nPlease select a language",
            font=title_font,
            justify="center"
        ).pack(pady=20)

        def set_lang_and_close(lang):
            LanguageManager.save_language(lang)
            lang_win.destroy()
            self.restart_app()

        ctk.CTkButton(
            lang_win,
            text="Français",
            command=lambda: set_lang_and_close("fr"),
            width=120
        ).pack(pady=5)

        ctk.CTkButton(
            lang_win,
            text="English",
            command=lambda: set_lang_and_close("en"),
            width=120
        ).pack(pady=5)

        self.wait_window(lang_win)

    def create_widgets(self):
        # Top bar
        self.topbar = ctk.CTkFrame(self, height=48, fg_color=ThemeManager.COLORS["topbar"])
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.topbar.grid_propagate(False)
        self.create_topbar_buttons()

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(10,0), pady=10)
        self.sidebar.grid_propagate(False)

        # Center frame
        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        # Bottom frame
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="sw", padx=20, pady=10)

        # Install button and dropdown
        self.create_bottom_controls()

    def create_topbar_buttons(self):
        buttons = [
            ("🏠 " + tr("Home"), lambda: self.show_category(next(iter(self.data)))),
            (tr("export"), self.export_selection),
            (tr("import"), self.import_selection),
            ("Français", lambda: self.set_language("fr")),
            ("English", lambda: self.set_language("en")),
            (tr("Open Logs"), lambda: self.open_logs()),
            ("❓ " + tr("about_title"), self.show_about)
        ]

        for text, command in buttons[:-1]:  # All except the last button
            ctk.CTkButton(
                self.topbar,
                text=text,
                width=90,
                font=default_font,
                command=command
            ).pack(side="left", padx=6, pady=8)

        # About button goes to the right
        ctk.CTkButton(
            self.topbar,
            text=buttons[-1][0],
            width=110,
            font=default_font,
            command=buttons[-1][1]
        ).pack(side="right", padx=8, pady=8)

    def create_bottom_controls(self):
        ctk.CTkButton(
            self.bottom_frame,
            text=tr("install"),
            font=default_font,
            command=lambda: self.install_selected_apps()
        ).pack(side="left", padx=(0,10))

        self.selected_var = tk.StringVar(value=tr("no_app_selected"))
        self.dropdown_btn = ctk.CTkOptionMenu(
            self.bottom_frame,
            variable=self.selected_var,
            values=[tr("no_app_selected")],
            width=220,
            font=default_font
        )
        self.dropdown_btn.pack(side="left")

    def load_config(self):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            self.data = json.load(f)
        self.show_category(next(iter(self.data)))

    def set_language(self, lang):
        global current_lang
        LanguageManager.save_language(lang)
        self.restart_app()

    def restart_app(self):
        python = sys.executable
        subprocess.Popen([python] + sys.argv)
        self.quit()

    def show_category(self, category):
        for widget in self.center_frame.winfo_children():
            widget.destroy()

        # Category title
        ctk.CTkLabel(
            self.center_frame,
            text=tr(category),
            font=(title_font[0], title_font[1], "bold")
        ).pack(pady=(0,10))

        # Apps list
        apps_list = list(self.data[category].items())
        self.checkboxes[category] = {}

        # Create scrollable frame if needed
        if len(apps_list) > 21:
            self.create_scrollable_apps_list(category, apps_list)
        else:
            self.create_simple_apps_list(category, apps_list)

        # Apply theme to new widgets
        ThemeManager.apply_theme(self.center_frame)

    def create_scrollable_apps_list(self, category, apps_list):
        frame_canvas = ctk.CTkFrame(self.center_frame)
        frame_canvas.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            frame_canvas,
            borderwidth=0,
            highlightthickness=0,
            bg=ThemeManager.COLORS["background"]
        )
        scrollbar = ctk.CTkScrollbar(
            frame_canvas,
            orientation="vertical",
            command=canvas.yview
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        scrollable_frame = ctk.CTkFrame(canvas)
        scrollable_frame_id = canvas.create_window(
            (0, 0),
            window=scrollable_frame,
            anchor="nw"
        )

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(scrollable_frame_id, width=canvas.winfo_width())

        scrollable_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_frame_configure)

        self.create_app_checkboxes(scrollable_frame, category, apps_list)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def create_simple_apps_list(self, category, apps_list):
        frame = ctk.CTkFrame(
            self.center_frame,
            fg_color=ThemeManager.COLORS["frame"]
        )
        frame.pack(fill="both", expand=True)
        self.create_app_checkboxes(frame, category, apps_list)

    def create_app_checkboxes(self, parent_frame, category, apps_list):
        for app, app_id in apps_list:
            if app_id not in self.checkbox_vars:
                self.checkbox_vars[app_id] = tk.BooleanVar(
                    value=app_id in selected_apps
                )
            cb = ctk.CTkCheckBox(
                parent_frame,
                text=app,
                font=default_font,
                variable=self.checkbox_vars[app_id],
                command=lambda a=app_id, c=category: self.toggle_app(a, c)
            )
            cb.pack(anchor="w", padx=20, pady=2)
            self.checkboxes[category][app_id] = cb

    def toggle_app(self, app_id, category=None):
        checked = self.checkbox_vars[app_id].get()
        if checked and app_id not in selected_apps:
            selected_apps.append(app_id)
        elif not checked and app_id in selected_apps:
            selected_apps.remove(app_id)

        self.update_selection_display()

    def update_selection_display(self):
        if selected_apps:
            if len(selected_apps) == 1:
                self.selected_var.set(selected_apps[0])
            else:
                self.selected_var.set(f"{len(selected_apps)} {tr('apps_selected')}")
            self.dropdown_btn.configure(values=selected_apps)
        else:
            self.selected_var.set(tr("no_app_selected"))
            self.dropdown_btn.configure(values=[tr("no_app_selected")])

    def refresh_texts(self):
        # Clear and rebuild sidebar
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        # Add logo or title
        logo_path = os.path.join(DATA_DIR, "icon2.ico")
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path).resize((200, 200))
                self.logo = ImageTk.PhotoImage(logo_img)
                ctk.CTkLabel(self.sidebar, image=self.logo, text="").pack(pady=(10, 10))
            except Exception:
                ctk.CTkLabel(self.sidebar, text="Nova Installer", font=big_title_font).pack(pady=(10, 10))
        else:
            ctk.CTkLabel(self.sidebar, text="Nova Installer", font=big_title_font).pack(pady=(10, 10))

        # Categories section
        ctk.CTkLabel(self.sidebar, text=tr("Categories"), font=title_font).pack(pady=(10, 20))

        # Category buttons
        for category in self.data:
            ctk.CTkButton(
                self.sidebar,
                text=tr(category),
                width=200,
                font=default_font,
                command=lambda c=category: self.show_category(c)
            ).pack(pady=5, fill="x")

        # Update bottom controls
        self.update_selection_display()
        self.bottom_frame.winfo_children()[0].configure(text=tr("install"))

        # Apply theme to all widgets
        ThemeManager.apply_theme(self)

    def on_close(self):
        """Clean up and close the application"""
        self.quit()

class InstallDialog(ctk.CTkToplevel):
    """Installation progress dialog"""
    def __init__(self, parent, apps_to_install, cfg):
        super().__init__(parent)

        # Initialize with current time and user
        self.current_datetime = "2025-06-13 20:57:25"
        self.current_user = "Nixiews"

        self.transient(parent)
        self.title(tr("installation_window_title"))
        self.geometry("600x500")
        self.resizable(False, False)

        # Store apps to install
        self.apps_to_install = apps_to_install

        # Inherit fonts
        self.comfortaa_fonts = parent.comfortaa_fonts

        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True)

        # Setup UI sections
        self._setup_header()
        self._setup_installation_type()
        self._setup_progress_section()
        self._setup_buttons()

        # Installation state
        self.installing = False
        self.cancelled = False

        # Initially hide progress section and show only installation type
        self.progress_frame.pack_forget()

        # Log dialog creation
        logger.info(f"Install dialog created - Time: {self.current_datetime} - User: {self.current_user}")

        self.grab_set()

    def _setup_header(self):
        """Setup header section"""
        self.header_frame = ctk.CTkFrame(self.main_container)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 0))

        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text=tr("installation_settings"),
            font=self.comfortaa_fonts["title"]
        )
        self.header_label.pack(pady=10)

    def _setup_installation_type(self):
        """Setup installation type selection section"""
        self.install_type_frame = ctk.CTkFrame(self.main_container)
        self.install_type_frame.pack(fill="x", padx=20, pady=10)

        # Type header
        self.type_header = ctk.CTkLabel(
            self.install_type_frame,
            text=tr("installation_type"),
            font=self.comfortaa_fonts["header"]
        )
        self.type_header.pack(anchor="w", padx=15, pady=10)

        # Installation type selector
        self.type_selector_frame = ctk.CTkFrame(
            self.install_type_frame,
            fg_color="transparent"
        )
        self.type_selector_frame.pack(fill="x", padx=15, pady=5)

        self.system_wide_var = tk.BooleanVar(value=False)

        # User installation option with icon
        self.user_frame = ctk.CTkFrame(
            self.type_selector_frame,
            fg_color="transparent"
        )
        self.user_frame.pack(fill="x", pady=5)

        self.user_radio = ctk.CTkRadioButton(
            self.user_frame,
            text=tr("personal_install"),
            variable=self.system_wide_var,
            value=False,
            font=self.comfortaa_fonts["normal"],
            command=self._on_type_selected
        )
        self.user_radio.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            self.user_frame,
            text="🏠",  # Home icon for user installation
            font=self.comfortaa_fonts["normal"]
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            self.user_frame,
            text=tr("user_install_desc"),
            font=self.comfortaa_fonts["small"],
            text_color="gray"
        ).pack(side="left")

        # System installation option with icon
        self.system_frame = ctk.CTkFrame(
            self.type_selector_frame,
            fg_color="transparent"
        )
        self.system_frame.pack(fill="x", pady=5)

        self.system_radio = ctk.CTkRadioButton(
            self.system_frame,
            text=tr("system_install"),
            variable=self.system_wide_var,
            value=True,
            font=self.comfortaa_fonts["normal"],
            command=self._on_type_selected
        )
        self.system_radio.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            self.system_frame,
            text="🖥️",  # Computer icon for system installation
            font=self.comfortaa_fonts["normal"]
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            self.system_frame,
            text=tr("system_install_desc"),
            font=self.comfortaa_fonts["small"],
            text_color="gray"
        ).pack(side="left")

        # Install button (initially hidden)
        self.install_button = ctk.CTkButton(
            self.install_type_frame,
            text=tr("begin_installation"),
            command=self._start_installation,
            font=self.comfortaa_fonts["normal"],
            height=38,
            fg_color="#2d5a27"  # Green color for install button
        )
        self.install_button.pack(pady=15)
        self.install_button.pack_forget()  # Hide initially

    def _setup_progress_section(self):
        """Setup progress display section"""
        self.progress_frame = ctk.CTkFrame(self.main_container)
        self.progress_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.progress_header = ctk.CTkLabel(
            self.progress_frame,
            text=tr("installation_progress"),
            font=self.comfortaa_fonts["header"]
        )
        self.progress_header.pack(pady=(10, 5))

        self.progress_text = ctk.CTkTextbox(
            self.progress_frame,
            wrap="word",
            font=self.comfortaa_fonts["console"],
            height=200
        )
        self.progress_text.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 10))
        self.progress_bar.set(0)

    def _setup_buttons(self):
        """Setup bottom buttons"""
        self.button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text=tr("cancel"),
            command=self.destroy,
            font=self.comfortaa_fonts["normal"],
            height=38,
            fg_color="transparent",
            border_width=1
        )
        self.cancel_button.pack(side="right", padx=5)

    def _on_type_selected(self):
        """Handle installation type selection"""
        # Show the install button with animation
        self.install_button.pack(pady=15)

        # Update description based on selection
        install_type = "system" if self.system_wide_var.get() else "user"
        self.install_button.configure(
            text=f"{tr('begin_installation')} ({tr(f'{install_type}_install')})"
        )

    def _start_installation(self):
        """Start the installation process"""
        # Disable type selection
        self.user_radio.configure(state="disabled")
        self.system_radio.configure(state="disabled")
        self.install_button.configure(state="disabled")

        # Show progress section
        self.progress_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Update cancel button
        self.cancel_button.configure(
            text=tr("stop_installation"),
            command=self._cancel_installation,
            fg_color="#bf4040",
            border_width=0
        )

        # Start installation
        self._perform_installation(self.apps_to_install)

    def _update_progress(self, text):
        """Update the progress display with styled text"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.progress_text.insert("end", f"[{timestamp}] {text}\n")
            self.progress_text.see("end")
            self.update_idletasks()  # Force update the UI
        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    def _perform_installation(self, apps):
        """Perform the installation with enhanced user feedback"""
        self.installing = True
        total = len(apps)
        successful_installs = []
        failed_installs = []

        # Get installation type
        system_wide = self.system_wide_var.get()
        install_type = tr("system_install") if system_wide else tr("personal_install")

        self._update_progress(f"Starting {install_type.lower()}...")
        self._update_progress("─" * 40)

        for i, app_id in enumerate(apps, 1):
            if self.cancelled:
                break

            # Update progress
            progress = i / total
            self.progress_bar.set(progress)

            # Add installation message
            self._update_progress(f"\nInstalling {app_id}")
            self._update_progress(f"Progress: {i}/{total} ({int(progress*100)}%)")

            # Perform Flatpak installation with real-time output
            def progress_handler(text):
                self._update_progress(text)

            success, message = install_flatpak(app_id, system_wide, progress_handler)

            if success:
                successful_installs.append(app_id)
                self._update_progress(f"✓ Successfully installed {app_id}")

                # Show app info
                app_info = get_flatpak_info(app_id)
                if app_info:
                    self._update_progress("─" * 20)
                    self._update_progress("Application Details:")
                    self._update_progress(app_info)
            else:
                failed_installs.append(app_id)
                self._update_progress(f"❌ Failed to install {app_id}")
                self._update_progress(f"Error: {message}")

            self._update_progress("─" * 40)

        self.installing = False

        # Show installation summary
        self._update_progress("\n" + "═" * 40)
        self._update_progress(f"Installation Summary ({install_type})")
        self._update_progress("═" * 40 + "\n")

        if successful_installs:
            self._update_progress("✓ Successfully Installed:")
            for app in successful_installs:
                self._update_progress(f"  • {app}")

        if failed_installs:
            self._update_progress("\n❌ Failed Installations:")
            for app in failed_installs:
                self._update_progress(f"  • {app}")

        if self.cancelled:
            self._update_progress("\n⚠ Installation was cancelled")

        # Replace buttons with close button
        self.button_frame.destroy()
        ctk.CTkButton(
            self,
            text=tr("close"),
            command=self.destroy,
            font=self.comfortaa_fonts["normal"],
            height=38,
            fg_color="#2d5a27"  # Success green color
        ).pack(pady=(0, 20))

    def _cancel_installation(self):
        """Cancel installation with visual feedback"""
        if self.installing:
            self.cancelled = True
            self._update_progress("\n⚠ Stopping installation...")
            self.cancel_button.configure(
                state="disabled",
                text=tr("stopping"),
                fg_color="#bf4040"
            )
        else:
            self.destroy()

class ColorDialog(ctk.CTkToplevel):
    """
    Nova Installer Color Dialog
    Created by Nixiews
    Last updated: 2025-06-13 16:07:17 UTC
    """
    def __init__(self, parent, cfg):
        super().__init__(parent)

        # Log initialization
        logging.info(f"ColorDialog initialized - Date: 2025-06-13 16:07:17 - User: Nixiews")

        # Inherit fonts from parent
        self.comfortaa_fonts = parent.comfortaa_fonts

        # Initialize theme
        ThemeManager.apply_theme(cfg, self)

        # Configure window
        self.transient(parent)
        self.title(tr("colors"))
        self.geometry("350x400")
        self.minsize(300, 350)
        self.resizable(True, True)

        # Initialize configuration
        self.config = cfg.copy() if cfg else {"theme": {"color_theme": "dark", "custom": {}}}
        self.result = None

        # Ensure theme structure exists
        if "theme" not in self.config:
            self.config["theme"] = {"color_theme": "dark", "custom": {}}
        if "custom" not in self.config["theme"]:
            self.config["theme"]["custom"] = {}

        # Configure main layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create title
        title_label = ctk.CTkLabel(
            self,
            text=tr("select_theme"),
            font=self.comfortaa_fonts["header"]
        )
        title_label.grid(row=0, column=0, pady=15, sticky="ew")

        # Create scrollable content
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=300, height=250)
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Create theme selection section
        self._create_theme_section()

        # Create custom color sections
        self._create_button_color_section()
        self._create_background_color_section()

        # Create preview section
        self._create_preview_section()

        # Create action buttons
        self._create_action_buttons()

        # Initialize preview and focus
        self._update_preview()
        self.grab_set()
        self.focus()

    def _create_theme_section(self):
        """Create the theme selection section"""
        theme_section = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        theme_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            theme_section,
            text=tr("select_theme"),
            font=self.comfortaa_fonts["header"]
        ).pack(anchor="w", pady=(0, 5))

        # Theme selection
        self.theme_var = tk.StringVar(value=self.config["theme"].get("color_theme", "dark"))
        theme_options = ThemeManager.get_available_themes()

        for theme in theme_options:
            theme_button = ctk.CTkRadioButton(
                theme_section,
                text=theme.capitalize(),
                variable=self.theme_var,
                value=theme,
                command=self._on_theme_change,
                font=self.comfortaa_fonts["normal"]
            )
            theme_button.pack(anchor="w", padx=10, pady=2)

    def _create_button_color_section(self):
        """Create the custom button color section"""
        button_section = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        button_section.pack(fill="x", pady=(15, 10))

        ctk.CTkLabel(
            button_section,
            text=tr("custom_button_color"),
            font=self.comfortaa_fonts["header"]
        ).pack(anchor="w", pady=(0, 5))

        button_frame = ctk.CTkFrame(button_section, fg_color="transparent")
        button_frame.pack(fill="x")
        button_frame.grid_columnconfigure(0, weight=1)

        self.btn_color = ctk.CTkEntry(
            button_frame,
            placeholder_text="#color or name",
            font=self.comfortaa_fonts["normal"]
        )
        self.btn_color.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        # Set initial button color
        button_color = self.config["theme"].get("custom", {}).get("button", "")
        if button_color:
            self.btn_color.insert(0, button_color)

        ctk.CTkButton(
            button_frame,
            text=tr("choose"),
            width=80,
            command=self._choose_button_color,
            font=self.comfortaa_fonts["normal"]
        ).grid(row=0, column=1)

    def _create_background_color_section(self):
        """Create the custom background color section"""
        bg_section = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        bg_section.pack(fill="x", pady=(15, 10))

        ctk.CTkLabel(
            bg_section,
            text=tr("custom_background_color"),
            font=self.comfortaa_fonts["header"]
        ).pack(anchor="w", pady=(0, 5))

        bg_frame = ctk.CTkFrame(bg_section, fg_color="transparent")
        bg_frame.pack(fill="x")
        bg_frame.grid_columnconfigure(0, weight=1)

        self.bg_color = ctk.CTkEntry(
            bg_frame,
            placeholder_text="#color or name",
            font=self.comfortaa_fonts["normal"]
        )
        self.bg_color.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        # Set initial background color
        background_color = self.config["theme"].get("custom", {}).get("background", "")
        if background_color:
            self.bg_color.insert(0, background_color)

        ctk.CTkButton(
            bg_frame,
            text=tr("choose"),
            width=80,
            command=self._choose_bg_color,
            font=self.comfortaa_fonts["normal"]
        ).grid(row=0, column=1)

    def _create_preview_section(self):
        """Create the preview section"""
        preview_section = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        preview_section.pack(fill="x", pady=(15, 10))

        ctk.CTkLabel(
            preview_section,
            text=tr("preview"),
            font=self.comfortaa_fonts["header"]
        ).pack(anchor="w", pady=(0, 5))

        self.preview_frame = ctk.CTkFrame(preview_section, height=60)
        self.preview_frame.pack(fill="x", pady=5)

        self.preview_button = ctk.CTkButton(
            self.preview_frame,
            text=tr("example_button"),
            command=self._update_preview,
            font=self.comfortaa_fonts["normal"]
        )
        self.preview_button.pack(pady=15)

    def _create_action_buttons(self):
        """Create the action buttons"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=15, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_frame,
            text=tr("apply"),
            command=self._on_apply,
            font=self.comfortaa_fonts["normal"]
        ).grid(row=0, column=0, padx=10)

        ctk.CTkButton(
            btn_frame,
            text=tr("cancel"),
            command=self.destroy,
            font=self.comfortaa_fonts["normal"]
        ).grid(row=0, column=1, padx=10)

    def _on_theme_change(self):
        """Handle theme change"""
        try:
            selected_theme = self.theme_var.get()
            self.config["theme"]["color_theme"] = selected_theme
            self.config["theme"]["custom"] = {}
            self.btn_color.delete(0, tk.END)
            self.bg_color.delete(0, tk.END)
            ThemeManager.apply_theme(self.config, self)
            self._update_preview()
            logging.info(f"Theme changed to {selected_theme} - Time: 2025-06-13 16:07:17 - User: Nixiews")
        except Exception as e:
            logging.error(f"Error in theme change: {e}")
            messagebox.showerror(tr("error"), str(e))

    def _choose_button_color(self):
        """Handle button color selection"""
        color = colorchooser.askcolor(title=tr("choose_button_color"))
        if color[1]:
            self.btn_color.delete(0, tk.END)
            self.btn_color.insert(0, color[1])
            self._update_preview()
            logging.info(f"Button color changed to {color[1]} - Time: 2025-06-13 16:07:17 - User: Nixiews")

    def _choose_bg_color(self):
        """Handle background color selection"""
        color = colorchooser.askcolor(title=tr("choose_background_color"))
        if color[1]:
            self.bg_color.delete(0, tk.END)
            self.bg_color.insert(0, color[1])
            self._update_preview()
            logging.info(f"Background color changed to {color[1]} - Time: 2025-06-13 16:07:17 - User: Nixiews")

    def _update_preview(self):
        """Update the preview section"""
        try:
            colors = ThemeManager.get_theme_colors(self.theme_var.get())
            custom_bg = self.bg_color.get().strip()
            custom_btn = self.btn_color.get().strip()
            bg_color = custom_bg if custom_bg else colors["bg"]
            btn_color = custom_btn if custom_btn else colors["button"]
            self.preview_frame.configure(fg_color=bg_color)
            self.preview_button.configure(fg_color=btn_color)
        except Exception as e:
            logging.error(f"Error in preview update: {e}")

    def _on_apply(self):
        """Apply the selected theme and colors"""
        try:
            theme = {
                "color_theme": self.theme_var.get(),
                "custom": {
                    "button": self.btn_color.get().strip() or None,
                    "background": self.bg_color.get().strip() or None
                }
            }

            def is_valid_color(color):
                if not color:
                    return True
                if color.lower() in ['dark', 'oled']:
                    return True
                if color.startswith('#') and len(color) in [4, 7]:
                    try:
                        int(color[1:], 16)
                        return True
                    except ValueError:
                        return False
                return False

            if not is_valid_color(theme["custom"]["button"]):
                messagebox.showerror(tr("error"), tr("invalid_button_color"))
                return
            if not is_valid_color(theme["custom"]["background"]):
                messagebox.showerror(tr("error"), tr("invalid_background_color"))
                return

            self.result = theme
            logging.info(f"Theme applied: {theme} - Time: 2025-06-13 16:07:17 - User: Nixiews")
            self.destroy()
        except Exception as e:
            logging.error(f"Error in apply: {e}")
            messagebox.showerror(tr("error"), str(e))

class LanguageDialog(ctk.CTkToplevel):
    """Language selection dialog"""
    def __init__(self, parent, cfg):
        super().__init__(parent)

        self.transient(parent)
        self.title(tr("Select Language"))
        self.geometry("400x500")
        self.resizable(False, False)

        # Inherit fonts
        self.comfortaa_fonts = parent.comfortaa_fonts

        self.config = cfg
        self.result = None

        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_label = ctk.CTkLabel(
            self.main_container,
            text=tr("Select Language"),
            font=self.comfortaa_fonts["header"]
        )
        header_label.pack(pady=(0, 10))

        # Create scrollable frame for languages
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_container)
        self.scrollable_frame.pack(fill="both", expand=True)

        # Language selection
        self.lang_var = tk.StringVar(value=cfg.get("language", "en"))

        # Get available languages (excluding metadata key)
        available_languages = [lang for lang in LANGUAGES.keys() if lang != "metadata"]

        # Language names dictionary
        language_names = {
            "en": "English",
            "fr": "Français",
            "es": "Español",
            "de": "Deutsch",
            "it": "Italiano",
            "pt": "Português",
            "nl": "Nederlands",
            "pl": "Polski",
            "ru": "Русский",
            "zh": "中文",
            "ja": "日本語"
        }

        # Create language buttons
        for lang_code in sorted(available_languages):
            lang_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            lang_frame.pack(fill="x", pady=5)

            # Create language selection button
            lang_button = ctk.CTkRadioButton(
                lang_frame,
                text=f"{language_names.get(lang_code, lang_code)} ({lang_code})",
                variable=self.lang_var,
                value=lang_code,
                font=self.comfortaa_fonts["normal"]
            )
            lang_button.pack(side="left", padx=10)

        # Action buttons
        btn_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            btn_frame,
            text=tr("Apply"),
            command=self._on_apply,
            font=self.comfortaa_fonts["normal"]
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text=tr("Cancel"),
            command=self.destroy,
            font=self.comfortaa_fonts["normal"]
        ).pack(side="right", padx=5)

        self.grab_set()

    def _on_apply(self):
        """Apply selected language and save configuration"""
        try:
            new_lang = self.lang_var.get()
            if new_lang != self.config.get("language"):
                self.config["language"] = new_lang
                save_json(CONFIG_FILE, self.config)

                # Simple restart message
                messagebox.showinfo(
                    tr("info"),
                    "Please restart the application to apply language changes."
                )

            self.result = new_lang
            self.destroy()

        except Exception as e:
            logger.error(f"Error applying language change: {e}")
            messagebox.showerror(tr("error"), str(e))

class NovaInstallerApp(ctk.CTk):
    """Main application class with enhanced language support"""
    def __init__(self):
        super().__init__()

        # Initialize with current time and user
        self.current_datetime = "2025-06-13 20:57:25"
        self.current_user = "Nixiews"

        # Log startup with metadata
        logger.info(f"Starting Nova Installer - Version: V8")
        logger.info(f"Date: {self.current_datetime}")
        logger.info(f"User: {self.current_user}")

        # Log available languages
        metadata = LANGUAGES.get("metadata", {})
        supported_languages = metadata.get("supported_languages", [])
        logger.info(f"Available languages: {', '.join(supported_languages)}")
        logger.info(f"Current language: {config.get('language', 'en')}")

        # Configure Comfortaa font for the entire application
        self.comfortaa_fonts = {
            "small": ctk.CTkFont(family="Comfortaa", size=12),
            "normal": ctk.CTkFont(family="Comfortaa", size=14),
            "large": ctk.CTkFont(family="Comfortaa", size=16),
            "title": ctk.CTkFont(family="Comfortaa", size=20, weight="bold"),
            "header": ctk.CTkFont(family="Comfortaa", size=16, weight="bold"),
            "console": ctk.CTkFont(family="Comfortaa", size=12)
        }

        # Set default font for window
        self.configure(font=self.comfortaa_fonts["normal"])

        # Initialize logger
        self.logger = logging.getLogger("NovaInstaller")
        self.logger.info(f"Starting Nova Installer - Date: {self.current_datetime} - User: {self.current_user}")

        # Check system requirements
        requirements = check_system_requirements()
        if not setup_system_requirements(requirements):
            self.logger.warning("System requirements not met")

        # Apply theme
        ThemeManager.apply_theme(config, self)

        # Configure window
        self.title("Nova Installer")
        self.geometry("1280x720")
        self.minsize(960, 540)

        # Initialize data and UI
        self.selected_apps = set()
        self.data = {}
        self._load_apps_data()
        self.build_ui()

    def _load_apps_data(self):
        """Load applications data from JSON file"""
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            apps_json_path = APPS_FILE

            self.logger.info(f"Loading apps.json from: {apps_json_path}")

            if not os.path.exists(apps_json_path):
                self.logger.error(f"apps.json not found at: {apps_json_path}")
                messagebox.showerror(tr("error"), tr("apps_json_not_found"))
                self.data = {}
                return

            with open(apps_json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            self.logger.info(f"Successfully loaded {len(self.data)} categories from apps.json")

        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing apps.json: {e}")
            messagebox.showerror(tr("error"), tr("apps_json_invalid"))
            self.data = {}
        except Exception as e:
            self.logger.error(f"Unexpected error loading apps data: {e}")
            messagebox.showerror(tr("error"), f"{tr('unexpected_error')}: {str(e)}")
            self.data = {}

    def build_ui(self):
        """Build the main user interface"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Get current theme colors
        current_theme = config["theme"].get("color_theme", "dark")
        colors = ThemeManager.get_theme_colors(current_theme)

        # Header frame
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20,0))
        header.grid_columnconfigure(2, weight=1)

        # Logo
        try:
            logo = Image.open(LOGO_PATH)
            logo = logo.resize((32, 32))
            self.logo = ctk.CTkImage(light_image=logo, dark_image=logo, size=(32, 32))
            ctk.CTkLabel(header, image=self.logo, text="").grid(row=0, column=0, padx=10)
        except Exception as e:
            self.logger.error(f"Error loading logo: {e}")

        # Title
        ctk.CTkLabel(
            header,
            text="Nova Installer",
            font=self.comfortaa_fonts["title"]
        ).grid(row=0, column=1, padx=10)

        # Menu buttons
        menu_frame = ctk.CTkFrame(header, fg_color="transparent")
        menu_frame.grid(row=0, column=2, sticky="e", padx=10)

        # File menu with updated colors
        self.file_menu = ctk.CTkOptionMenu(
            menu_frame,
            values=[tr("import"), tr("export"), tr("exit")],
            command=self._handle_file_menu,
            width=100,
            font=self.comfortaa_fonts["normal"],
            dropdown_font=self.comfortaa_fonts["normal"],
            fg_color=colors["button"],
            button_color=colors["button"],
            button_hover_color=colors["button_hover"],
            dropdown_hover_color=colors["button_hover"]
        )
        self.file_menu.grid(row=0, column=0, padx=5)
        self.file_menu.set(tr("file"))

        # Options menu with updated colors
        self.options_menu = ctk.CTkOptionMenu(
            menu_frame,
            values=[tr("colors"), tr("language")],
            command=self._handle_options_menu,
            width=100,
            font=self.comfortaa_fonts["normal"],
            dropdown_font=self.comfortaa_fonts["normal"],
            fg_color=colors["button"],
            button_color=colors["button"],
            button_hover_color=colors["button_hover"],
            dropdown_hover_color=colors["button_hover"]
        )
        self.options_menu.grid(row=0, column=1, padx=5)
        self.options_menu.set(tr("options"))

        # Help menu with updated colors
        self.help_menu = ctk.CTkOptionMenu(
            menu_frame,
            values=[tr("about"), tr("logs")],
            command=self._handle_help_menu,
            width=100,
            font=self.comfortaa_fonts["normal"],
            dropdown_font=self.comfortaa_fonts["normal"],
            fg_color=colors["button"],
            button_color=colors["button"],
            button_hover_color=colors["button_hover"],
            dropdown_hover_color=colors["button_hover"]
        )
        self.help_menu.grid(row=0, column=2, padx=5)
        self.help_menu.set(tr("help"))

        # Categories frame
        categories = ctk.CTkScrollableFrame(self, width=200)
        categories.grid(row=1, column=0, sticky="nsw", padx=20, pady=20)

        self.category_var = tk.StringVar()
        for category, data in self.data.items():
            category_frame = ctk.CTkFrame(categories)
            category_frame.pack(fill="x", pady=5)

            btn = ctk.CTkRadioButton(
                category_frame,
                text=category,
                variable=self.category_var,
                value=category,
                command=lambda c=category: self._show_category(c),
                font=self.comfortaa_fonts["normal"]
            )
            btn.pack(anchor="w", pady=2)

            if "description" in data:
                desc = ctk.CTkLabel(
                    category_frame,
                    text=data["description"],
                    wraplength=180,
                    font=self.comfortaa_fonts["small"],
                    text_color="gray"
                )
                desc.pack(anchor="w", padx=20, pady=(0,5))

        # Apps panel
        self.apps_frame = ctk.CTkScrollableFrame(self)
        self.apps_frame.grid(row=1, column=1, sticky="nsew", padx=(0,20), pady=20)
        self.apps_frame.grid_columnconfigure(0, weight=1)

        # Bottom bar
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

        install_button = ctk.CTkButton(
            bottom,
            text=tr("install"),
            command=self._install_selected,
            font=self.comfortaa_fonts["normal"]
        )
        install_button.pack(side="left")

        self.selected_var = tk.StringVar(value=tr("no_app_selected"))
        self.dropdown_btn = ctk.CTkOptionMenu(
            bottom,
            variable=self.selected_var,
            values=[tr("no_app_selected")],
            fg_color=colors["button"],
            button_color=colors["button"],
            button_hover_color=colors["button_hover"],
            font=self.comfortaa_fonts["normal"],
            dropdown_font=self.comfortaa_fonts["normal"]
        )
        self.dropdown_btn.pack(side="left", padx=20)

    def _show_category(self, category):
        """Display apps for the selected category"""
        # Clear existing widgets
        for widget in self.apps_frame.winfo_children():
            widget.destroy()

        if not category or category not in self.data:
            return

        # Get current theme colors
        current_theme = config["theme"].get("color_theme", "dark")
        colors = ThemeManager.get_theme_colors(current_theme)

        # Create app buttons for the selected category
        for app_name, app_data in self.data[category]["apps"].items():
            app_frame = ctk.CTkFrame(
                self.apps_frame,
                fg_color=colors["bg"],
                border_color=colors["border"],
                border_width=1
            )
            app_frame.pack(fill="x", padx=10, pady=5)
            app_frame.grid_columnconfigure(1, weight=1)

            # Left side - checkbox
            checkbox = ctk.CTkCheckBox(
                app_frame,
                text=app_name,
                command=lambda a=app_data["id"]: self._toggle_app(a),
                font=self.comfortaa_fonts["normal"],
                fg_color=colors["button"],
                hover_color=colors["button_hover"],
                text_color=colors["text"]
            )
            checkbox.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            # Right side - description
            desc_frame = ctk.CTkFrame(
                app_frame,
                fg_color="transparent"
            )
            desc_frame.grid(row=0, column=1, sticky="e", padx=10)

            desc_label = ctk.CTkLabel(
                desc_frame,
                text=app_data["description"],
                font=self.comfortaa_fonts["small"],
                text_color=colors["text"],
                justify="right"
            )
            desc_label.pack(side="right")

            # Add separator
            separator = ctk.CTkFrame(
                app_frame,
                height=1,
                fg_color=colors["border"]
            )
            separator.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5)

    def _update_app_list_theme(self):
        """Update the theme of the app list when theme changes"""
        current_category = self.category_var.get()
        if current_category:
            self._show_category(current_category)

    def _handle_file_menu(self, choice):
        """Handle file menu selections"""
        if choice == tr("exit"):
            self.quit()
        # Reset menu to default text
        self.file_menu.set(tr("file"))

    def _handle_options_menu(self, choice):
        """Enhanced options menu handler with proper language support"""
        if choice == tr("colors"):
            dialog = ColorDialog(self, config)
            self.wait_window(dialog)
            if dialog.result:
                config["theme"] = dialog.result
                save_json(CONFIG_FILE, config)
                ThemeManager.apply_theme(config, self)
                self._update_app_list_theme()
                logger.info(f"Theme updated - Time: {self.current_datetime} - User: {self.current_user}")

        elif choice == tr("language"):
            current_lang = config.get("language", "en")
            dialog = LanguageDialog(self, config)
            self.wait_window(dialog)

            if dialog.result and dialog.result != current_lang:
                config["language"] = dialog.result
                save_json(CONFIG_FILE, config)
                logger.info(f"Language changed from {current_lang} to {dialog.result}")

                # Rebuild UI with new language
                self.destroy()
                app = NovaInstallerApp()
                app.run()
                return

        # Reset menu to default text
        self.options_menu.set(tr("options"))

    def _handle_help_menu(self, choice):
        """Handle help menu selections"""
        if choice == tr("about"):
            dialog = AboutDialog(self, config)
            self.wait_window(dialog)
        elif choice == tr("logs"):
            if os.path.exists(LOG_DIR):
                open_path(LOG_DIR)
            else:
                messagebox.showinfo(tr("info"), tr("no_logs"))

        # Reset menu to default text
        self.help_menu.set(tr("help"))

    def _toggle_app(self, app_id):
        """Toggle app selection"""
        if app_id in self.selected_apps:
            self.selected_apps.remove(app_id)
        else:
            self.selected_apps.add(app_id)
        self._update_selected_display()

    def _update_selected_display(self):
        """Update the display of selected apps"""
        if not self.selected_apps:
            self.selected_var.set(tr("no_app_selected"))
        else:
            self.selected_var.set(f"{tr('selected')}: {len(self.selected_apps)}")

    def _install_selected(self):
        """Install selected applications"""
        if not self.selected_apps:
            messagebox.showinfo(tr("info"), tr("no_apps_selected"))
            return

        dialog = InstallDialog(self, list(self.selected_apps), config)
        self.wait_window(dialog)

        # Clear selections after installation
        self.selected_apps.clear()
        self._update_selected_display()

        # Refresh the current category display
        current_category = self.category_var.get()
        if current_category:
            self._show_category(current_category)

    def run(self):
        """Start the application"""
        self.mainloop()

if __name__ == "__main__":
    app = NovaInstallerApp()
    app.mainloop()
