import os
import subprocess
import json
import sys
import ctypes
import tkinter as tk
import webbrowser
import customtkinter
import subprocess
import tkinter.font as tkFont
from threading import Thread
from tkinter import Menu, messagebox
from PIL import Image, ImageTk

try:
    import customtkinter as ctk
except ImportError:
    print("Veuillez installer customtkinter : pip install customtkinter")
    sys.exit(1)

sys.stdout.reconfigure(encoding='utf-8')

customtkinter.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "apps.json")

comfortaa_path = os.path.join(DATA_DIR, "Comfortaa-Regular.ttf")
if os.path.exists(comfortaa_path):
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
        self.iconbitmap(os.path.join(DATA_DIR, "./icon.ico"))
        self.textbox = ctk.CTkTextbox(self, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("end", "Installation des applications sélectionnées...\n\n")
        self.textbox.configure(state="disabled")

        # Exécuter dans un thread séparé
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
                # Important : utiliser after pour modifier l'UI depuis le thread principal
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

def toggle_app(app_id, display_label):
    if app_id in selected_apps:
        selected_apps.remove(app_id)
    else:
        selected_apps.append(app_id)
    display_label.configure(text="Applications sélectionnées : " + ", ".join(selected_apps) if selected_apps else "Aucune application sélectionnée")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nova Installer")
        self.iconbitmap(os.path.join(DATA_DIR, "./icon.ico"))
        self.geometry("1280x720")
        self.minsize(960, 540)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Menu "À propos..."
        menubar = Menu(self)
        self.config(menu=menubar)
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="À propos...", menu=help_menu)

        def show_about():
            msg = (
                "Nom de l'application : Nova Installer\n"
                "Créé par : Jojo - InfoMaker & Nixiews\n\n"
                "Ce projet a pour but d'arrêter les gens de télécharger n'importe quoi sur Internet.\n\nCe projet est Open-Source et disponible sur notre Github dans le menu À propos !"
            )
            messagebox.showinfo("À propos de Nova Installer", msg)

        help_menu.add_command(label="Infos de l'application", command=show_about)
        help_menu.add_separator()
        help_menu.add_command(label="Notre Tipee", command=lambda: webbrowser.open("https://fr.tipeee.com/nova-instaaller/"))
        help_menu.add_command(label="Voir notre projet", command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"))

        # Logo centré en haut
        logo_path = os.path.join(DATA_DIR, "logo.png")
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((120, 120))
            self.logo = ImageTk.PhotoImage(logo_img)
            logo_label = ctk.CTkLabel(self, image=self.logo, text="")
            logo_label.grid(row=0, column=1, pady=(20, 10), sticky="n")
        else:
            logo_label = ctk.CTkLabel(self, text="Nova Installer", font=big_title_font)
            logo_label.grid(row=0, column=1, pady=(20, 10), sticky="n")

        # Frame latérale pour les catégories
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(10,0), pady=10)
        self.sidebar.grid_propagate(False)
        ctk.CTkLabel(self.sidebar, text="Catégories", font=title_font).pack(pady=(10, 20))

        # Frame centrale pour les apps
        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.center_frame.grid_propagate(True)

        # Bas gauche : bouton installer + menu déroulant sélection
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="sw", padx=20, pady=10)
        ctk.CTkButton(
            self.bottom_frame,
            text="Installer",
            font=default_font,  # <-- Ajoute ceci
            command=lambda: install_selected_apps(self)
        ).pack(side="left", padx=(0,10))

        self.selected_var = tk.StringVar(value="Aucune application sélectionnée")
        self.dropdown_btn = ctk.CTkOptionMenu(
            self.bottom_frame,
            variable=self.selected_var,
            values=["Aucune application sélectionnée"],
            width=220,
            font=default_font  # <-- Ajoute ceci
        )
        self.dropdown_btn.pack(side="left")

        # Charger la config
        with open(CONFIG_FILE, encoding="utf-8") as f:
            self.data = json.load(f)

        # Afficher les catégories
        for category in self.data:
            btn = ctk.CTkButton(
                self.sidebar,
                text=category,
                width=200,
                font=default_font,  # <-- Ajoute ceci
                command=lambda c=category: self.show_category(c)
            )
            btn.pack(pady=5, fill="x")

        # Afficher la première catégorie par défaut
        first_cat = next(iter(self.data))
        self.show_category(first_cat)

        # Charger Comfortaa si le fichier existe
        comfortaa_path = os.path.join(DATA_DIR, "Comfortaa-Regular.ttf")
        if os.path.exists(comfortaa_path):
            try:
                tkFont.Font(root=self, name="Comfortaa", family="Comfortaa", size=12)
            except Exception:
                pass

    def show_category(self, category):
        # Effacer le contenu central
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
        # Affichage résumé dans le bouton
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
    if not is_admin():
        messagebox.showerror("Droits requis", "L'application doit être lancée en tant qu'administrateur.")
        sys.exit(1)
    app = App()
    app.mainloop()
