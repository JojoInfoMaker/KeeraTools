"""
Nova Installer Color Dialog
Created by Nixiews
Last updated: 2025-06-15 09:34:26 UTC
"""

import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)

class ColorDialog(ctk.CTkToplevel):
    def __init__(self, parent, config):
        super().__init__(parent)

        # Dialog setup
        self.parent = parent
        self.config = config
        self.result = None

        # Make dialog resizable
        self.resizable(True, True)
        self.minsize(400, 400)  # Increased minimum height

        # Configure grid weights for proper resizing
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Make themes section expand

        # Create header
        self.create_header()

        # Create scrollable themes section
        self.create_themes_section()

        # Create footer
        self.create_footer()

        # Initial theme selection
        self.initial_theme = self.config.get("theme", {}).get("color_theme", "night-blue")
        self.theme_var.set(self.initial_theme)

        logger.info(f"Color dialog initialized with theme: {self.initial_theme}")

    def create_header(self):
        """Create dialog header"""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")

        # Title
        ctk.CTkLabel(
            header_frame,
            text=self.parent.tr("select_theme"),
            font=self.parent.fonts["header"]
        ).pack(pady=10)

        # Mode selection
        mode_frame = ctk.CTkFrame(header_frame)
        mode_frame.pack(fill="x", padx=20, pady=5)

        # Theme preview label
        self.preview_label = ctk.CTkLabel(
            header_frame,
            text="",  # Will be updated in preview_theme
            font=self.parent.fonts["normal"]
        )
        self.preview_label.pack(pady=5)

    def create_themes_section(self):
        """Create scrollable themes section"""
        # Create main frame that will contain the scrollable frame
        self.themes_container = ctk.CTkFrame(self)
        self.themes_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Configure grid weights for container
        self.themes_container.grid_columnconfigure(0, weight=1)
        self.themes_container.grid_rowconfigure(0, weight=1)

        # Create scrollable frame
        self.themes_frame = ctk.CTkScrollableFrame(
            self.themes_container,
            label_text=self.parent.tr("available_themes")
        )
        self.themes_frame.grid(row=0, column=0, sticky="nsew")

        # Get theme colors for proper styling
        colors = self.parent.get_theme_colors()

        # Initialize theme variable
        self.theme_var = ctk.StringVar(value="night-blue")

        # Create radio buttons for themes
        for i, (theme_id, theme_name) in enumerate(self.parent.theme_manager.get_available_themes().items()):
            frame = ctk.CTkFrame(self.themes_frame)
            frame.pack(fill="x", padx=10, pady=2)

            theme_button = ctk.CTkRadioButton(
                frame,
                text=theme_name,
                value=theme_id,
                variable=self.theme_var,
                command=lambda t=theme_id: self.preview_theme(t),
                font=self.parent.fonts["normal"],
                fg_color=colors["button"],
                hover_color=colors["button_hover"],
                text_color=colors["text"]
            )
            theme_button.pack(side="left", padx=10, pady=5)

            # Store reference to button
            setattr(self, f"theme_button_{theme_id}", theme_button)

    def create_footer(self):
        """Create dialog footer"""
        footer_frame = ctk.CTkFrame(self)
        footer_frame.grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew")

        # Get theme colors
        colors = self.parent.get_theme_colors()

        # Create buttons with more padding and width
        ctk.CTkButton(
            footer_frame,
            text=self.parent.tr("apply"),
            command=self.apply_theme,
            font=self.parent.fonts["normal"],
            fg_color=colors["button"],
            hover_color=colors["button_hover"],
            text_color=colors["text"],
            width=120  # Set fixed width
        ).pack(side="right", padx=10, pady=10)

        ctk.CTkButton(
            footer_frame,
            text=self.parent.tr("cancel"),
            command=self.cancel,
            font=self.parent.fonts["normal"],
            fg_color=colors["button"],
            hover_color=colors["button_hover"],
            text_color=colors["text"],
            width=120  # Set fixed width
        ).pack(side="right", padx=10, pady=10)

    def preview_theme(self, theme_name):
        """Preview selected theme"""
        try:
            # Get theme display name
            theme_display_name = self.parent.theme_manager.get_available_themes().get(theme_name, theme_name)
            self.preview_label.configure(text=f"Preview: {theme_display_name}")

            # Apply theme
            self.parent.theme_manager.apply_theme(self.parent, theme_name)

            # Update dialog colors
            self.update_dialog_colors()

            logger.info(f"Theme preview: {theme_name}")

        except Exception as e:
            logger.error(f"Error previewing theme: {e}")

    def update_dialog_colors(self):
        """Update dialog colors after theme change"""
        try:
            colors = self.parent.get_theme_colors()

            # Update button colors
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(
                        fg_color=colors["button"],
                        hover_color=colors["button_hover"],
                        text_color=colors["text"]
                    )
                elif isinstance(widget, ctk.CTkFrame):
                    widget.configure(fg_color=colors["bg"])

            # Update radio buttons
            for theme_id in self.parent.theme_manager.get_available_themes().keys():
                if hasattr(self, f"theme_button_{theme_id}"):
                    btn = getattr(self, f"theme_button_{theme_id}")
                    btn.configure(
                        fg_color=colors["button"],
                        hover_color=colors["button_hover"],
                        text_color=colors["text"]
                    )

        except Exception as e:
            logger.error(f"Error updating dialog colors: {e}")

    def apply_theme(self):
        """Apply selected theme and close dialog"""
        try:
            selected_theme = self.theme_var.get()

            if not "theme" in self.config:
                self.config["theme"] = {}

            self.config["theme"]["color_theme"] = selected_theme
            self.result = self.config["theme"]

            logger.info(f"Theme applied: {selected_theme}")
            self.destroy()

        except Exception as e:
            logger.error(f"Error applying theme: {e}")

    def cancel(self):
        """Cancel theme selection and restore previous theme"""
        try:
            # Restore previous theme
            self.parent.theme_manager.apply_theme(self.parent, self.initial_theme)

            logger.info(f"Theme selection cancelled, restored: {self.initial_theme}")
            self.destroy()

        except Exception as e:
            logger.error(f"Error cancelling theme selection: {e}")
