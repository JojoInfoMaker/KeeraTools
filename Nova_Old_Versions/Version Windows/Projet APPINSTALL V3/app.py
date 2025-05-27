import os
import subprocess
import json
import sys
import ctypes
import tkinter as tk
import webbrowser
from tkinter import Menu, messagebox

try:
    import customtkinter as ctk
except ImportError:
    print("Veuillez installer customtkinter : pip install customtkinter")
    sys.exit(1)

# Configuration UI
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "apps.json")

selected_apps = []

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_selected_apps():
    if not selected_apps:
        messagebox.showwarning("Aucune application", "Aucune application sélectionnée. Veuillez sélectionner des applications.")
        return
    for app in selected_apps:
        subprocess.run(["winget", "install", "--id", app, "--accept-package-agreements", "--accept-source-agreements"])
    messagebox.showinfo("Terminé", "Toutes les applications ont été installées avec succès.")

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
        self.iconbitmap(os.path.join(DATA_DIR, "./logo.ico"))
        self.geometry("1280x720")
        self.minsize(960, 540)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scrollable_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        scrollable_frame.pack(padx=20, pady=20, fill="both", expand=True)

        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)

        self.selected_label = ctk.CTkLabel(scrollable_frame, text="Aucune application sélectionnée", wraplength=800)
        self.selected_label.pack(pady=10)

        for category, apps in data.items():
            cat_frame = ctk.CTkFrame(scrollable_frame)
            cat_frame.pack(fill="x", padx=10, pady=5)

            is_expanded = tk.BooleanVar(value=False)
            app_frame = ctk.CTkFrame(cat_frame)

            def toggle_visibility(var=is_expanded, frame=app_frame, btn_text=f"► {category}", cat=category, btn_ref=None):
                if var.get():
                    frame.pack(fill="x", padx=20, pady=5)
                    btn_ref.configure(text=f"▼ {cat}")
                else:
                    frame.pack_forget()
                    btn_ref.configure(text=f"► {cat}")

            toggle_button = ctk.CTkButton(
                cat_frame,
                text=f"► {category}",
                width=0,
                command=None
            )
            toggle_button.pack(fill="x")

            def make_toggle(button=toggle_button, var=is_expanded, frame=app_frame, cat=category):
                def _cmd():
                    var.set(not var.get())
                    toggle_visibility(var, frame, cat=cat, btn_ref=button)
                return _cmd

            toggle_button.configure(command=make_toggle())

            for app in apps:
                ctk.CTkCheckBox(
                    app_frame,
                    text=app,
                    command=lambda a=apps[app]: toggle_app(a, self.selected_label)
                ).pack(anchor="w", padx=10, pady=1)

        ctk.CTkButton(scrollable_frame, text="Installer les applications", command=install_selected_apps).pack(pady=15)

        menubar = Menu(self)
        self.config(menu=menubar)
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="À propos...", menu=help_menu)

        def show_about():
            msg = (
                "Nom de l'application : Nova Installer\n"
                "Créé par : Jojo - InfoMaker & Nixiews\n\n"
                "Ce projet est pour but d'arrêter au gens de télécharger n'importe quoi sur internet. Car on ne sais jamais ce que l'on télécharge sur internet\nMais grâce à Nova Installer, vous pouvez installer vos appli en toutes tranquillités\n\nCe projet est Open-Source est disponible sur notre Github dans le à propos !"
            )
            messagebox.showinfo("À propos de Rivals Installer", msg)

        help_menu.add_command(label="Infos de l'application", command=show_about)
        help_menu.add_separator()
        help_menu.add_command(label="Notre Discord", command=lambda: webbrowser.open("https://discord.gg/WV2Ms7AqDQ"))
        help_menu.add_command(label="Voir notre projet", command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"))

if __name__ == "__main__":
    if not is_admin():
        messagebox.showerror("Droits requis", "L'application doit être lancée en tant qu'administrateur.")
        sys.exit(1)
    app = App()
    app.mainloop()
