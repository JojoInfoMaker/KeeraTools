import os
import subprocess
import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import customtkinter as ctk

# Appearance settings
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "apps.json")
LOGO_IMAGE = os.path.join(DATA_DIR, "logo.ico")

selected_apps = []

def is_flatpak_installed():
    try:
        subprocess.run(["flatpak", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def install_flatpak():
    messagebox.showinfo("Installation", "Flatpak n'est pas installé. Installation en cours...")
    subprocess.run(["flatpak", "install"])
    messagebox.showinfo("Succès", "Flatpak installé. Vous pouvez maintenant installer des applications.")

def install_selected_apps():
    if not is_flatpak_installed():
        install_flatpak()

    if not selected_apps:
        messagebox.showwarning("Aucune application", "Aucune application sélectionnée.")
        return

    for app_id in selected_apps:
        try:
            subprocess.run(["flatpak", "install", "-y", app_id], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'installation de {app_id} : {e}")
        else:
            messagebox.showinfo("Succès", f"{app_id} installé avec succès.")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nova Installer")
        self.geometry("900x600")
        self.resizable(True, True)

        # Set window icon safely
        try:
            icon_img = Image.open(LOGO_IMAGE)
            icon_photo = ImageTk.PhotoImage(icon_img)
            self.iconphoto(False, icon_photo)
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")

        self.bg_label = tk.Label(self)
        self.bg_label.place(relwidth=1, relheight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.selected_label = ctk.CTkLabel(self.main_frame, text="Aucune application sélectionnée", wraplength=800)
        self.selected_label.pack(pady=10)

        # Buttons saved as instance attributes for easier widget management
        self.btn_install = ctk.CTkButton(self.main_frame, text="Installer les applications", command=install_selected_apps)
        self.btn_install.pack(pady=15)

        self.btn_reload = ctk.CTkButton(self.main_frame, text="🔄 Recharger les catégories", command=self.reload_categories)
        self.btn_reload.pack(pady=5)

        self.btn_show_flatpak = ctk.CTkButton(self.main_frame, text="📋 Voir les Flatpaks installés", command=self.show_flatpak_list)
        self.btn_show_flatpak.pack(pady=5)

        self.reload_categories()

        self.bind("<Configure>", lambda event: self.update_background())

    def reload_categories(self):
        # Remove all widgets inside main_frame except the selected_label and the fixed buttons at the bottom
        for widget in self.main_frame.winfo_children():
            if widget in [self.selected_label, self.btn_install, self.btn_reload, self.btn_show_flatpak]:
                continue
            widget.destroy()

        self.selected_label.configure(text="Aucune application sélectionnée")

        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de chargement : {e}")
            return

        def on_category_click(category_name, apps_dict):
            top = tk.Toplevel(self)
            top.title(f"Sélectionner des applications - {category_name}")
            top.geometry("400x400")

            def add_app(app_name, app_id):
                if app_id not in selected_apps:
                    selected_apps.append(app_id)
                self.selected_label.configure(text="Applications sélectionnées: " + ", ".join(selected_apps))
                top.destroy()

            for app_name, app_id in apps_dict.items():
                ctk.CTkButton(
                    top,
                    text=f"{app_name} ({app_id})",
                    command=lambda a=app_name, i=app_id: add_app(a, i)
                ).pack(pady=5, padx=10, fill="x")

        # Add category buttons fresh:
        for category_name, apps_dict in data.items():
            ctk.CTkButton(
                master=self.main_frame,
                text=category_name,
                command=lambda c=category_name, a=apps_dict: on_category_click(c, a)
            ).pack(pady=5, fill="x", padx=50)

    def update_background(self):
        # If you want to resize or update background image dynamically, implement here
        pass  # or implement your background update logic if needed

    def show_flatpak_list(self):
        try:
            result = subprocess.run(["flatpak", "list"], capture_output=True, text=True, check=True)
            output = result.stdout if result.stdout else "Aucune sortie disponible."
        except subprocess.CalledProcessError as e:
            output = f"Erreur lors de l'exécution de flatpak list :\n{e}"
        except FileNotFoundError:
            output = "Flatpak n'est pas installé sur ce système."

        # Create new window for flatpak output
        flatpak_window = tk.Toplevel(self)
        flatpak_window.title("Liste des Flatpaks installés")
        flatpak_window.geometry("600x400")

        text_box = tk.Text(flatpak_window, wrap="word")
        text_box.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(flatpak_window, command=text_box.yview)
        scrollbar.pack(side="right", fill="y")

        text_box.configure(yscrollcommand=scrollbar.set, state="normal")
        text_box.insert("1.0", output)
        text_box.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
