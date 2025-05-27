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
from datetime import datetime
import requests
import shutil

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
GITHUB_REPO = "Nixiews/Nova-Installer"
CURRENT_VERSION = "V1"

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
        self.transient(parent)  # <-- Ajoute cette ligne
        self.title("Installation en cours")
        self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        self.textbox = ctk.CTkTextbox(self, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("end", "Installation des applications sélectionnées...\n\n")
        self.textbox.configure(state="disabled")
        self.process = None  # <-- Ajouté pour garder la référence du process
        self.protocol("WM_DELETE_WINDOW", self.on_close)  # <-- Ajouté pour gérer la fermeture
        Thread(target=self.run_installation, args=(apps,), daemon=True).start()

    def append_text(self, text):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def run_installation(self, apps):
        installed = []
        failed = []
        for app in apps:
            self.append_text(f">>> Installation de {app}... ! NE PAS FERMER CETTE FENÊTRE SINON L'INSTALLATION S'ANNULERAS !\n")
            if app.lower() == "spotify.spotify":
                # Ouvre une fenêtre PowerShell non admin pour Spotify
                powershell_cmd = (
                    f'powershell -NoExit -Command "winget install --id Spotify.Spotify --accept-package-agreements --accept-source-agreements"'
                )
                subprocess.Popen(
                    ["start", "powershell", "-NoExit", "-Command", f"winget install --id Spotify.Spotify --accept-package-agreements --accept-source-agreements"],
                    shell=True
                )
                self.textbox.after(0, self.append_text, "Spotify va s'installer dans une fenêtre PowerShell séparée.\n\n")
                installed.append(app)  # On considère comme lancé
                continue
            # Installation normale pour les autres applis
            self.process = subprocess.Popen(
                ["winget", "install", "--id", app, "--accept-package-agreements", "--accept-source-agreements"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = ""
            for line in self.process.stdout:
                output += line
                self.textbox.after(0, self.append_text, line)
            self.process.wait()
            if self.process.returncode == 0:
                installed.append(app)
            else:
                failed.append(app)
            self.textbox.after(0, self.append_text, f"\n--- Fin de l'installation de {app} ---\n\n")
        summary = (
            f"\n✅ Toutes les installations sont terminées.\n"
            f"Applications installées : {len(installed)}/{len(apps)}\n"
        )
        if failed:
            summary += f"❌ Problèmes avec : {', '.join(failed)}"
        else:
            summary += "Aucune erreur détectée."
        self.textbox.after(0, self.append_text, summary)
        def show_summary_and_close():
            messagebox.showinfo(
                "Terminé",
                f"Installations terminées : {len(installed)}/{len(apps)}\n"
                + (f"Problèmes avec : {', '.join(failed)}" if failed else "Aucune erreur détectée.")
            )
            self.destroy()
        self.textbox.after(0, show_summary_and_close)
        log_content = (
            f"Installation terminée pour : {', '.join(apps)}\n"
            f"Installées : {', '.join(installed)}\n"
            f"Échecs : {', '.join(failed) if failed else 'Aucun'}"
        )
        write_install_log(log_content)

    def on_close(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
        self.destroy()

def install_selected_apps(parent):
    if not selected_apps:
        messagebox.showwarning("Aucune application", "Aucune application sélectionnée. Veuillez sélectionner des applications.")
        return

    # Vérifie et met à jour Winget si besoin
    def check_and_update_winget():
        try:
            # Récupère la version locale de winget
            result = subprocess.run(["winget", "--version"], capture_output=True, text=True, encoding="utf-8")
            local_version = result.stdout.strip()

            # Récupère la dernière version de winget via winget lui-même
            upgrade_result = subprocess.run(
                ["winget", "upgrade", "--id", "Microsoft.Winget.Source_8wekyb3d8bbwe", "--accept-source-agreements", "--accept-package-agreements", "--source", "msstore"],
                capture_output=True, text=True, encoding="utf-8"
            )
            if "Aucune mise à jour disponible" not in upgrade_result.stdout and "No applicable update found" not in upgrade_result.stdout:
                # Lance la mise à jour de winget
                subprocess.run(
                    ["winget", "upgrade", "--id", "Microsoft.Winget.Source_8wekyb3d8bbwe", "--accept-source-agreements", "--accept-package-agreements", "--source", "msstore"],
                    check=True
                )
                messagebox.showinfo("Mise à jour Winget", "Winget a été mis à jour. Veuillez relancer l'installation des applications.")
                return False  # Stoppe l'installation, l'utilisateur doit relancer
            return True
        except Exception as e:
            messagebox.showwarning("Erreur Winget", f"Impossible de vérifier ou mettre à jour Winget : {e}")
            return True  # Continue quand même

    if check_and_update_winget():
        ProgressWindow(parent, selected_apps)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nova Installer ™")
        self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        self.geometry("1280x720")
        self.minsize(960, 540)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.checkbox_vars = {}   # <-- Déplace ici
        self.checkboxes = {}      # <-- Déplace ici

        # Menu
        menubar = Menu(self)
        self.config(menu=menubar)
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="À propos...", menu=help_menu)
        help_menu.add_command(label="Infos de l'application", command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label="Notre Tipee", command=lambda: webbrowser.open("https://fr.tipeee.com/nova-instaaller//"))
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
            ctk.CTkLabel(self.sidebar, text="Nova Installer ™", font=big_title_font).pack(pady=(10, 10))

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
        self.after(1000, self.check_for_update)

    def show_about(self):
        about_win = ctk.CTkToplevel(self)
        about_win.title("À propos de Nova Installer ™")
        about_win.geometry("400x540")
        about_win.resizable(False, False)
        about_win.attributes("-topmost", True)

        # Afficher le logo centré
        if os.path.exists(LOGO_PATH_INFO):
            try:
                logo_img = Image.open(LOGO_PATH_INFO).resize((128, 128))
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = ctk.CTkLabel(about_win, image=logo_photo, text="")
                logo_label.image = logo_photo 
                logo_label.pack(pady=(30, 10))
            except Exception:
                pass

        # Texte à propos
        msg = (
            "Creator : Jojo - InfoMaker & Nixiews\n\n"
            "Version : 1.0\n\n"
            "Nova Installer ™ est un outil de gestion d'applications pour Windows / Linux.\n"
            "Il permet d'installer facilement des applications sans avoir de virus.\n\n"
            "Ce projet est Open-Source et disponible sur notre Github dans le menu À propos !\n\n"
            "Copyright © 2025 Jojo - InfoMaker & Nixiews\n\n"
        )
        ctk.CTkLabel(about_win, text=msg, font=default_font, justify="center", wraplength=350).pack(pady=(0, 20), padx=10)

        ctk.CTkButton(about_win, text="Fermer", command=about_win.destroy).pack(pady=10)

    def show_category(self, category):
        for widget in self.center_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.center_frame, text=category, font=(title_font[0], title_font[1], "bold")).pack(pady=(0,10))

        apps_list = list(self.data[category].items())
        self.checkboxes[category] = {}

        if len(apps_list) > 21:
            # --- Canvas + Scrollbar CustomTkinter, fond gris par défaut ---
            frame_canvas = ctk.CTkFrame(self.center_frame)
            frame_canvas.pack(fill="both", expand=True)

            canvas = tk.Canvas(frame_canvas, borderwidth=0, highlightthickness=0, bg="#2b2b2b")
            scrollbar = ctk.CTkScrollbar(frame_canvas, orientation="vertical", command=canvas.yview)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            scrollable_frame = ctk.CTkFrame(canvas)
            scrollable_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

            def on_frame_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.itemconfig(scrollable_frame_id, width=canvas.winfo_width())

            scrollable_frame.bind("<Configure>", on_frame_configure)
            canvas.bind("<Configure>", on_frame_configure)

            for app, app_id in apps_list:
                if app_id not in self.checkbox_vars:
                    self.checkbox_vars[app_id] = tk.BooleanVar(value=app_id in selected_apps)
                cb = ctk.CTkCheckBox(
                    scrollable_frame,
                    text=app,
                    font=default_font,
                    variable=self.checkbox_vars[app_id],
                    command=lambda a=app_id, c=category: self.toggle_app(a, c)
                )
                cb.pack(anchor="w", padx=20, pady=2)
                self.checkboxes[category][app_id] = cb

            # Molette souris pour le scroll (à garder uniquement ici)
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        else:
            # Affichage direct sans scroll
            frame = ctk.CTkFrame(self.center_frame, fg_color="#2b2b2b")
            frame.pack(fill="both", expand=True)
            for app, app_id in apps_list:
                if app_id not in self.checkbox_vars:
                    self.checkbox_vars[app_id] = tk.BooleanVar(value=app_id in selected_apps)
                cb = ctk.CTkCheckBox(
                    frame,
                    text=app,
                    font=default_font,
                    variable=self.checkbox_vars[app_id],
                    command=lambda a=app_id, c=category: self.toggle_app(a, c)
                )
                cb.pack(anchor="w", padx=20, pady=2)
                self.checkboxes[category][app_id] = cb

    def toggle_app(self, app_id, category=None):
        # Met à jour selected_apps selon la variable associée
        checked = self.checkbox_vars[app_id].get()
        if checked:
            if app_id not in selected_apps:
                selected_apps.append(app_id)
        else:
            if app_id in selected_apps:
                selected_apps.remove(app_id)
        # Met à jour le menu déroulant
        if selected_apps:
            if len(selected_apps) == 1:
                self.selected_var.set(selected_apps[0])
            else:
                self.selected_var.set(f"{len(selected_apps)} applications sélectionnées")
            self.dropdown_btn.configure(values=selected_apps)
        else:
            self.selected_var.set("Aucune application sélectionnée")
            self.dropdown_btn.configure(values=["Aucune application sélectionnée"])

    def check_for_update(self):
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data["tag_name"].lstrip("v")
                print(f"Version locale: {CURRENT_VERSION} | Version GitHub: {latest_version}")  # <-- Ajout
                if latest_version != CURRENT_VERSION:
                    if messagebox.askyesno("Mise à jour disponible", f"Une nouvelle version ({latest_version}) est disponible. Voulez-vous l'installer ?"):
                        # Cherche l'asset .exe
                        exe_asset = next((a for a in data["assets"] if a["name"].endswith(".exe")), None)
                        if exe_asset:
                            self.download_and_replace(exe_asset["browser_download_url"], exe_asset["name"])
                        else:
                            messagebox.showerror("Erreur", "Impossible de trouver le fichier exécutable dans la release.")
            else:
                print("Impossible de vérifier les mises à jour.")
        except Exception as e:
            print(f"Erreur lors de la vérification de mise à jour : {e}")

    def download_and_replace(self, url, filename):
        try:
            temp_path = os.path.join(os.path.dirname(sys.executable), f"update_{filename}")
            with requests.get(url, stream=True) as r:
                with open(temp_path, "wb") as f:
                    shutil.copyfileobj(r.raw, f)
            # Prépare un script batch pour remplacer l'exe après fermeture
            batch_path = os.path.join(os.path.dirname(sys.executable), "update.bat")
            with open(batch_path, "w") as batch:
                batch.write(f"""@echo off
timeout /t 2 >nul
move /y "{temp_path}" "{sys.executable}"
start "" "{sys.executable}"
del "%~f0"
""")
            messagebox.showinfo("Mise à jour", "L'application va redémarrer pour terminer la mise à jour.")
            os.startfile(batch_path)
            self.destroy()
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec du téléchargement ou de la mise à jour : {e}")

def write_install_log(log_content):
    # Chemin du dossier Documents de l'utilisateur
    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    nova_folder = os.path.join(documents_path, "Nova Installer ™")
    os.makedirs(nova_folder, exist_ok=True)

    # Format du nom de fichier : Logs-NVI-DD-MM-AA.txt
    date_str = datetime.now().strftime("%d-%m-%y")
    log_filename = f"Logs-NVI-{date_str}.txt"
    log_filepath = os.path.join(nova_folder, log_filename)

    # Écriture du log
    with open(log_filepath, "a", encoding="utf-8") as log_file:
        log_file.write(log_content + "\n")

if __name__ == "__main__":
    app = App()
    app.mainloop()