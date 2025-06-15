#!/usr/bin/env python3
"""
Nova Installer Main Application
Created by Nixiews
Last updated: 2025-06-14 16:51:09 UTC
"""

import os
import sys
import logging
from tkinter import messagebox
from modules.app import NovaInstallerApp

# Configure logging
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "nova_installer.log")

os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging to write only to file, not to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE)  # Only file handler, no StreamHandler
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point of the application"""
    try:
        logger.info(f"Starting Nova Installer - Time: 2025-06-14 16:51:09 - User: Nixiews")
        app = NovaInstallerApp()
        app.run()
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
        messagebox.showerror(
            "Critical Error",
            f"An unexpected error occurred: {str(e)}\n\nPlease check the logs for more details."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
