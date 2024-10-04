# User Guide for Imolia Desktop Customization Tool

## Table of Contents
1. Installation
2. First Use
3. Using the Overlay
4. Managing Widgets
5. Adjusting Settings
6. Frequently Asked Questions (FAQ)

## 1. Installation

1. Clone the repository:
   ```
   git clone https://github.com/ImoliMedia/desktop-customization-tool.git
   ```
2. Navigate to the project directory:
   ```
   cd desktop-customization-tool
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python main.py
   ```

## 2. First Use

When you first run the Imolia Desktop Customization Tool:

1. The application will start and minimize to the system tray.
2. Click on the Imolia icon in the system tray to open the menu.
3. Select "Settings" to open the settings window.
4. In the Settings window, you can select which widgets you want to activate.
5. Click "Save" to apply your settings.
6. The selected widgets will appear on your desktop.

## 3. Using the Overlay

The overlay is the transparent layer on your desktop where widgets are displayed.

- To show/hide the overlay: Click the Imolia icon in the system tray and select "Toggle Overlay".
- The overlay will stay on top of other windows but allow click-through to interact with your desktop and other applications.

## 4. Managing Widgets

### Activating Widgets
1. Open the Settings window from the system tray icon.
2. Go to the "Widgets" tab.
3. Check the box next to the widgets you want to activate.
4. Click "Save" to apply your changes.

### Using Widgets
- Click and drag to move widgets around your desktop.
- Some widgets may have resize handles in the bottom-right corner for resizing.
- Interact with widgets as described in their individual documentation.

### Configuring Widgets
1. Open the Settings window from the system tray icon.
2. Go to the "Widgets" tab.
3. Click the settings button next to the widget you want to configure.
4. Adjust the settings in the dialog that appears.
5. Click "Save" in the widget settings dialog.
6. Click "Save" in the main Settings window to apply all changes.

### Adding Custom Widgets
1. In the Settings window, go to the "Widgets" tab.
2. Click on the "Open Widgets Folder" button.
3. Place your custom widget Python file in this folder:
   ```
   C:\Users\[YourUsername]\Documents\Imolia Desktop Customizer Widgets\
   ```
4. Restart the Imolia Desktop Customizer application.
5. Your new widget should now appear in the list of available widgets.

## 5. Adjusting Settings

To access the main settings:

1. Click the Imolia icon in the system tray.
2. Select "Settings" from the menu.

In the Settings window, you can:
- Manage and configure widgets
- Access the widgets folder

## 6. Frequently Asked Questions (FAQ)

Q: How do I completely exit the application?
A: Right-click the Imolia icon in the system tray and select "Exit".

Q: Can I use the application on multiple monitors?
A: Yes, the overlay should span across all connected monitors.

Q: How do I create my own widget?
A: Refer to our [Widget Development Guide](docs/WIDGET_DEVELOPMENT_GUIDE.md) for detailed instructions on creating custom widgets.

Q: Is my data safe?
A: The Imolia Desktop Customization Tool does not collect or transmit any personal data. All widget configurations are stored locally on your computer.

Q: How do I update the application?
A: Check our GitHub repository for the latest releases. Download and install the new version over the existing one.

For further assistance, please open an issue on our [GitHub repository](https://github.com/ImolaMedia/desktop-customization-tool/issues).
