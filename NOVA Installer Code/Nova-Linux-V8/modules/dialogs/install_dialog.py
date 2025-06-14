"""
Nova Installer Installation Dialog
Created by Nixiews
Last updated: 2025-06-14 16:01:21 UTC
"""

import os
import sys
import subprocess
import threading
import logging
from tkinter import messagebox, scrolledtext
import customtkinter as ctk

logger = logging.getLogger(__name__)

class InstallDialog(ctk.CTkToplevel):
    def __init__(self, parent, apps, config):
        try:
            super().__init__(parent)

            self.parent = parent
            self.apps = apps
            self.config = config

            # Initialize variables first
            self.install_type = ctk.StringVar(value="user")  # Default to user install
            self.installation_running = False

            # Set window properties
            self.title(self.parent.tr("installation_type"))
            self.geometry("600x500")
            self.resizable(False, False)

            # Make dialog modal
            self.transient(parent)

            # Create widgets
            self.create_widgets()

            # Center dialog
            self.center_window()

            # Wait for the window to be visible before setting grab
            self.after(100, self.set_grab)

            logger.info("Installation dialog initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing installation dialog: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to initialize installation dialog: {str(e)}"
            )
            self.destroy()

    def set_grab(self):
        """Set window grab after ensuring it's visible"""
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
            logger.debug("Dialog grab set successfully")
        except Exception as e:
            logger.error(f"Error setting window grab: {e}")

    def center_window(self):
        """Center dialog on parent window"""
        try:
            self.update_idletasks()

            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            width = 600
            height = 500

            x = parent_x + (parent_width - width) // 2
            y = parent_y + (parent_height - height) // 2

            self.geometry(f"{width}x{height}+{x}+{y}")
            logger.debug("Dialog centered successfully")

        except Exception as e:
            logger.error(f"Error centering window: {e}")

    def create_widgets(self):
        """Create dialog widgets"""
        try:
            # Main container
            container = ctk.CTkFrame(self)
            container.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            title_label = ctk.CTkLabel(
                container,
                text=self.parent.tr("installation_type"),
                font=("Comfortaa", 20, "bold")
            )
            title_label.pack(pady=(0, 20))

            # Installation options frame
            options_frame = ctk.CTkFrame(container)
            options_frame.pack(fill="x", pady=(0, 20))

            # User installation option (default)
            user_radio = ctk.CTkRadioButton(
                options_frame,
                text=self.parent.tr("user_only"),
                variable=self.install_type,
                value="user",
                font=("Comfortaa", 14)
            )
            user_radio.pack(pady=10, padx=20, anchor="w")

            # System-wide installation option
            system_radio = ctk.CTkRadioButton(
                options_frame,
                text=self.parent.tr("system_wide"),
                variable=self.install_type,
                value="system",
                font=("Comfortaa", 14)
            )
            system_radio.pack(pady=10, padx=20, anchor="w")

            # Progress frame (initially hidden)
            self.progress_frame = ctk.CTkFrame(container)

            # Progress section
            self.progress_container = ctk.CTkFrame(self.progress_frame)
            self.progress_container.pack(fill="x", pady=(10, 5))

            self.progress_label = ctk.CTkLabel(
                self.progress_container,
                text="0%",
                font=("Comfortaa", 12)
            )
            self.progress_label.pack(side="right", padx=5)

            self.progress_bar = ctk.CTkProgressBar(
                self.progress_container,
                height=15,
                corner_radius=5
            )
            self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
            self.progress_bar.set(0)

            # Console output
            self.console_frame = ctk.CTkFrame(self.progress_frame)
            self.console_frame.pack(fill="both", expand=True, pady=(5, 10))

            self.console = scrolledtext.ScrolledText(
                self.console_frame,
                height=10,
                font=("Consolas", 10),
                bg="#2B2B2B",
                fg="#FFFFFF",
                wrap="word"
            )
            self.console.pack(fill="both", expand=True, padx=5, pady=5)

            # Buttons
            button_frame = ctk.CTkFrame(container, fg_color="transparent")
            button_frame.pack(fill="x", pady=(20, 0))

            # Cancel button
            self.cancel_button = ctk.CTkButton(
                button_frame,
                text=self.parent.tr("cancel"),
                command=self.on_cancel,
                font=("Comfortaa", 14),
                height=35,
                corner_radius=10,
                fg_color=("#FF4444", "#AA0000")
            )
            self.cancel_button.pack(side="left")

            # Install button
            self.proceed_button = ctk.CTkButton(
                button_frame,
                text=self.parent.tr("proceed"),
                command=self.start_installation,
                font=("Comfortaa", 14),
                height=35,
                corner_radius=10,
                fg_color=("#1F538D", "#3B8ED0")
            )
            self.proceed_button.pack(side="right")

            logger.debug("Dialog widgets created successfully")

        except Exception as e:
            logger.error(f"Error creating widgets: {e}")
            raise

    def update_console(self, text):
        """Update console output"""
        self.console.insert("end", f"{text}\n")
        self.console.see("end")
        self.update_idletasks()

    def on_cancel(self):
        """Handle cancellation"""
        if self.installation_running:
            if messagebox.askyesno(
                self.parent.tr("confirm_cancel"),
                self.parent.tr("cancel_installation_confirm")
            ):
                self.installation_running = False
        else:
            self.destroy()

    def start_installation(self):
        """Start the installation process"""
        self.installation_running = True
        self.progress_frame.pack(fill="both", expand=True, pady=(20, 0))

        # Update button states
        self.proceed_button.configure(state="disabled")
        self.cancel_button.configure(
            text=self.parent.tr("cancel_installation")
        )

        # Start installation thread
        thread = threading.Thread(target=self.install_apps)
        thread.daemon = True
        thread.start()

    def install_apps(self):
        """Install selected applications"""
        total_apps = len(self.apps)
        success_count = 0

        for i, app_id in enumerate(self.apps, 1):
            if not self.installation_running:
                self.after(0, self.installation_cancelled)
                return

            try:
                # Update progress
                progress = i / total_apps
                self.after(0, self.update_progress, progress, f"Installing {app_id}...")

                # Build Flatpak command
                cmd = ["flatpak", "install", "-y"]

                # Add installation type
                install_type = self.install_type.get()
                logger.debug(f"Installation type selected: {install_type}")

                if install_type == "user":
                    cmd.append("--user")
                elif install_type == "system":
                    cmd.append("--system")  # Changed: No sudo needed for system install

                cmd.append(app_id)
                logger.debug(f"Running command: {' '.join(cmd)}")

                # Execute installation
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Read output in real-time
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.after(0, self.update_console, output.strip())

                if process.returncode == 0:
                    success_count += 1
                    self.after(0, self.update_console, f"Successfully installed {app_id}")
                    logger.info(f"Successfully installed {app_id}")
                else:
                    self.after(0, self.update_console, f"Failed to install {app_id}")
                    logger.error(f"Failed to install {app_id}")

            except Exception as e:
                self.after(0, self.update_console, f"Error: {str(e)}")
                logger.error(f"Error installing {app_id}: {e}")

        if self.installation_running:
            if success_count == total_apps:
                self.after(0, self.installation_complete)
            else:
                self.after(0, self.installation_failed, success_count, total_apps)

    def update_progress(self, value, text):
        """Update progress bar and labels"""
        self.progress_bar.set(value)
        percentage = int(value * 100)
        self.progress_label.configure(text=f"{percentage}%")
        self.update_console(text)

    def installation_complete(self):
        """Show installation complete message"""
        self.progress_label.configure(text="100%")
        self.progress_bar.set(1)
        self.update_console("Installation complete!")
        messagebox.showinfo(
            self.parent.tr("info"),
            self.parent.tr("installation_complete")
        )
        self.destroy()

    def installation_failed(self, success_count, total_apps):
        """Show installation failed message"""
        self.update_console("Installation failed!")
        messagebox.showerror(
            self.parent.tr("error"),
            f"{self.parent.tr('installation_failed')}\n"
            f"Installed: {success_count}/{total_apps}"
        )
        self.destroy()

    def installation_cancelled(self):
        """Handle installation cancellation"""
        self.update_console("Installation cancelled by user.")
        messagebox.showinfo(
            self.parent.tr("info"),
            self.parent.tr("installation_cancelled")
        )
        self.destroy()
