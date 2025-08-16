"""
Nova Installer App Manager
Created by Nixiews
Last updated: 2025-08-16 21:49:35 UTC
"""

import os
import json
import logging
import requests
import gzip
import xml.etree.ElementTree as ET
import tempfile
from datetime import datetime, timedelta
from threading import Thread
from PyQt5.QtWidgets import (QFrame, QLabel, QPushButton, QVBoxLayout,
                            QHBoxLayout, QProgressDialog, QMessageBox)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QMetaObject, Q_ARG, Qt
from PyQt5.QtGui import QPixmap

logger = logging.getLogger(__name__)

class AppDataSignals(QObject):
    """Signals for app data processing"""
    apps_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

class AppManager(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.selected_apps = []
        self.all_apps = []
        self.filtered_apps = []
        self.current_category = "All Categories"
        self.category_buttons = {}

        # Setup signals
        self.signals = AppDataSignals()
        self.signals.apps_loaded.connect(self._on_apps_loaded)
        self.signals.error_occurred.connect(self._on_error)

        # Connect UI signals
        self.app.ui_manager.search_bar.textChanged.connect(self.filter_apps)
        self.app.ui_manager.install_button.clicked.connect(self.install_selected)

        # Start loading apps
        self.load_apps()

    def load_apps(self):
        """Load apps data"""
        self.progress_dialog = QProgressDialog("Loading applications...", None, 0, 100, self.app)
        self.progress_dialog.setWindowTitle("Loading")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()

        # Start background thread
        Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        """Fetch data in background thread"""
        try:
            apps_data = self._download_and_parse_appstream()
            self.signals.apps_loaded.emit(apps_data)
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            self.signals.error_occurred.emit(str(e))

    def _on_apps_loaded(self, apps_data):
        """Handle loaded apps data in main thread"""
        try:
            self.progress_dialog.close()
            self.all_apps = apps_data
            self.filtered_apps = apps_data

            # Extract categories
            categories = {"All Categories"}
            for app in apps_data:
                categories.update(app.get('categories', []))

            # Update UI in main thread
            self.app.ui_manager.update_categories(sorted(categories), self.select_category)
            self.display_apps()

        except Exception as e:
            logger.error(f"Error processing apps data: {e}")
            self._on_error(str(e))

    def _on_error(self, error_msg):
        """Handle errors in main thread"""
        self.progress_dialog.close()
        QMessageBox.critical(self.app, "Error", f"Failed to load applications: {error_msg}")

    def _download_and_parse_appstream(self):
        """Download and parse the Flathub appstream file"""
        try:
            logger.info("Downloading Flathub appstream data...")
            response = requests.get(
                "https://dl.flathub.org/beta-repo/appstream/x86_64/appstream.xml.gz",
                stream=True
            )
            response.raise_for_status()

            # Create temp directory
            temp_dir = os.path.join(tempfile.gettempdir(), 'nova-installer')
            os.makedirs(temp_dir, exist_ok=True)

            # Save and decompress files
            gz_path = os.path.join(temp_dir, 'appstream.xml.gz')
            xml_path = os.path.join(temp_dir, 'appstream.xml')

            with open(gz_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info("Decompressing appstream data...")
            with gzip.open(gz_path, 'rb') as gz_file:
                with open(xml_path, 'wb') as xml_file:
                    xml_file.write(gz_file.read())

            # Parse XML
            logger.info("Parsing appstream XML...")
            tree = ET.parse(xml_path)
            root = tree.getroot()

            apps = []
            # Look for components in all possible namespaces
            components = (
                root.findall(".//component") +
                root.findall(".//{http://www.freedesktop.org/software/appstream/appdata}component")
            )

            for component in components:
                try:
                    # Check for various component types that could be applications
                    component_type = component.get('type', '')
                    if component_type not in ['desktop', 'desktop-application', 'webapp']:
                        continue

                    # Get application ID (try multiple possible tags)
                    app_id = None
                    for id_tag in ['id', 'bundle', './/id', './/bundle']:
                        id_elem = component.find(id_tag)
                        if id_elem is not None and id_elem.text:
                            app_id = id_elem.text
                            break

                    if not app_id:
                        continue

                    # Clean up the app ID (remove any prefixes if present)
                    if app_id.startswith('flatpak:'):
                        app_id = app_id[8:]

                    # Get application name (try multiple possible tags)
                    name = None
                    for name_tag in ['name', './/name', 'summary', './/summary']:
                        name_elem = component.find(name_tag)
                        if name_elem is not None and name_elem.text:
                            name = name_elem.text
                            break

                    if not name:
                        name = app_id

                    # Process categories
                    categories = []
                    for cat_elem in component.findall('.//category'):
                        if cat_elem.text:
                            normalized = self._normalize_category(cat_elem.text)
                            if normalized:
                                categories.append(normalized)

                    # If no categories found, check for desktop categories
                    if not categories:
                        for cat_elem in component.findall('.//categories/category'):
                            if cat_elem.text:
                                normalized = self._normalize_category(cat_elem.text)
                                if normalized:
                                    categories.append(normalized)

                    # If still no categories, add to "Other"
                    if not categories:
                        categories = ["Other"]

                    # Get latest version
                    version = 'latest'
                    releases = component.findall('.//release')
                    if releases:
                        version = releases[0].get('version', 'latest')

                    # Get summary and description
                    summary = ''
                    summary_elem = component.find('.//summary')
                    if summary_elem is not None and summary_elem.text:
                        summary = summary_elem.text

                    description = ''
                    desc_elem = component.find('.//description')
                    if desc_elem is not None:
                        description = ET.tostring(desc_elem, encoding='unicode', method='xml')

                    app_data = {
                        'app_id': app_id,
                        'name': name,
                        'summary': summary,
                        'description': description,
                        'categories': list(set(categories)),  # Remove duplicates
                        'version': version,
                        'bundle_type': 'flatpak'
                    }

                    # Process icons
                    icons = component.findall('.//icon')
                    icon_urls = []
                    for icon in icons:
                        if icon.get('type') == 'remote':
                            icon_urls.append(icon.text)
                    app_data['icon_urls'] = icon_urls

                    # Process screenshots
                    screenshots = []
                    for screenshot in component.findall('.//screenshot'):
                        for image in screenshot.findall('.//image'):
                            if image.get('type') == 'source':
                                screenshots.append({'url': image.text})
                                break
                    app_data['screenshots'] = screenshots

                    apps.append(app_data)

                except Exception as e:
                    logger.error(f"Error processing component: {e}")
                    continue

            # Sort apps by name
            apps.sort(key=lambda x: x['name'].lower())

            # Cleanup
            try:
                os.remove(gz_path)
                os.remove(xml_path)
            except:
                pass

            logger.info(f"Successfully processed {len(apps)} applications")
            return apps

        except Exception as e:
            logger.error(f"Error downloading/parsing appstream data: {e}")
            raise

    def _normalize_category(self, category):
        """Convert raw category to user-friendly name"""
        STANDARD_CATEGORIES = {
            "AudioVideo": "Audio & Video",
            "Audio": "Audio",
            "Video": "Video",
            "Development": "Development",
            "Education": "Education",
            "Game": "Games",
            "Graphics": "Graphics",
            "Network": "Internet",
            "Office": "Office",
            "Science": "Science",
            "Settings": "Settings",
            "System": "System",
            "Utility": "Utilities"
        }

        # Remove common prefixes
        for prefix in ['X-', 'Qt', 'GTK', 'GNOME', 'KDE']:
            if category.startswith(prefix):
                category = category[len(prefix):]

        base_category = category.split('.')[-1]
        return STANDARD_CATEGORIES.get(base_category, base_category.title())

    def select_category(self, category):
        """Handle category selection"""
        self.current_category = category
        self.filter_apps()

    def filter_apps(self):
        """Filter apps based on search text and category"""
        search_text = self.app.ui_manager.search_bar.text().lower()

        self.filtered_apps = []
        for app in self.all_apps:
            name_match = search_text in app['name'].lower()
            summary_match = search_text in app.get('summary', '').lower()
            category_match = (self.current_category == "All Categories" or
                            self.current_category in app.get('categories', []))

            if (name_match or summary_match) and category_match:
                self.filtered_apps.append(app)

        self.display_apps()

    def display_apps(self):
        """Display filtered apps"""
        self.app.ui_manager.clear_apps()
        for app in self.filtered_apps:
            app_widget = self.create_app_widget(app)
            self.app.ui_manager.add_app_widget(app_widget)

    def create_app_widget(self, app):
        """Create widget for an app"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(widget)

        # Info container
        info_container = QFrame()
        info_layout = QVBoxLayout(info_container)

        # App name and version
        name_label = QLabel(f"{app['name']} ({app['version']})")
        name_label.setFont(self.app.fonts["normal"])
        info_layout.addWidget(name_label)

        # Description
        desc_label = QLabel(app.get('summary', 'No description available'))
        desc_label.setWordWrap(True)
        desc_label.setFont(self.app.fonts["small"])
        info_layout.addWidget(desc_label)

        layout.addWidget(info_container, stretch=1)

        # Install button
        install_btn = QPushButton("Install")
        install_btn.setCheckable(True)
        install_btn.setChecked(app['app_id'] in self.selected_apps)
        install_btn.clicked.connect(lambda checked, a=app: self.toggle_app_selection(a, checked))
        layout.addWidget(install_btn)

        return widget

    def toggle_app_selection(self, app, checked):
        """Toggle app selection"""
        app_id = app['app_id']
        if checked and app_id not in self.selected_apps:
            self.selected_apps.append(app_id)
        elif not checked and app_id in self.selected_apps:
            self.selected_apps.remove(app_id)

        self.app.ui_manager.install_button.setEnabled(bool(self.selected_apps))

    def install_selected(self):
        """Install selected apps"""
        if not self.selected_apps:
            QMessageBox.warning(self.app, "Warning", "No applications selected.")
            return

        # TODO: Implement installation
        QMessageBox.information(self.app, "Info", "Installation not yet implemented.")
