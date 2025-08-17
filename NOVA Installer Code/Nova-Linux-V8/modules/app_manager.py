"""
Nova Installer App Manager
Created by Nixiews
Last updated: 2025-08-17
"""

import os
import gzip
import xml.etree.ElementTree as ET
import tempfile
import logging
from threading import Thread
import requests
import subprocess

from PyQt5.QtWidgets import (QFrame, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QProgressDialog, QMessageBox)
from PyQt5.QtCore import Qt, QObject, pyqtSignal

from .dialogs.install_dialog import InstallDialog

logger = logging.getLogger(__name__)

class AppDataSignals(QObject):
    apps_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

class AppManager(QObject):
    APPSTREAM_URL = "https://dl.flathub.org/beta-repo/appstream/aarch64/appstream.xml.gz"

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.all_apps = []
        self.filtered_apps = []
        self.selected_apps = []
        self.current_category = "All Categories"
        self.signals = AppDataSignals()
        self.signals.apps_loaded.connect(self._on_apps_loaded)
        self.signals.error_occurred.connect(self._on_error)

        # Connect UI
        self.app.ui_manager.search_bar.textChanged.connect(self.filter_apps)
        self.app.ui_manager.install_button.clicked.connect(self.install_selected_apps)

        # Load apps
        self.load_apps()

    def ensure_flathub_remote(self):
        """Ensure the Flathub remote is configured for Flatpak."""
        try:
            # Check if Flathub remote already exists
            result = subprocess.run(
                ["flatpak", "remote-list", "--columns=name"],
                capture_output=True, text=True
            )
            if "flathub" not in result.stdout.lower():
                subprocess.run([
                    "flatpak", "remote-add", "--if-not-exists",
                    "flathub", "https://flathub.org/repo/flathub.flatpakrepo"
                ], check=True)
                logger.info("Flathub remote added successfully.")
            else:
                logger.info("Flathub remote already exists.")
        except Exception as e:
            logger.error(f"Failed to ensure Flathub remote: {e}")
            raise

    def load_apps(self):
        self.progress_dialog = QProgressDialog("Loading applications...", None, 0, 0, self.app)
        self.progress_dialog.setWindowTitle("Loading")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()
        Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        try:
            apps_data = self._download_and_parse_appstream()
            self.signals.apps_loaded.emit(apps_data)
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            self.signals.error_occurred.emit(str(e))

    def _on_apps_loaded(self, apps_data):
        self.progress_dialog.close()
        self.all_apps = apps_data
        self.filtered_apps = apps_data

        categories = {"All Categories"}
        for app in apps_data:
            categories.update(app.get("categories", []))

        self.app.ui_manager.update_categories(sorted(categories), self.select_category)
        self.display_apps()

    def _on_error(self, msg):
        self.progress_dialog.close()
        QMessageBox.critical(self.app, "Error", f"Failed to load applications: {msg}")

    def _download_and_parse_appstream(self):
        """Download Flathub appstream XML and parse apps"""
        temp_dir = os.path.join(tempfile.gettempdir(), "nova-installer")
        os.makedirs(temp_dir, exist_ok=True)
        gz_path = os.path.join(temp_dir, "appstream.xml.gz")
        xml_path = os.path.join(temp_dir, "appstream.xml")

        # Download
        logger.info("Downloading appstream...")
        r = requests.get(self.APPSTREAM_URL, stream=True, timeout=60)
        r.raise_for_status()
        with open(gz_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Decompress
        logger.info("Decompressing appstream...")
        with gzip.open(gz_path, "rb") as f_in, open(xml_path, "wb") as f_out:
            f_out.write(f_in.read())

        # Parse XML
        logger.info("Parsing appstream XML...")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        apps = []

        for component in root.findall(".//component") + root.findall(".//{http://www.freedesktop.org/software/appstream/appdata}component"):
            try:
                if component.get("type") not in ["desktop", "desktop-application", "webapp"]:
                    continue

                # App ID
                app_id = None
                for tag in ["id", "bundle", ".//id", ".//bundle"]:
                    elem = component.find(tag)
                    if elem is not None and elem.text:
                        app_id = elem.text.strip()
                        break
                if not app_id:
                    continue
                app_id = app_id.replace("flatpak:", "")

                # Name
                name = None
                for tag in ["name", ".//name", "summary", ".//summary"]:
                    elem = component.find(tag)
                    if elem is not None and elem.text:
                        name = elem.text.strip()
                        break
                if not name:
                    name = app_id

                # Categories
                categories = [self._normalize_category(c.text) for c in component.findall(".//category") if c.text]
                if not categories:
                    categories = ["Other"]

                # Version
                releases = component.findall(".//release")
                version = releases[0].get("version", "latest") if releases else "latest"

                # Summary & Description
                summary = component.findtext(".//summary", default="")
                description_elem = component.find(".//description")
                description = ET.tostring(description_elem, encoding="unicode", method="xml") if description_elem is not None else ""

                # Icons
                icon_urls = [i.text for i in component.findall(".//icon") if i.get("type") == "remote"]

                # Screenshots
                screenshots = []
                for shot in component.findall(".//screenshot"):
                    for img in shot.findall(".//image"):
                        if img.get("type") == "source":
                            screenshots.append({"url": img.text})
                            break

                apps.append({
                    "app_id": app_id,
                    "name": name,
                    "categories": list(set(categories)),
                    "version": version,
                    "summary": summary,
                    "description": description,
                    "icon_urls": icon_urls,
                    "screenshots": screenshots,
                    "bundle_type": "flatpak"
                })

            except Exception as e:
                logger.error(f"Failed to process component: {e}")
                continue

        apps.sort(key=lambda a: a["name"].lower())

        # Cleanup
        for f in [gz_path, xml_path]:
            try: os.remove(f)
            except: pass

        logger.info(f"Processed {len(apps)} applications")
        return apps

    def _normalize_category(self, cat):
        std = {
            "AudioVideo": "Audio & Video", "Audio": "Audio", "Video": "Video",
            "Development": "Development", "Education": "Education", "Game": "Games",
            "Graphics": "Graphics", "Network": "Internet", "Office": "Office",
            "Science": "Science", "Settings": "Settings", "System": "System",
            "Utility": "Utilities"
        }
        for prefix in ["X-", "Qt", "GTK", "GNOME", "KDE"]:
            if cat.startswith(prefix):
                cat = cat[len(prefix):]
        base = cat.split(".")[-1]
        return std.get(base, base.title())

    def select_category(self, category):
        self.current_category = category
        self.filter_apps()

    def filter_apps(self):
        search = self.app.ui_manager.search_bar.text().lower()
        self.filtered_apps = [
            app for app in self.all_apps
            if (search in app["name"].lower() or search in app.get("summary","").lower()) and
               (self.current_category == "All Categories" or self.current_category in app.get("categories", []))
        ]
        self.display_apps()

    def display_apps(self):
        self.app.ui_manager.clear_apps()
        for app in self.filtered_apps:
            self.app.ui_manager.add_app_widget(self.create_app_widget(app))

    def create_app_widget(self, app):
        widget = QFrame()
        widget.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(widget)

        # Info
        info_container = QFrame()
        info_layout = QVBoxLayout(info_container)
        info_layout.addWidget(QLabel(f"{app['name']} ({app['version']})"))
        info_layout.addWidget(QLabel(app.get("summary", "No description available")))
        layout.addWidget(info_container, stretch=1)

        # Install button
        install_btn = QPushButton("Install")
        install_btn.setCheckable(True)
        install_btn.setChecked(app["app_id"] in self.selected_apps)
        install_btn.clicked.connect(lambda checked, a=app: self.toggle_app_selection(a, checked))
        layout.addWidget(install_btn)

        return widget

    def toggle_app_selection(self, app, checked):
        app_id = app["app_id"]
        if checked:
            if app_id not in self.selected_apps:
                self.selected_apps.append(app_id)
        else:
            if app_id in self.selected_apps:
                self.selected_apps.remove(app_id)
        self.app.ui_manager.install_button.setEnabled(bool(self.selected_apps))

    def install_selected_apps(self):
        if not self.selected_apps:
            return

        # Build list of selected app info dicts
        selected_info = [app for app in self.all_apps if app["app_id"] in self.selected_apps]

        dialog = InstallDialog(self.app, selected_info)
        dialog.exec_()
