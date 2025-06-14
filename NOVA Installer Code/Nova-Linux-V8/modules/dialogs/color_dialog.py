"""
Nova Installer Color Dialog
Created by Nixiews
Last updated: 2025-06-14 16:52:14 UTC
"""

import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class ColorDialog(ctk.CTkToplevel):
    def __init__(self, parent, config):
        try:
            super().__init__(parent)
            self.config = config
            self.result = None

            # Dialog setup
            self.title(parent.tr("colors"))
            self.geometry("300x500")
            self.resizable(False, False)

            # Make dialog modal
            self.transient(parent)
            self.grab_set()

            # Center dialog on parent
            self.geometry("+%d+%d" % (
                parent.winfo_rootx() + parent.winfo_width()/2 - 150,
                parent.winfo_rooty() + parent.winfo_height()/2 - 250
            ))

            self.create_widgets(parent)

        except Exception as e:
            logger.error(f"Error initializing color dialog: {e}")
            self.destroy()
            raise

    def create_widgets(self, parent):
        try:
            # Title
            ctk.CTkLabel(
                self,
                text=parent.tr("colors"),
                font=parent.fonts["header"]
            ).pack(pady=20)

            # Theme selection frame
            frame = ctk.CTkFrame(self)
            frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            # Get available themes
            themes = parent.theme_manager.get_available_themes()
            current_theme = self.config.get("theme", {}).get("color_theme", "night-blue")

            # Create radio buttons for each theme
            self.theme_var = ctk.StringVar(value=current_theme)

            for theme_id, theme_name in themes.items():
                button = ctk.CTkRadioButton(
                    frame,
                    text=theme_name,
                    value=theme_id,
                    variable=self.theme_var,
                    font=parent.fonts["normal"],
                    command=lambda t=theme_id: self.preview_theme(parent, t)
                )
                button.pack(pady=10, padx=20, anchor="w")

            # Buttons frame
            button_frame = ctk.CTkFrame(self, fg_color="transparent")
            button_frame.pack(fill="x", padx=20, pady=(0, 20))

            # OK button
            ctk.CTkButton(
                button_frame,
                text="OK",
                command=self.ok_clicked,
                width=100,
                font=parent.fonts["normal"]
            ).pack(side="left", padx=5)

            # Cancel button
            ctk.CTkButton(
                button_frame,
                text=parent.tr("cancel"),
                command=self.cancel_clicked,
                width=100,
                font=parent.fonts["normal"]
            ).pack(side="right", padx=5)

        except Exception as e:
            logger.error(f"Error creating widgets: {e}")
            raise

    def preview_theme(self, parent, theme_id):
        """Preview selected theme"""
        try:
            parent.theme_manager.apply_theme(parent, theme_id)
        except Exception as e:
            logger.error(f"Error previewing theme: {e}")

    def ok_clicked(self):
        """Handle OK button click"""
        try:
            self.result = {
                "appearance_mode": "dark",
                "color_theme": self.theme_var.get()
            }
            self.destroy()
        except Exception as e:
            logger.error(f"Error handling OK click: {e}")
            self.destroy()

    def cancel_clicked(self):
        """Handle Cancel button click"""
        try:
            self.result = None
            self.destroy()
        except Exception as e:
            logger.error(f"Error handling Cancel click: {e}")
            self.destroy()
