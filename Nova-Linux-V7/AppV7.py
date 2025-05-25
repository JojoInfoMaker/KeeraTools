import os
import sys
import json
import ctypes
import subprocess
import tkinter as tk
from tkinter import Menu, messagebox
from threading import Thread
from PIL import Image, ImageTk

import customtkinter as ctk

# Appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "apps.json")
ICON_PATH = os.path.join(DATA_DIR, "icon.ico")
LOGO_PATH = os.path.join(DATA_DIR, "icon2.ico")
FONT_PATH = os.path.join(DATA_DIR, "Comfortaa-Regular.ttf")

selected_apps = []

# Font setup
def load_font(path):
    FR_PRIVATE = 0x10
    path = os.path.abspath(path)
    return ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0) > 0 if os.path.exists(path) else False

if load_font(FONT_PATH):
    default_font = ("Comfortaa", 12)
    title_font = ("Comfortaa", 20, "bold")
    big_title_font = ("Comfortaa", 32, "bold")
else:
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

class ProgressWindow(ctk.CTkToplevel):
    def __init__(self, parent, apps):
        super().__init__(parent)
        self.geometry("900x500")
        self.attributes("-topmost", True)
        self.title("Installation en cours")
        self.iconbitmap(ICON_PATH)
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
                ["flatpak", "install", "--user", "-y", app_id],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in process.stdout:
                self.textbox.after(0, self.append_text, line)
            process.wait()
            self.textbox.after(0, self.append_text, f"\n--- Fin de l'installation de {app_id} ---\n\n")

        self.textbox.after(0, self.append_text, "✅ Toutes les installations sont terminées.")
        self.textbox.after(0, lambda: messagebox.showinfo("Terminé", "Toutes les applications ont été installées avec succès."))

# Main App Class
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nova Installer")
        self.geometry("1280x720")
        self.minsize(960, 540)
        self.iconbitmap(ICON_PATH)
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
            logo_img = Image.open(LOGO_PATH).resize((200, 200))
            self.logo = ImageTk.PhotoImage(logo_img)
            ctk.CTkLabel(self.sidebar, image=self.logo, text="").pack(pady=(10, 10))
        else:
            ctk.CTkLabel(self.sidebar, text="Nova Installer", font=big_title_font).pack(pady=(10, 10))

        ctk.CTkLabel(self.sidebar, text="Catégories", font=title_font).pack(pady=(10, 20))

        # Center Frame
        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        # Bottom Bar
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky="sew", padx=20, pady=10)

        ctk.CTkButton(self.bottom_frame, text="Installer", font=default_font, command=lambda: self.install_apps()).pack(side="left")

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

        for category in self.data:
            ctk.CTkButton(self.sidebar, text=category, width=200, font=default_font, command=lambda c=category: self.show_category(c)).pack(pady=5, fill="x")

        if self.data:
            self.show_category(next(iter(self.data)))

    def show_about(self):
        messagebox.showinfo("À propos", "Nova Installer - Version Flatpak\nDéveloppé par Nixiews & Jojo")

    def show_category(self, category):
        for widget in self.center_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.center_frame, text=category, font=title_font).pack(pady=(0, 10))

        for app_name, app_id in self.data[category].items():
            ctk.CTkCheckBox(
                self.center_frame,
                text=f"{app_name} ({app_id})",
                font=default_font,
                command=lambda a=app_id: self.toggle_app(a)
            ).pack(anchor="w", padx=20, pady=2)

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

if __name__ == "__main__":
    app = App()
    app.mainloop()
