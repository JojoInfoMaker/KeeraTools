"""
Nova Installer UI Manager
Created by Nixiews
Last updated: 2025-06-15 09:13:13 UTC
"""

import tkinter as tk
import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class UIManager:
    def __init__(self, app):
        self.app = app

    def setup_window(self):
        """Set up main window"""
        # Configure window
        self.app.title("Nova Installer")
        self.app.geometry("1000x600")
        self.app.minsize(800, 500)

        # Create frames using pack manager
        self.create_header()
        self.create_main_layout()
        self.create_status_bar()

    def create_header(self):
        """Create header with title and menus"""
        # Header frame
        self.app.header = ctk.CTkFrame(self.app)
        self.app.header.pack(fill="x", padx=20, pady=10)

        # Logo
        logo = self.app.icon_manager.get_app_icon((32, 32))
        if logo:
            ctk.CTkLabel(
                self.app.header,
                image=logo,
                text=""
            ).pack(side="left", padx=10)

        # Title
        ctk.CTkLabel(
            self.app.header,
            text="Nova Installer",
            font=self.app.fonts["title"]
        ).pack(side="left", padx=10)

        # Menu buttons
        self.create_menu_buttons()

    def create_main_layout(self):
        """Create main layout with sidebar and content"""
        # Main container
        self.app.main_container = ctk.CTkFrame(self.app)
        self.app.main_container.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 10)
        )

        # Create sidebar frame
        self.app.sidebar = ctk.CTkFrame(
            self.app.main_container,
            width=200
        )
        self.app.sidebar.pack(
            side="left",
            fill="y",
            padx=(0, 10)
        )
        self.app.sidebar.pack_propagate(False)

        # Create scrollable frame for categories
        self.app.categories_frame = ctk.CTkScrollableFrame(self.app.sidebar)
        self.app.categories_frame.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # Content area
        self.app.content_area = ctk.CTkFrame(self.app.main_container)
        self.app.content_area.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Title area
        self.app.title_area = ctk.CTkFrame(self.app.content_area)
        self.app.title_area.pack(
            fill="x",
            padx=10,
            pady=5
        )

        # Content frame
        self.app.content_frame = ctk.CTkScrollableFrame(self.app.content_area)
        self.app.content_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

    def create_status_bar(self):
        """Create status bar"""
        self.app.status_bar = ctk.CTkFrame(self.app)
        self.app.status_bar.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # Install button
        self.app.install_button = ctk.CTkButton(
            self.app.status_bar,
            text=self.app.tr("install"),
            command=self.app.install_selected,
            font=self.app.fonts["normal"],
            state="disabled"
        )
        self.app.install_button.pack(
            side="right",
            padx=10,
            pady=5
        )

        # Selection counter
        self.app.selection_label = ctk.CTkLabel(
            self.app.status_bar,
            text=self.app.tr("no_apps_selected"),
            font=self.app.fonts["normal"]
        )
        self.app.selection_label.pack(
            side="left",
            padx=10,
            pady=5
        )

    def create_menu_buttons(self):
        """Create menu buttons in header"""
        try:
            menu_frame = ctk.CTkFrame(
                self.app.header,
                fg_color="transparent"
            )
            menu_frame.pack(side="right", padx=10)

            # Get theme colors
            colors = self.app.get_theme_colors()

            # Create buttons with theme-aware styling
            button_style = {
                "width":        100,
                "font":         self.app.fonts["normal"],
                "fg_color":     colors["button"],
                "hover_color":  colors["button_hover"],
                "text_color":   colors["text"]
            }

            # File button
            self.app.file_button = ctk.CTkButton(
                menu_frame,
                text=self.app.tr("file"),
                **button_style
            )
            self.app.file_button.configure(
                command=self.app.menu_manager.show_file_menu
            )
            self.app.file_button.pack(side="left", padx=5)
            self.app.file_button.bind(
                '<Button-1>',
                self.app.menu_manager.show_file_menu
            )

            # Options button
            self.app.options_button = ctk.CTkButton(
                menu_frame,
                text=self.app.tr("options"),
                **button_style
            )
            self.app.options_button.configure(
                command=self.app.menu_manager.show_options_menu
            )
            self.app.options_button.pack(side="left", padx=5)
            self.app.options_button.bind(
                '<Button-1>',
                self.app.menu_manager.show_options_menu
            )

            # Help button
            self.app.help_button = ctk.CTkButton(
                menu_frame,
                text=self.app.tr("help"),
                **button_style
            )
            self.app.help_button.configure(
                command=self.app.menu_manager.show_help_menu
            )
            self.app.help_button.pack(side="left", padx=5)
            self.app.help_button.bind(
                '<Button-1>',
                self.app.menu_manager.show_help_menu
            )

            logger.info("Menu buttons created successfully")

        except Exception as e:
            logger.error(f"Error creating menu buttons: {e}")
