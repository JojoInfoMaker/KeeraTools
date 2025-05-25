import os
import sys
import json
import ctypes
import tkinter as tk
import tkinter.font as tkFont
import webbrowser
import subprocess
from threading import Thread
from tkinter import Menu, messagebox
from PIL import Image, ImageTk

try:
    import customtkinter as ctk
except ImportError:
    print("Veuillez installer customtkinter : pip install customtkinter")
    sys.exit(1)

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

# Apparence
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

if hasattr(sys, "_MEIPASS"):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemins de base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FONT_PATH = os.path.join(BASE_DIR, "data", "Comfortaa-Regular.ttf")
CONFIG_FILE = os.path.join(DATA_DIR, "apps.json")
LOGO_PATH_INFO = os.path.join(DATA_DIR, "icon2.ico")

def load_font(path):
    FR_PRIVATE = 0x10
    FR_NOT_ENUM = 0x20
    path = os.path.abspath(path)
    if os.path.exists(path):
        return ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0) > 0
    return False

# Polices personnalisées
comfortaa_path = os.path.join(DATA_DIR, "Comfortaa-Regular.ttf")
if load_font(comfortaa_path):
    default_font = ("Comfortaa", 12)
    title_font = ("Comfortaa", 20, "bold")
    big_title_font = ("Comfortaa", 32, "bold")
else:
    default_font = ("Arial", 12)
    title_font = ("Arial", 20, "bold")
    big_title_font = ("Arial", 32, "bold")

selected_apps = []

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class ProgressWindow(ctk.CTkToplevel):
    def __init__(self, parent, apps):
        super().__init__(parent)
        self.geometry("1100x650")
        self.attributes("-topmost", True)
        self.title("Installation en cours")
        self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
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
        for app in apps:
            self.append_text(f">>> Installation de {app}...\n")
            process = subprocess.Popen(
                ["winget", "install", "--id", app, "--accept-package-agreements", "--accept-source-agreements"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8"
            )
            for line in process.stdout:
                self.textbox.after(0, self.append_text, line)
            process.wait()
            self.textbox.after(0, self.append_text, f"\n--- Fin de l'installation de {app} ---\n\n")
        self.textbox.after(0, self.append_text, "✅ Toutes les installations sont terminées.")
        self.textbox.after(0, lambda: messagebox.showinfo("Terminé", "Toutes les applications ont été installées avec succès."))

def install_selected_apps(parent):
    if not selected_apps:
        messagebox.showwarning("Aucune application", "Aucune application sélectionnée. Veuillez sélectionner des applications.")
        return
    ProgressWindow(parent, selected_apps)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nova Installer")
        self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        self.geometry("1280x720")
        self.minsize(960, 540)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Menu
        menubar = Menu(self)
        self.config(menu=menubar)
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="À propos...", menu=help_menu)
        help_menu.add_command(label="Infos de l'application", command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label="Notre Tipee", command=lambda: webbrowser.open("https://fr.tipeee.com/nova-instaaller/"))
        help_menu.add_command(label="Voir notre projet", command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"))

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(10,0), pady=10)
        self.sidebar.grid_propagate(False)

        logo_path = os.path.join(DATA_DIR, "icon2.ico")
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path).resize((200, 200))
            self.logo = ImageTk.PhotoImage(logo_img)
            ctk.CTkLabel(self.sidebar, image=self.logo, text="").pack(pady=(10, 10))
        else:
            ctk.CTkLabel(self.sidebar, text="Nova Installer", font=big_title_font).pack(pady=(10, 10))

        ctk.CTkLabel(self.sidebar, text="Catégories", font=title_font).pack(pady=(10, 20))

        # Centre
        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.center_frame.grid_propagate(True)

        # Bas gauche
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="sw", padx=20, pady=10)
        ctk.CTkButton(self.bottom_frame, text="Installer", font=default_font, command=lambda: install_selected_apps(self)).pack(side="left", padx=(0,10))

        self.selected_var = tk.StringVar(value="Aucune application sélectionnée")
        self.dropdown_btn = ctk.CTkOptionMenu(self.bottom_frame, variable=self.selected_var, values=["Aucune application sélectionnée"], width=220, font=default_font)
        self.dropdown_btn.pack(side="left")

        # Charger apps.json
        with open(CONFIG_FILE, encoding="utf-8") as f:
            self.data = json.load(f)

        # Boutons des catégories
        for category in self.data:
            ctk.CTkButton(self.sidebar, text=category, width=200, font=default_font, command=lambda c=category: self.show_category(c)).pack(pady=5, fill="x")

        self.show_category(next(iter(self.data)))

    def show_about(self):
        about_win = ctk.CTkToplevel(self)
        about_win.title("À propos de Nova Installer")
        about_win.geometry("400x420")
        about_win.resizable(False, False)

        # Afficher le logo centré
        if os.path.exists(LOGO_PATH_INFO):
            try:
                logo_img = Image.open(LOGO_PATH_INFO).resize((128, 128))
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
        for widget in self.center_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.center_frame, text=category, font=title_font).pack(pady=(0,10))
        for app in self.data[category]:
            ctk.CTkCheckBox(
                self.center_frame,
                text=app,
                font=default_font,
                command=lambda a=self.data[category][app]: self.toggle_app(a)
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

if __name__ == "__main__":
    app = App()
    app.mainloop()