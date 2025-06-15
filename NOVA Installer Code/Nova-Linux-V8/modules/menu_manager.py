"""
Nova Installer Menu Manager
Created by Nixiews
Last updated: 2025-06-15 09:13:13 UTC
"""

import tkinter as tk
import logging

logger = logging.getLogger(__name__)

class MenuManager:
    def __init__(self, app):
        self.app = app
        self.active_menu = None
        self.cached_menus = {}

    def create_themed_menu(self):
        """Create a themed popup menu"""
        menu = tk.Menu(self.app, tearoff=0)
        colors = self.app.get_theme_colors()

        menu.configure(
            bg=colors["frame_low"],
            fg=colors["text"],
            activebackground=colors["button_hover"],
            activeforeground=colors["text"],
            bd=0,
            font=self.app.fonts["normal"]
        )

        return menu

    def show_menu_at_button(self, menu, button):
        """Helper to show menu at button position"""
        try:
            # Unpost any active menu
            if self.active_menu:
                self.active_menu.unpost()
                self.active_menu = None

            # Get button position
            x = button.winfo_rootx()
            y = button.winfo_rooty() + button.winfo_height()

            logger.info(f"Showing menu at position x={x}, y={y}")

            # Post menu and store reference
            menu.post(x, y)
            self.active_menu = menu

        except Exception as e:
            logger.error(f"Error showing menu: {e}")

    def show_file_menu(self, event=None):
        """Show file menu popup"""
        try:
            logger.info("Showing file menu")

            # Create or get cached menu
            if 'file' not in self.cached_menus:
                menu = self.create_themed_menu()

                # Add menu items
                menu.add_command(
                    label=self.app.tr('import'),
                    command=self.app.import_selection,
                    font=self.app.fonts["normal"]
                )
                menu.add_command(
                    label=self.app.tr('export'),
                    command=self.app.export_selection,
                    font=self.app.fonts["normal"]
                )
                menu.add_separator()
                menu.add_command(
                    label=self.app.tr('exit'),
                    command=self.app.quit,
                    font=self.app.fonts["normal"]
                )

                self.cached_menus['file'] = menu

            self.show_menu_at_button(self.cached_menus['file'], self.app.file_button)
            return "break"  # Prevent event from propagating

        except Exception as e:
            logger.error(f"Error showing file menu: {e}")

    def show_options_menu(self, event=None):
        """Show options menu popup"""
        try:
            logger.info("Showing options menu")

            # Create or get cached menu
            if 'options' not in self.cached_menus:
                menu = self.create_themed_menu()

                # Add menu items
                menu.add_command(
                    label=self.app.tr('colors'),
                    command=self.app.show_color_dialog,
                    font=self.app.fonts["normal"]
                )
                menu.add_command(
                    label=self.app.tr('language'),
                    command=self.app.show_language_dialog,
                    font=self.app.fonts["normal"]
                )

                self.cached_menus['options'] = menu

            self.show_menu_at_button(self.cached_menus['options'], self.app.options_button)
            return "break"  # Prevent event from propagating

        except Exception as e:
            logger.error(f"Error showing options menu: {e}")

    def show_help_menu(self, event=None):
        """Show help menu popup"""
        try:
            logger.info("Showing help menu")

            # Create or get cached menu
            if 'help' not in self.cached_menus:
                menu = self.create_themed_menu()

                # Add menu items
                menu.add_command(
                    label=self.app.tr('about'),
                    command=self.app.show_about_dialog,
                    font=self.app.fonts["normal"]
                )
                menu.add_command(
                    label=self.app.tr('logs'),
                    command=self.app.open_logs,
                    font=self.app.fonts["normal"]
                )

                self.cached_menus['help'] = menu

            self.show_menu_at_button(self.cached_menus['help'], self.app.help_button)
            return "break"  # Prevent event from propagating

        except Exception as e:
            logger.error(f"Error showing help menu: {e}")

    def dismiss_active_menu(self, event=None):
        """Dismiss active menu if exists"""
        if self.active_menu:
            self.active_menu.unpost()
            self.active_menu = None
