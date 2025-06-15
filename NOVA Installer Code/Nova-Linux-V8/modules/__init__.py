"""
Nova Installer Modules
Created by Nixiews
Last updated: 2025-06-14 09:09:12 UTC
"""

from .theme_manager import ThemeManager
from .language_manager import LanguageManager
from .icon_manager import IconManager

__version__ = "8.0"
__author__ = "Nixiews"
__updated__ = "2025-06-14 09:09:12"

# Export all managers
__all__ = [
    'ThemeManager',
    'LanguageManager',
    'IconManager'
]
