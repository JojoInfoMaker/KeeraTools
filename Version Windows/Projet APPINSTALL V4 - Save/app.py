import os
import subprocess
import json
import sys
import ctypes
import tkinter as tk
import webbrowser
import customtkinter
import subprocess
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

        ctk.CTkButton(scrollable_frame, text="Installer les applications", command=lambda: install_selected_apps(self)).pack(pady=15)

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
        help_menu.add_command(label="Notre Discord", command=lambda: webbrowser.open("https://discord.gg/WV2Ms7AqDQ"))
        help_menu.add_command(label="Voir notre projet", command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"))

if __name__ == "__main__":
    if not is_admin():
        messagebox.showerror("Droits requis", "L'application doit être lancée en tant qu'administrateur.")
        sys.exit(1)
    app = App()
    app.mainloop()
