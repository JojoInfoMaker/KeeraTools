"""
Nova Installer About Dialog
Created by Nixiews
Last updated: 2025-06-14 16:06:47 UTC
"""

import customtkinter as ctk
import logging
import webbrowser

logger = logging.getLogger(__name__)

class AboutDialog(ctk.CTkToplevel):
    def __init__(self, parent, config):
        try:
            super().__init__(parent)

            self.parent = parent
            self.config = config

            # Set window properties
            self.title(self.parent.tr("about"))
            self.geometry("400x500")
            self.resizable(False, False)

            # Make dialog modal
            self.transient(parent)

            # Create widgets
            self.create_widgets()

            # Center dialog
            self.center_window()

            # Wait for window to be visible before setting grab
            self.after(100, self.set_grab)

        except Exception as e:
            logger.error(f"Error initializing about dialog: {e}")
            self.destroy()

    def set_grab(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception as e:
            logger.error(f"Error setting window grab: {e}")

    def center_window(self):
        self.update_idletasks()

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        width = 400
        height = 500

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        # Main container
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # App icon
        icon = self.parent.icon_manager.get_app_icon((64, 64))
        if icon:
            icon_label = ctk.CTkLabel(
                container,
                image=icon,
                text=""
            )
            icon_label.pack(pady=(0, 10))

        # Title
        title_label = ctk.CTkLabel(
            container,
            text="Nova Installer",
            font=("Comfortaa", 24, "bold")
        )
        title_label.pack(pady=(0, 5))

        # Version
        version_label = ctk.CTkLabel(
            container,
            text="Version 8.0",
            font=("Comfortaa", 14)
        )
        version_label.pack(pady=(0, 20))

        # Description
        description = ctk.CTkTextbox(
            container,
            height=150,
            font=("Comfortaa", 12),
            wrap="word"
        )
        description.pack(fill="x", pady=(0, 20))
        description.insert("1.0", "Nova Installer is a modern, user-friendly tool for installing Flatpak applications on Linux systems. It provides an intuitive interface for browsing and installing applications from Flathub and other Flatpak repositories.")
        description.configure(state="disabled")

        # Creator info
        creator_label = ctk.CTkLabel(
            container,
            text="Created by Nixiews",
            font=("Comfortaa", 12)
        )
        creator_label.pack(pady=(0, 5))

        # Last updated
        updated_label = ctk.CTkLabel(
            container,
            text=f"Last Updated: 2025-06-14 16:06:47",
            font=("Comfortaa", 12)
        )
        updated_label.pack(pady=(0, 20))

        # GitHub link
        github_button = ctk.CTkButton(
            container,
            text="View on GitHub",
            command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"),
            font=("Comfortaa", 12)
        )
        github_button.pack(pady=(0, 10))

        # Close button
        close_button = ctk.CTkButton(
            container,
            text=self.parent.tr("Close"),
            command=self.destroy,
            font=("Comfortaa", 12)
        )
        close_button.pack(pady=(20, 0))
