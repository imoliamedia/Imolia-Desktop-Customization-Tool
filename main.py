import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.core.overlay import Overlay
from src.core.tray_icon import SystemTrayIcon
from src.utils.settings import Settings
from src.utils.logger import setup_logger
from src.utils.translation import update_language

def main():
    print("Starting the application...")  # Debug print

    # Setup logging
    logger = setup_logger()
    logger.info("Application starting")

    # Initialize application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Load settings
    settings = Settings()
    
    # Set language
    update_language(settings.get('language', 'en'))

    # Create overlay
    overlay = Overlay(settings)
    overlay.show()  # Make the overlay visible by default
    print("Overlay created and should be visible")  # Debug print

    # Create system tray icon
    icon_path = "resources/icons/tray_icon.png"
    tray_icon = SystemTrayIcon(QIcon(icon_path), overlay, settings)
    tray_icon.show()
    print(f"Tray icon created with icon from: {icon_path}")  # Debug print

    # Start the application
    print("Entering main event loop")  # Debug print
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()