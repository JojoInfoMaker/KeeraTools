"""
Nova Installer App Manager
Created by Nixiews
Last updated: 2025-06-15 09:13:13 UTC
"""

import tkinter as tk
import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class AppManager:
    def __init__(self, app):
        self.app = app
        self.selected_apps = set()
        self.selected_category = None
        self.category_buttons = {}

    def create_categories(self):
        """Create category buttons"""
        try:
            # Clear existing category buttons
            for widget in self.app.categories_frame.winfo_children():
                widget.destroy()
            self.category_buttons.clear()

            # Get theme colors
            colors = self.app.get_theme_colors()

            # Create new category buttons
            for category in self.app.apps_data:
                button = ctk.CTkButton(
                    self.app.categories_frame,
                    text=self.app.tr(category),
                    command=lambda c=category: self.show_category(c),
                    font=self.app.fonts["normal"],
                    fg_color=colors["button"],
                    hover_color=colors["button_hover"],
                    text_color=colors["text"]
                )
                button.pack(
                    fill="x",
                    padx=5,
                    pady=2
                )
                self.category_buttons[category] = button

            logger.info("Categories created successfully")

        except Exception as e:
            logger.error(f"Error creating categories: {e}")

    def show_category(self, category):
        """Display apps for selected category"""
        try:
            # Clear previous content
            for widget in self.app.title_area.winfo_children():
                widget.destroy()
            for widget in self.app.content_frame.winfo_children():
                widget.destroy()

            if category not in self.app.apps_data:
                return

            self.selected_category = category
            colors = self.app.get_theme_colors()

            # Update category buttons
            for cat, button in self.category_buttons.items():
                if cat == category:
                    button.configure(fg_color=colors["button_hover"])
                else:
                    button.configure(fg_color=colors["button"])

            # Add category title
            ctk.CTkLabel(
                self.app.title_area,
                text=self.app.tr(category),
                font=self.app.fonts["header"],
                fg_color="transparent",
                text_color=colors["text"]
            ).pack(pady=5)

            # Add apps
            if "apps" in self.app.apps_data[category]:
                for app_name, app_data in self.app.apps_data[category]["apps"].items():
                    self.create_app_item(app_name, app_data)

            logger.info(f"Category displayed: {category}")

        except Exception as e:
            logger.error(f"Error showing category: {e}")

    def create_app_item(self, app_name, app_data):
        """Create an app item in the content area"""
        try:
            frame = ctk.CTkFrame(self.app.content_frame)
            frame.pack(
                fill="x",
                padx=5,
                pady=2
            )

            var = tk.BooleanVar(value=app_data["id"] in self.selected_apps)

            checkbox = ctk.CTkCheckBox(
                frame,
                text=app_name,
                variable=var,
                command=lambda a=app_data["id"]: self.toggle_app(a),
                font=self.app.fonts["normal"]
            )
            checkbox.pack(
                side="left",
                padx=10,
                pady=5
            )

            if "description" in app_data:
                desc_label = ctk.CTkLabel(
                    frame,
                    text=app_data["description"],
                    font=self.app.fonts["small"],
                    text_color="gray",
                    wraplength=600
                )
                desc_label.pack(
                    side="left",
                    padx=10,
                    pady=5,
                    fill="x",
                    expand=True
                )

        except Exception as e:
            logger.error(f"Error creating app item: {e}")

    def toggle_app(self, app_id):
        """Toggle app selection"""
        try:
            if app_id in self.selected_apps:
                self.selected_apps.remove(app_id)
            else:
                self.selected_apps.add(app_id)
            self.update_selection_display()

            logger.info(f"App toggled: {app_id}")

        except Exception as e:
            logger.error(f"Error toggling app: {e}")

    def update_selection_display(self):
        """Update the selection counter display"""
        try:
            count = len(self.selected_apps)
            if count == 0:
                self.app.selection_label.configure(
                    text=self.app.tr("no_apps_selected")
                )
                self.app.install_button.configure(state="disabled")
            else:
                self.app.selection_label.configure(
                    text=f"{self.app.tr('selected')}: {count}"
                )
                self.app.install_button.configure(state="normal")

            logger.info(f"Selection display updated: {count} apps selected")

        except Exception as e:
            logger.error(f"Error updating selection display: {e}")
