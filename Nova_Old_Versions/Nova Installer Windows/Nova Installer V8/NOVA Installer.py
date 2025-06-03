import os
import sys
import json
import ctypes
import tkinter as tk
import tkinter.font as tkFont
import webbrowser
import subprocess
from threading import Thread
from tkinter import Menu, messagebox, filedialog
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


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

if hasattr(sys, "_MEIPASS"):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FONT_PATH = os.path.join(BASE_DIR, "data", "Comfortaa-Regular.ttf")
CONFIG_FILE = os.path.join(DATA_DIR, "apps.json")
CONFIG_TRAD = os.path.join(DATA_DIR, "traduction.json")
LOGO_PATH_INFO = os.path.join(DATA_DIR, "icon2.ico")
GITHUB_REPO = "Nixiews/Nova-Installer"
CURRENT_VERSION = "V1W"

with open(CONFIG_TRAD, encoding="utf-8") as f:
    LANGUAGES = json.load(f)

current_lang = "fr" # ou "en"

def tr(key, **kwargs):
    txt = LANGUAGES.get(current_lang, {}).get(key, key)
    if kwargs:
        return txt.format(**kwargs)
    return txt

def load_font(path):
    FR_PRIVATE = 0x10
    FR_NOT_ENUM = 0x20
    path = os.path.abspath(path)
    if os.path.exists(path):
        return ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0) > 0
    return False


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

def center_window(win, width=None, height=None):
    win.update_idletasks()
    if width is None or height is None:
        width = win.winfo_width()
        height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

