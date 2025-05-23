import os
import subprocess
import json
import sys
import ctypes
import tkinter as tk
import webbrowser
from tkinter import Menu, messagebox
from PIL import Image, ImageTk
import ctypes, sys

try:
    import customtkinter as ctk
except ImportError:
    print("Veuillez installer customtkinter : pip install customtkinter")
    sys.exit(1)

# Configuration UI
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Chemin absolu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "apps.json")
BACKGROUND_IMAGE = os.path.join(DATA_DIR, "background.jpg")
LOGO_IMAGE = os.path.join(DATA_DIR, "logo.png")

selected_apps = []

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Vérifie si Chocolatey est installé
def is_choco_installed():
    try:
        subprocess.run(["choco", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

# Installe Chocolatey
def install_choco():
    messagebox.showinfo("Installation", "Chocolatey n'est pas installé, Veuillez cliquez sur Ok pour lancer l'installation")
    subprocess.run([
        "powershell", "-NoProfile", "-InputFormat", "None",
        "-ExecutionPolicy", "Bypass", "-Command",
        "Set-ExecutionPolicy Bypass -Scope Process -Force; "
        "[System.Net.ServicePointManager]::SecurityProtocol = "
        "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
        "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
    ])
    messagebox.showinfo("Succès", "Chocolatey installé. Veuillez redémarrer l'application pour continuer.")

# Installe les applications sélectionnées
def install_selected_apps():
    if not is_choco_installed():
        install_choco()
    if not selected_apps:
        messagebox.showwarning("Aucune application", "Aucune application sélectionnée. Veuillez sélectionnez des Applications.")
        return
    for app in selected_apps:
        subprocess.run(["choco", "install", app, "-y"])
    messagebox.showinfo("Terminé", "Toutes les applications ont été installées avec succès.")

# Gère la sélection
def toggle_app(app_id, display_label):
    if app_id in selected_apps:
        selected_apps.remove(app_id)
    else:
        selected_apps.append(app_id)
    display_label.configure(text=", ".join(selected_apps))

# UI principale
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nova Installer")
        self.geometry("900x600")
        self.resizable(True, True)

        self.bg_image = Image.open(BACKGROUND_IMAGE)
        self.bg_label = tk.Label(self)
        self.bg_label.place(relwidth=1, relheight=1)
        self.update_background()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Affichage des catégories
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)

        self.selected_label = ctk.CTkLabel(main_frame, text="Aucune application sélectionnée", wraplength=800)
        self.selected_label.pack(pady=10)

        for category, apps in data.items():
            ctk.CTkLabel(main_frame, text=category, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=5)
            for app in apps:
                ctk.CTkCheckBox(
                    main_frame,
                    text=app,
                    command=lambda a=apps[app]: toggle_app(a, self.selected_label)
                ).pack(anchor="w", padx=20)

        # Boutons
        ctk.CTkButton(main_frame, text="Installer les applications", command=install_selected_apps).pack(pady=15)

        # Menu principal
        menubar = Menu(self)
        self.config(menu=menubar)

        # Menu "Aide"
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="À propos...", menu=help_menu)

        # Fonction appelée quand on clique sur "Infos de l'application"
        def show_about():
            msg = (
                "Nom de l'application : Nova Installer\n"
                "Créé par : Jojo - InfoMaker & Nixiews\n"
                "Date de création : mai 2025\n"
                "Date de publication : prévue en 2025\n"
                "Ce projet est pour but d'arrêter au gens de télécharger n'importe quoi sur internet.\n\nCe projet est Open-Source est disponible sur notre Github dans le à propos !"
            )
            messagebox.showinfo("À propos de Rivals Installer", msg)

        # Commandes du menu
        help_menu.add_command(label="Infos de l'application", command=show_about)
        help_menu.add_separator()
        help_menu.add_command(label="Notre Discord", command=lambda: webbrowser.open("https://discord.gg/tonlien"))
        help_menu.add_command(label="Voir notre projet", command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"))
        # Fond dynamique
        self.bind("<Configure>", lambda event: self.update_background())

    def update_background(self):
        width = self.winfo_width()
        height = self.winfo_height()
        resized = self.bg_image.resize((width, height), Image.Resampling.LANCZOS)
        self.tk_bg_image = ImageTk.PhotoImage(resized)
        self.bg_label.configure(image=self.tk_bg_image)

if __name__ == "__main__":
    if not is_admin():
        messagebox.showerror("Droits requis", "L'application doit être lancée en tant qu'administrateur.")
        sys.exit(1)
    app = App()
    app.mainloop()
