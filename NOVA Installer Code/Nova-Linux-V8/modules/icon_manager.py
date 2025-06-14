"""
Nova Installer Icon Manager
Created by Nixiews
Last updated: 2025-06-14 16:24:23 UTC
"""

import os
from pathlib import Path
import logging
from PIL import Image, ImageTk
import customtkinter as ctk

logger = logging.getLogger(__name__)

class IconManager:
    def __init__(self):
        self.icon_cache = {}
        self.data_dir = Path(__file__).parent.parent / "data"
        self.icon_path = self.data_dir / "icon.png"
        logger.info("Icon Manager initialized")

    def get_app_icon(self, size=(32, 32)):
        """Get application icon as CTkImage"""
        try:
            cache_key = f"app_icon_{size[0]}x{size[1]}"

            if cache_key not in self.icon_cache:
                if self.icon_path.exists():
                    # Load and resize the image
                    image = Image.open(self.icon_path)
                    image = image.resize(size, Image.Resampling.LANCZOS)

                    # Create CTkImage
                    ctk_image = ctk.CTkImage(
                        light_image=image,
                        dark_image=image,
                        size=size
                    )

                    self.icon_cache[cache_key] = ctk_image
                    logger.debug(f"Created {size} icon")
                else:
                    logger.warning("Icon file not found")
                    return None

            return self.icon_cache[cache_key]

        except Exception as e:
            logger.error(f"Error loading app icon: {e}")
            return None

    def set_window_icon(self, window):
        """Set window icon for both window decoration and taskbar"""
        try:
            if self.icon_path.exists():
                # Load the icon
                icon = Image.open(self.icon_path)

                # For window decoration (works on most window managers)
                window.iconphoto(True, ImageTk.PhotoImage(icon))

                # For taskbar (works on most desktop environments)
                icon_photo = ImageTk.PhotoImage(icon)
                window.tk.call('wm', 'iconphoto', window._w, icon_photo)

                # For WM_CLASS (helps with proper taskbar grouping)
                window.wm_class = "Nova Installer"

                # Additional X11-specific icon hint
                if os.environ.get('XDG_SESSION_TYPE') == 'x11':
                    window.tk.call('wm', 'iconname', window._w, 'nova-installer')

                logger.info("Window icon set successfully")

            else:
                logger.warning("Icon file not found for window icon")

        except Exception as e:
            logger.error(f"Error setting window icon: {e}")