class ProgressWindow(ctk.CTkToplevel):
    def __init__(self, parent, apps):
        super().__init__(parent)
        self.geometry("1100x650")
        center_window(self, 1100, 650)
        self.transient(parent)
        self.title(tr("installing"))
        self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        self.textbox = ctk.CTkTextbox(self, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("end", tr("installing") + "\n\n")
        self.textbox.configure(state="disabled")
        self.process = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
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
            self.append_text(tr("installing2", app=app))
            if app.lower() == "spotify.spotify":
                subprocess.Popen(
                    ["start", "powershell", "-NoExit", "-Command", f"winget install --id Spotify.Spotify --accept-package-agreements --accept-source-agreements"],
                    shell=True
                )
                self.textbox.after(0, self.append_text, "Spotify " + tr("will_install_in_powershell") + "\n\n")
                installed.append(app)
                continue
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
            self.textbox.after(0, self.append_text, f"\n--- {tr('finished')} {app} ---\n\n")
        summary = (
            f"\n✅ {tr('all_installations_finished')}\n"
            f"{tr('installed')}: {len(installed)}/{len(apps)}\n"
        )
        if failed:
            summary += f"❌ {tr('problems_with', apps=', '.join(failed))}"
        else:
            summary += tr("no_error")
        self.textbox.after(0, self.append_text, summary)
        def show_summary_and_close():
            messagebox.showinfo(
                tr("finished"),
                f"{tr('finished_installations')}: {len(installed)}/{len(apps)}\n"
                + (tr("problems_with", apps=', '.join(failed)) if failed else tr("no_error"))
            )
            self.destroy()
        self.textbox.after(0, show_summary_and_close)
        log_content = (
            f"{tr('finished_installations_for')}: {', '.join(apps)}\n"
            f"{tr('installed')}: {', '.join(installed)}\n"
            f"{tr('failed')}: {', '.join(failed) if failed else tr('no_error')}"
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
        messagebox.showwarning(tr("no_app_selected"), tr("no_app_selected"))
        return

    ProgressWindow(parent, selected_apps)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        marker_path = os.path.join(os.path.expanduser("~"), "Documents", "Nova Installer", "first_run_marker.txt")
        lang_marker_path = os.path.join(os.path.expanduser("~"), "Documents", "Nova Installer", "lang_marker.txt")

        global current_lang
        if not os.path.exists(lang_marker_path):
            lang_win = ctk.CTkToplevel(self)
            lang_win.title("Choix de la langue / Language selection")
            lang_win.geometry("350x200")
            center_window(lang_win, 350, 200)
            self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
            lang_win.resizable(False, False)
            lang_win.attributes("-topmost", True)
            ctk.CTkLabel(lang_win, text="Veuillez choisir une langue\nPlease select a language", font=title_font, justify="center").pack(pady=20)
            def set_lang_and_close(lang):
                global current_lang
                current_lang = lang
                os.makedirs(os.path.dirname(lang_marker_path), exist_ok=True)
                with open(lang_marker_path, "w", encoding="utf-8") as f:
                    f.write(lang)
                lang_win.destroy()
            ctk.CTkButton(lang_win, text="Français", command=lambda: set_lang_and_close("fr"), width=120).pack(pady=5)
            ctk.CTkButton(lang_win, text="English", command=lambda: set_lang_and_close("en"), width=120).pack(pady=5)
            self.wait_window(lang_win)
        else:
            with open(lang_marker_path, "r", encoding="utf-8") as f:
                current_lang = f.read().strip()

        self.title("Nova Installer")
        self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        self.geometry("1280x720")
        self.minsize(960, 540)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.checkbox_vars = {}
        self.checkboxes = {}

        Menu
        menubar = Menu(self)
        self.config(menu=menubar)
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_command(label=tr("export"), command=self.export_selection)
        menubar.add_command(label=tr("import"), command=self.import_selection)
        menubar.add_command(label="Français", command=lambda: self.set_language("fr"))
        menubar.add_command(label="English", command=lambda: self.set_language("en"))
        menubar.add_cascade(label=tr("about_title"), menu=help_menu)
        help_menu.add_command(label=tr("app_info"), command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label=tr("tipeee"), command=lambda: webbrowser.open("https://fr.tipeee.com/nova-instaaller//"))
        help_menu.add_command(label=tr("project"), command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"))


        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(10,0), pady=10)
        self.sidebar.grid_propagate(False)


        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.center_frame.grid_propagate(True)

        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="sw", padx=20, pady=10)
        ctk.CTkButton(self.bottom_frame, text=tr("install"), font=default_font, command=lambda: install_selected_apps(self)).pack(side="left", padx=(0,10))

        self.selected_var = tk.StringVar(value=tr("no_app_selected"))
        self.dropdown_btn = ctk.CTkOptionMenu(self.bottom_frame, variable=self.selected_var, values=[tr("no_app_selected")], width=220, font=default_font)
        self.dropdown_btn.pack(side="left")

        with open(CONFIG_FILE, encoding="utf-8") as f:
            self.data = json.load(f)


        self.refresh_texts()

        if not os.path.exists(marker_path):
            self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
            store_url = "ms-windows-store://pdp/?productid=9NBLGGH4NNS1"
            message = tr("welcome")
            if messagebox.askyesno(tr("update_recommended"), message):
                os.startfile(store_url)
            os.makedirs(os.path.dirname(marker_path), exist_ok=True)
            with open(marker_path, "w", encoding="utf-8") as f:
                f.write("shown")

        self.title("Nova Installer")
        self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        self.geometry("1280x720")
        self.minsize(960, 540)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.checkbox_vars = {}
        self.checkboxes = {}

        Menu
        menubar = Menu(self)
        self.config(menu=menubar)
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_command(label=tr("export"), command=self.export_selection)
        menubar.add_command(label=tr("import"), command=self.import_selection)
        menubar.add_command(label="Français", command=lambda: self.set_language("fr"))
        menubar.add_command(label="English", command=lambda: self.set_language("en"))
        menubar.add_cascade(label=tr("about_title"), menu=help_menu)
        help_menu.add_command(label=tr("app_info"), command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label=tr("tipeee"), command=lambda: webbrowser.open("https://fr.tipeee.com/nova-instaaller//"))
        help_menu.add_command(label=tr("project"), command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"))

   
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(10,0), pady=10)
        self.sidebar.grid_propagate(False)

       
        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.center_frame.grid_propagate(True)


        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="sw", padx=20, pady=10)
        ctk.CTkButton(self.bottom_frame, text=tr("install"), font=default_font, command=lambda: install_selected_apps(self)).pack(side="left", padx=(0,10))

        self.selected_var = tk.StringVar(value=tr("no_app_selected"))
        self.dropdown_btn = ctk.CTkOptionMenu(self.bottom_frame, variable=self.selected_var, values=[tr("no_app_selected")], width=220, font=default_font)
        self.dropdown_btn.pack(side="left")

  
        with open(CONFIG_FILE, encoding="utf-8") as f:
            self.data = json.load(f)


        self.refresh_texts()

        if not os.path.exists(marker_path):
            self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
            store_url = "ms-windows-store://pdp/?productid=9NBLGGH4NNS1"
            message = tr("welcome")
            if messagebox.askyesno(tr("update_recommended"), message):
                os.startfile(store_url)
            os.makedirs(os.path.dirname(marker_path), exist_ok=True)
            with open(marker_path, "w", encoding="utf-8") as f:
                f.write("shown")

        self.title("Nova Installer")
        self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        self.geometry("1280x720")
        self.minsize(960, 540)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.checkbox_vars = {}
        self.checkboxes = {}

        Menu
        menubar = Menu(self)
        self.config(menu=menubar)
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_command(label=tr("export"), command=self.export_selection)
        menubar.add_command(label=tr("import"), command=self.import_selection)
        menubar.add_command(label="Français", command=lambda: self.set_language("fr"))
        menubar.add_command(label="English", command=lambda: self.set_language("en"))
        menubar.add_cascade(label=tr("about_title"), menu=help_menu)
        help_menu.add_command(label=tr("app_info"), command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label=tr("tipeee"), command=lambda: webbrowser.open("https://fr.tipeee.com/nova-instaaller//"))
        help_menu.add_command(label=tr("project"), command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"))

       
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

        ctk.CTkLabel(self.sidebar, text=tr("Categories"), font=title_font).pack(pady=(10, 20))

       
        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.center_frame.grid_propagate(True)

       
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="sw", padx=20, pady=10)
        ctk.CTkButton(self.bottom_frame, text=tr("install"), font=default_font, command=lambda: install_selected_apps(self)).pack(side="left", padx=(0,10))

        self.selected_var = tk.StringVar(value=tr("no_app_selected"))
        self.dropdown_btn = ctk.CTkOptionMenu(self.bottom_frame, variable=self.selected_var, values=[tr("no_app_selected")], width=220, font=default_font)
        self.dropdown_btn.pack(side="left")

       
        with open(CONFIG_FILE, encoding="utf-8") as f:
            self.data = json.load(f)

      
        for category in self.data:
            ctk.CTkButton(self.sidebar, text=tr(category), width=200, font=default_font, command=lambda c=category: self.show_category(c)).pack(pady=5, fill="x")

        self.show_category(next(iter(self.data)))
        self.after(1000, self.check_for_update)

    def set_language(self, lang):
        global current_lang
        current_lang = lang
        self.refresh_texts()

    def show_about(self):
        about_win = ctk.CTkToplevel(self)
        about_win.title(tr("about_title"))
        about_win.geometry("400x540")
        center_window(about_win, 400, 540)
        about_win.resizable(False, False)
        about_win.attributes("-topmost", True)

        
        if os.path.exists(LOGO_PATH_INFO):
            try:
                logo_img = Image.open(LOGO_PATH_INFO).resize((128, 128))
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = ctk.CTkLabel(about_win, image=logo_photo, text="")
                logo_label.image = logo_photo 
                logo_label.pack(pady=(30, 10))
            except Exception:
                pass

        
        msg = tr("about_text")
        self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        ctk.CTkLabel(about_win, text=msg, font=default_font, justify="center", wraplength=350).pack(pady=(0, 20), padx=10)

        ctk.CTkButton(about_win, text=tr("Close"), command=about_win.destroy).pack(pady=10)

    def show_category(self, category):
        for widget in self.center_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.center_frame, text=tr(category), font=(title_font[0], title_font[1], "bold")).pack(pady=(0,10))

        apps_list = list(self.data[category].items())
        self.checkboxes[category] = {}

        if len(apps_list) > 21:
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

            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        else:
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
        checked = self.checkbox_vars[app_id].get()
        if checked:
            if app_id not in selected_apps:
                selected_apps.append(app_id)
        else:
            if app_id in selected_apps:
                selected_apps.remove(app_id)
        if selected_apps:
            if len(selected_apps) == 1:
                self.selected_var.set(selected_apps[0])
            else:
                self.selected_var.set(f"{len(selected_apps)} {tr('apps_selected')}")
            self.dropdown_btn.configure(values=selected_apps)
        else:
            self.selected_var.set(tr("no_app_selected"))
            self.dropdown_btn.configure(values=[tr("no_app_selected")])

    def check_for_update(self):
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data["tag_name"].lstrip("v")
                print(f"Version locale: {CURRENT_VERSION} | Version GitHub: {latest_version}")
                if latest_version != CURRENT_VERSION:
                    if messagebox.askyesno(tr("update_available"), f"{tr('new_version_available')} ({latest_version}). {tr('want_to_install')}"):
                        exe_asset = next((a for a in data["assets"] if a["name"].endswith(".exe")), None)
                        if exe_asset:
                            self.download_and_replace(exe_asset["browser_download_url"], exe_asset["name"])
                        else:
                            messagebox.showerror(tr("error"), tr("exe_not_found"))
            else:
                print(tr("cannot_check_update"))
        except Exception as e:
            print(f"{tr('error_checking_update')}: {e}")

    def download_and_replace(self, url, filename):
        try:
            temp_path = os.path.join(os.path.dirname(sys.executable), f"update_{filename}")
            with requests.get(url, stream=True) as r:
                with open(temp_path, "wb") as f:
                    shutil.copyfileobj(r.raw, f)
            batch_path = os.path.join(os.path.dirname(sys.executable), "update.bat")
            with open(batch_path, "w") as batch:
                batch.write(f"""@echo off
timeout /t 2 >nul
move /y "{temp_path}" "{sys.executable}"
start "" "{sys.executable}"
del "%~f0"
""")
            messagebox.showinfo(tr("update"), tr("app_will_restart"))
            os.startfile(batch_path)
            self.destroy()
            sys.exit(0)
        except Exception as e:
            messagebox.showerror(tr("error"), f"{tr('download_or_update_failed')}: {e}")

    def export_selection(self):
        if not selected_apps:
            messagebox.showinfo(tr("export"), tr("no_app_selected_export"))
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[(tr("json_file"), "*.json")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(selected_apps, f, ensure_ascii=False, indent=2)
            messagebox.showinfo(tr("export"), tr("export_success"))

    def import_selection(self):
        file_path = filedialog.askopenfilename(filetypes=[(tr("json_file"), "*.json")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                imported = json.load(f)
            for app_id, var in self.checkbox_vars.items():
                var.set(app_id in imported)
            global selected_apps
            selected_apps = [app_id for app_id in self.checkbox_vars if self.checkbox_vars[app_id].get()]
            messagebox.showinfo(tr("import"), tr("import_success"))

    def refresh_texts(self):
  
        menubar = Menu(self)
        self.config(menu=menubar)
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_command(label=tr("export"), command=self.export_selection)
        menubar.add_command(label=tr("import"), command=self.import_selection)
        menubar.add_command(label="Français", command=lambda: self.set_language("fr"))
        menubar.add_command(label="English", command=lambda: self.set_language("en"))
        menubar.add_cascade(label=tr("about_title"), menu=help_menu)
        help_menu.add_command(label=tr("app_info"), command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label=tr("tipeee"), command=lambda: webbrowser.open("https://fr.tipeee.com/nova-instaaller//"))
        help_menu.add_command(label=tr("project"), command=lambda: webbrowser.open("https://github.com/Nixiews/Nova-Installer"))

        for widget in self.sidebar.winfo_children():
            widget.destroy()
        logo_path = os.path.join(DATA_DIR, "icon2.ico")
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path).resize((200, 200))
            self.logo = ImageTk.PhotoImage(logo_img)
            ctk.CTkLabel(self.sidebar, image=self.logo, text="").pack(pady=(10, 10))
        else:
            ctk.CTkLabel(self.sidebar, text="Nova Installer ", font=big_title_font).pack(pady=(10, 10))
        ctk.CTkLabel(self.sidebar, text=tr("Categories"), font=title_font).pack(pady=(10, 20))
        for category in self.data:
            ctk.CTkButton(self.sidebar, text=tr(category), width=200, font=default_font, command=lambda c=category: self.show_category(c)).pack(pady=5, fill="x")

        self.show_category(next(iter(self.data)))

        self.selected_var.set(tr("no_app_selected"))
        self.dropdown_btn.configure(values=[tr("no_app_selected")])
        self.bottom_frame.winfo_children()[0].configure(text=tr("install"))

def write_install_log(log_content):
    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    nova_folder = os.path.join(documents_path, "Nova Installer ")
    os.makedirs(nova_folder, exist_ok=True)
    date_str = datetime.now().strftime("%d-%m-%y")
    log_filename = f"Logs-NVI-{date_str}.txt"
    log_filepath = os.path.join(nova_folder, log_filename)
    with open(log_filepath, "a", encoding="utf-8") as log_file:
        log_file.write(log_content + "\n")

if __name__ == "__main__":
    app = App()
    app.mainloop()