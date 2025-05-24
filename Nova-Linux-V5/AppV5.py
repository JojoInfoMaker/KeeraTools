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
    # You might want to add your actual installation command here (like apt, yum, pacman, etc.)
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

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Selected apps label
        self.selected_label = ctk.CTkLabel(self.main_frame, text="Aucune application sélectionnée", wraplength=800)
        self.selected_label.pack(pady=10)

        # Flatpak output frame (initially hidden)
        self.flatpak_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.flatpak_text = tk.Text(self.flatpak_frame, wrap="word", height=15)
        self.flatpak_scrollbar = tk.Scrollbar(self.flatpak_frame, command=self.flatpak_text.yview)
        self.flatpak_text.configure(yscrollcommand=self.flatpak_scrollbar.set)

        self.flatpak_text.pack(side="left", fill="both", expand=True)
        self.flatpak_scrollbar.pack(side="right", fill="y")

        self.flatpak_frame.pack_forget()  # hide initially

        # Buttons
        ctk.CTkButton(self.main_frame, text="Installer les applications", command=install_selected_apps).pack(pady=15)
        ctk.CTkButton(self.main_frame, text="🔄 Recharger les catégories", command=self.reload_categories).pack(pady=5)
        ctk.CTkButton(self.main_frame, text="📋 Voir les Flatpaks installés", command=self.toggle_flatpak_list).pack(pady=5)

        self.reload_categories()

    def reload_categories(self):
        # Remove all widgets inside main_frame except selected_label and buttons at bottom
        for widget in self.main_frame.winfo_children():
            if widget == self.selected_label:
                continue
            # Keep buttons with these texts
            if isinstance(widget, ctk.CTkButton) and widget.cget("text") in [
                "Installer les applications", "🔄 Recharger les catégories", "📋 Voir les Flatpaks installés"
            ]:
                continue
            # Also keep flatpak_frame but it will be managed separately
            if widget == self.flatpak_frame:
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

        for category_name, apps_dict in data.items():
            ctk.CTkButton(
                master=self.main_frame,
                text=category_name,
                command=lambda c=category_name, a=apps_dict: on_category_click(c, a)
            ).pack(pady=5, fill="x", padx=50)

    def toggle_flatpak_list(self):
        if self.flatpak_frame.winfo_ismapped():
            self.flatpak_frame.pack_forget()
        else:
            self.show_flatpak_list()
            self.flatpak_frame.pack(fill="both", padx=10, pady=10, expand=False)

    def show_flatpak_list(self):
        try:
            result = subprocess.run(["flatpak", "list"], capture_output=True, text=True, check=True)
            output = result.stdout if result.stdout else "Aucune sortie disponible."
        except subprocess.CalledProcessError as e:
            output = f"Erreur lors de l'exécution de flatpak list :\n{e}"
        except FileNotFoundError:
            output = "Flatpak n'est pas installé sur ce système."

        self.flatpak_text.configure(state="normal")
        self.flatpak_text.delete("1.0", tk.END)
        self.flatpak_text.insert("1.0", output)
        self.flatpak_text.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
