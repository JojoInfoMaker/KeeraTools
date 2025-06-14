"""
Nova Installer Dialogs
Created by Nixiews
Last updated: 2025-06-14 09:09:12 UTC
"""

from .install_dialog import InstallDialog
from .color_dialog import ColorDialog
from .language_dialog import LanguageDialog
from .about_dialog import AboutDialog

__version__ = "8.0"
__author__ = "Nixiews"
__updated__ = "2025-06-14 09:09:12"

# Export all dialogs
__all__ = [
    'InstallDialog',
    'ColorDialog',
    'LanguageDialog',
    'AboutDialog'
]
