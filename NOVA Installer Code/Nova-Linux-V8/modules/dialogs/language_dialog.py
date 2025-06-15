"""
Nova Installer Language Dialog
Created by Nixiews
Last updated: 2025-06-14 16:48:21 UTC
"""

import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class LanguageDialog(ctk.CTkToplevel):
    def __init__(self, parent, config):
        try:
            super().__init__(parent)
            self.config = config
            self.result = None

            # Dialog setup
            self.title(parent.tr("language"))
            self.geometry("300x400")
            self.resizable(False, False)

            # Make dialog modal
            self.transient(parent)
            self.grab_set()

            # Center dialog on parent
            self.geometry("+%d+%d" % (
                parent.winfo_rootx() + parent.winfo_width()/2 - 150,
                parent.winfo_rooty() + parent.winfo_height()/2 - 200
            ))

            self.create_widgets(parent)

        except Exception as e:
            logger.error(f"Error initializing language dialog: {e}")
            self.destroy()
            raise

    def create_widgets(self, parent):
        try:
            # Title
            ctk.CTkLabel(
                self,
                text=parent.tr("language"),
                font=parent.fonts["header"]
            ).pack(pady=20)

            # Language selection frame
            frame = ctk.CTkFrame(self)
            frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            # Get available languages
            languages = parent.language_manager.get_available_languages()
            current_lang = self.config.get("language", "en")

            # Create radio buttons for each language
            self.lang_var = ctk.StringVar(value=current_lang)

            for code, name in languages.items():
                ctk.CTkRadioButton(
                    frame,
                    text=name,
                    value=code,
                    variable=self.lang_var,
                    font=parent.fonts["normal"]
                ).pack(pady=10, padx=20, anchor="w")

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

    def ok_clicked(self):
        """Handle OK button click"""
        try:
            self.result = self.lang_var.get()
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
