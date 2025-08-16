"""
Nova Installer Icon Manager
Created by Nixiews
Last updated: 2025-08-16 20:58:20 UTC
"""

import os
import logging
from pathlib import Path
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize

logger = logging.getLogger(__name__)

class IconManager:
    def __init__(self):
        self.icon_cache = {}
        self.data_dir = Path(__file__).parent.parent / "data"
        self.icon_path = self.data_dir / "icon.png"
        logger.info("Icon Manager initialized")

    def get_app_icon(self, size=(32, 32)):
        """Get application icon as QIcon"""
        try:
            cache_key = f"app_icon_{size[0]}x{size[1]}"

            if cache_key not in self.icon_cache:
                if self.icon_path.exists():
                    # Create QIcon and add to cache
                    icon = QIcon(str(self.icon_path))
                    self.icon_cache[cache_key] = icon
                    logger.debug(f"Created {size} icon")
                else:
                    logger.warning("Icon file not found")
                    return None

            return self.icon_cache[cache_key]

        except Exception as e:
            logger.error(f"Error loading app icon: {e}")
            return None

    def set_window_icon(self, window):
        """Set window icon"""
        try:
            if self.icon_path.exists():
                # Create and set icon
                icon = QIcon(str(self.icon_path))
                window.setWindowIcon(icon)
                logger.info("Window icon set successfully")
            else:
                logger.warning("Icon file not found for window icon")

        except Exception as e:
            logger.error(f"Error setting window icon: {e}")
