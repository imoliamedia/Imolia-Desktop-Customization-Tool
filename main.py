import sys
import os
if getattr(sys, 'frozen', False):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'platforms')
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.core.overlay import Overlay
from src.config import APP_NAME
from src.core.tray_icon import SystemTrayIcon
from src.utils.settings import Settings
from src.utils.logger import setup_logger

def main():
    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    # Load settings (for application-wide settings, not widget-specific)
    settings = Settings()
    
    # Create and show overlay
    overlay = Overlay()
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