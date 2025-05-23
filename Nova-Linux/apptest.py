import os
import subprocess
import json
import sys
import ctypes
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import customtkinter

customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

app = customtkinter.CTk()  # create CTk window like you do with the Tk window
app.geometry("1920x1080")

def button_function():
    print("button pressed")

# Use CTkButton instead of tkinter Button
button = customtkinter.CTkButton(master=app, text="CTkButton", command=button_function)
button.place(relx=0.5, rely=0.5, anchor=customtkinter.CENTER)

app.mainloop()

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
DATA_DIR = "./data"
CONFIG_FILE = os.path.join(DATA_DIR, "apps.json")
BACKGROUND_IMAGE = os.path.join(DATA_DIR, "background.jpg")
LOGO_IMAGE = os.path.join(DATA_DIR, "logo.png")

selected_apps = []

def is_flatpak_installed():
    try:
        subprocess.run(["flatpak", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def install_flatpak():
    messagebox.showinfo("Installation", "Flatpak n'est pas installé. Installation en cours...")
    subprocess.run(["flatpak install"])
    messagebox.showinfo("Succès", "Flatpak installé. Vous pouvez maintenant installer des applications.")

# Installe les applications sélectionnées
def install_selected_apps():
    if not is_flatpak_installed():
        install_flatpak()
    if not selected_apps:
        messagebox.showwarning("Aucune application", "Aucune application sélectionnée.")
        return
    for app in selected_apps:
        subprocess.run(["flatpak", "install", "-y", app_id], check=True)

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
        self.title("Installateur - Jojo InfoMaker")
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

        # Fond dynamique
        self.bind("<Configure>", lambda event: self.update_background())

    def update_background(self):
        width = self.winfo_width()
        height = self.winfo_height()
        resized = self.bg_image.resize((width, height), Image.Resampling.LANCZOS)
        self.tk_bg_image = ImageTk.PhotoImage(resized)
        self.bg_label.configure(image=self.tk_bg_image)

try:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    messagebox.showerror("Erreur", f"Erreur de chargement : {e}")
