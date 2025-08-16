"""
Nova Installer UI Manager
Created by Nixiews
Last updated: 2025-08-16 21:49:35 UTC
"""

from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QPushButton,
                            QLineEdit, QScrollArea, QFrame)
from PyQt5.QtCore import Qt

class UIManager:
    def __init__(self, app):
        self.app = app
        self.setup_category_frame()
        self.setup_content_frame()

    def setup_category_frame(self):
        """Setup the category frame"""
        layout = QVBoxLayout(self.app.category_frame)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Categories")
        title.setFont(self.app.fonts["header"])
        layout.addWidget(title)

        # Scrollable categories
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.category_container = QFrame()
        self.category_layout = QVBoxLayout(self.category_container)
        self.category_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.category_container)
        layout.addWidget(scroll)

    def setup_content_frame(self):
        """Setup the content frame"""
        layout = QVBoxLayout(self.app.content_frame)
        layout.setContentsMargins(10, 10, 10, 10)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search applications...")
        layout.addWidget(self.search_bar)

        # Apps scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.apps_container = QFrame()
        self.apps_layout = QVBoxLayout(self.apps_container)
        self.apps_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.apps_container)
        layout.addWidget(scroll)

        # Install button
        self.install_button = QPushButton("Install Selected")
        self.install_button.setEnabled(False)
        layout.addWidget(self.install_button)

    def update_categories(self, categories, on_click):
        """Update category buttons"""
        # Clear existing buttons
        while self.category_layout.count():
            item = self.category_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new buttons
        for category in categories:
            button = QPushButton(category)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, c=category: on_click(c))
            self.category_layout.addWidget(button)
            if category == "All Categories":
                button.setChecked(True)

    def clear_apps(self):
        """Clear all app widgets"""
        while self.apps_layout.count():
            item = self.apps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_app_widget(self, widget):
        """Add an app widget"""
        self.apps_layout.addWidget(widget)
