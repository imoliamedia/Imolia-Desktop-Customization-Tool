# Copyright (C) 2024 Imolia Media
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os
from pathlib import Path

# Configureer embedded Python als we in een PyInstaller executable zijn
if getattr(sys, 'frozen', False):
    # We zijn in een PyInstaller executable
    base_dir = os.path.dirname(sys.executable)
    
    # Voeg de embedded Python toe aan PATH
    embedded_python_dir = os.path.join(base_dir, "embedded_python")
    if os.path.exists(embedded_python_dir):
        os.environ['PATH'] = f"{embedded_python_dir};{os.environ.get('PATH', '')}"
        # Voeg embedded Python Scripts toe aan PATH
        scripts_dir = os.path.join(embedded_python_dir, "Scripts")
        if os.path.exists(scripts_dir):
            os.environ['PATH'] = f"{scripts_dir};{os.environ.get('PATH', '')}"

# Zorg ervoor dat alle Python modules beschikbaar zijn
if getattr(sys, 'frozen', False):
    # We runnen vanuit een PyInstaller executable
    base_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    # We runnen vanuit een Python script
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Voeg base_dir toe aan sys.path voor imports
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Zorgen dat QT plugins correct worden gevonden in frozen executable
if getattr(sys, 'frozen', False):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'platforms')

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.core.overlay import Overlay
from src.config import APP_NAME
from src.core.tray_icon import SystemTrayIcon
from src.utils.settings import Settings
from src.utils.logger import setup_logger
from src.utils.widget_loader import WidgetManager

def main():
    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    # Setup logger
    logger = setup_logger()
    logger.info("Applicatie wordt gestart")
    logger.info(f"Python versie: {sys.version}")
    logger.info(f"Systeem: {sys.platform}")
    
    if getattr(sys, 'frozen', False):
        logger.info(f"Applicatie draait als PyInstaller executable")
        logger.info(f"Executable pad: {sys.executable}")
        # Log embedded Python pad
        embedded_python_dir = os.path.join(os.path.dirname(sys.executable), "embedded_python")
        if os.path.exists(embedded_python_dir):
            logger.info(f"Embedded Python gevonden op: {embedded_python_dir}")
        else:
            logger.warning(f"Geen embedded Python gevonden in: {embedded_python_dir}")
    else:
        logger.info(f"Applicatie draait als Python script")

    # Load settings (for application-wide settings, not widget-specific)
    settings = Settings()

    # Create and show overlay
    overlay = Overlay(settings)
    overlay.initUI()
    overlay.show()  # Make the overlay visible by default

    # Create system tray icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icons", "tray_icon.ico")
    tray_icon = SystemTrayIcon(QIcon(icon_path), overlay, settings)
    tray_icon.show()

    # Start the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()