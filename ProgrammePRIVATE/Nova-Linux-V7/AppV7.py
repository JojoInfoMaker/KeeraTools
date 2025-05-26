#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import Menu, messagebox
from threading import Thread
from PIL import Image, ImageTk
import platform
import customtkinter as ctk

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "apps.json")
LOGO_PATH = os.path.join(DATA_DIR, "icon.ico")
FONT_PATH = os.path.join(DATA_DIR, "Comfortaa-Regular.ttf")

selected_apps = []

# Use default fonts to avoid issues on Linux
default_font = ("Arial", 12)
title_font = ("Arial", 20, "bold")
big_title_font = ("Arial", 32, "bold")

# Helpers
def is_flatpak_installed():
    try:
        subprocess.run(["flatpak", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

# Progress window
class ProgressWindow(ctk.CTkToplevel):
    def __init__(self, parent, apps):
        super().__init__(parent)
        self.geometry("900x500")
        self.attributes("-topmost", True)
        self.title("Installation en cours")

        self.textbox = ctk.CTkTextbox(self, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("end", "Installation des applications sélectionnées...\n\n")
        self.textbox.configure(state="disabled")

        Thread(target=self.run_installation, args=(apps,), daemon=True).start()

    def append_text(self, text):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def run_installation(self, apps):
        if not is_flatpak_installed():
            self.append_text("Flatpak n'est pas installé.\n")
            return

        for app_id in apps:
            self.append_text(f">>> Installation de {app_id}...\n")
            process = subprocess.Popen(
                ["flatpak", "install", "--system", "--assumeyes", "flathub", app_id],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in process.stdout:
                self.textbox.after(0, self.append_text, line)
            process.wait()
            self.textbox.after(0, self.append_text, f"\n--- Fin de l'installation de {app_id} ---\n\n")

        self.textbox.after(0, self.append_text, "✅ Toutes les installations sont terminées.")
        self.textbox.after(0, lambda: messagebox.showinfo("Terminé", "Toutes les applications ont été installées avec succès."))

# Main App
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nova Installer")
        self.geometry("1280x720")
        self.minsize(960, 540)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Menu Bar
        menubar = Menu(self)
        self.config(menu=menubar)
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="À propos de l'application", command=self.show_about)
        menubar.add_cascade(label="À propos...", menu=help_menu)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(10, 0), pady=10)
        self.sidebar.grid_propagate(False)

        if os.path.exists(LOGO_PATH):
            try:
                logo_img = Image.open(LOGO_PATH).resize((200, 200))
                self.logo = ImageTk.PhotoImage(logo_img)
                ctk.CTkLabel(self.sidebar, image=self.logo, text="").pack(pady=(10, 10))
            except Exception:
                ctk.CTkLabel(self.sidebar, text="Nova Installer", font=big_title_font).pack(pady=(10, 10))
        else:
            ctk.CTkLabel(self.sidebar, text="Nova Installer", font=big_title_font).pack(pady=(10, 10))

        ctk.CTkLabel(self.sidebar, text="Catégories", font=title_font).pack(pady=(10, 20))

        # Center Frame
        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        # Bottom Bar
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky="sew", padx=20, pady=10)

        ctk.CTkButton(self.bottom_frame, text="Installer", font=default_font, command=self.install_apps).pack(side="left")

        self.selected_var = tk.StringVar(value="Aucune application sélectionnée")
        self.dropdown_btn = ctk.CTkOptionMenu(self.bottom_frame, variable=self.selected_var, values=["Aucune application sélectionnée"], width=250, font=default_font)
        self.dropdown_btn.pack(side="left", padx=20)

        # Load app config
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le fichier apps.json : {e}")
            self.data = {}

        # State for current category and filtered apps
        self.current_category = None
        self.filtered_apps = {}

        for category in self.data:
            ctk.CTkButton(self.sidebar, text=category, width=200, font=default_font, command=lambda c=category: self.show_category(c)).pack(pady=5, fill="x")

        if self.data:
            first_category = next(iter(self.data))
            self.show_category(first_category)

    def show_about(self):
        about_win = ctk.CTkToplevel(self)
        about_win.title("À propos de Nova Installer")
        about_win.geometry("400x420")
        about_win.resizable(False, False)

        # Afficher le logo centré
        if os.path.exists(LOGO_PATH):
            try:
                logo_img = Image.open(LOGO_PATH).resize((128, 128))
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = ctk.CTkLabel(about_win, image=logo_photo, text="")
                logo_label.image = logo_photo  # garder une référence
                logo_label.pack(pady=(30, 10))
            except Exception:
                pass

        # Texte à propos
        msg = (
            "Creator : Jojo - InfoMaker & Nixiews\n\n"
            "Ce projet a pour but d'arrêter les gens de télécharger n'importe quoi sur Internet.\n\n"
            "Ce projet est Open-Source et disponible sur notre Github dans le menu À propos !\n"
        )
        ctk.CTkLabel(about_win, text=msg, font=default_font, justify="center", wraplength=350).pack(pady=(0, 20), padx=10)

        ctk.CTkButton(about_win, text="Fermer", command=about_win.destroy).pack(pady=10)

    def show_category(self, category):
        self.current_category = category
        self.filtered_apps = self.data[category]  # No filter at start

        for widget in self.center_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.center_frame, text=category, font=title_font).pack(pady=(0, 10))

        # Search bar
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(self.center_frame, placeholder_text="Rechercher une application...", textvariable=self.search_var)
        search_entry.pack(fill="x", padx=20, pady=(0, 10))
        search_entry.bind("<KeyRelease>", self.update_search_results)

        # Container for app checkboxes
        self.apps_container = ctk.CTkFrame(self.center_frame)
        self.apps_container.pack(fill="both", expand=True)

        self.display_apps(self.filtered_apps)

    def display_apps(self, apps):
        for widget in self.apps_container.winfo_children():
            widget.destroy()

        for app_name, app_id in apps.items():
            ctk.CTkCheckBox(
                self.apps_container,
                text=f"{app_name} ({app_id})",
                font=default_font,
                command=lambda a=app_id: self.toggle_app(a)
            ).pack(anchor="w", padx=20, pady=2)

    def update_search_results(self, event=None):
        query = self.search_var.get().lower()
        if not query:
            self.filtered_apps = self.data[self.current_category]
        else:
            self.filtered_apps = {
                name: appid for name, appid in self.data[self.current_category].items()
                if query in name.lower() or query in appid.lower()
            }
        self.display_apps(self.filtered_apps)

    def toggle_app(self, app_id):
        if app_id in selected_apps:
            selected_apps.remove(app_id)
        else:
            selected_apps.append(app_id)

        if selected_apps:
            if len(selected_apps) == 1:
                self.selected_var.set(selected_apps[0])
            else:
                self.selected_var.set(f"{len(selected_apps)} applications sélectionnées")
            self.dropdown_btn.configure(values=selected_apps)
        else:
            self.selected_var.set("Aucune application sélectionnée")
            self.dropdown_btn.configure(values=["Aucune application sélectionnée"])

    def install_apps(self):
        if not selected_apps:
            messagebox.showwarning("Sélection vide", "Veuillez sélectionner au moins une application.")
            return
        ProgressWindow(self, selected_apps)

# Launch app
if __name__ == "__main__":
    app = App()
    app.mainloop()
