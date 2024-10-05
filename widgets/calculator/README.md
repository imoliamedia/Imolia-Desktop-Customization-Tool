# Calculator Widget

## Description
The Calculator Widget is a simple yet functional calculator for the Imolia Desktop Customization Tool. It provides basic arithmetic operations and can be customized in appearance.

## Features
- Basic arithmetic operations (addition, subtraction, multiplication, division)
- Customizable colors for background, text, and buttons
- Resizable widget with a custom move handle
- Persistent configuration

## Dependencies
- PyQt5==5.15.6

## Installation
1. Ensure you have Python 3.7 or higher installed.
2. Install the required dependencies:
   ```
   pip install PyQt5==5.15.6
   ```
3. Place the `calculator_widget.py` file in the designated widgets folder of your Imolia Desktop Customization Tool installation.

## Usage
1. Launch the Imolia Desktop Customization Tool.
2. Add the Calculator Widget to your desktop.
3. Use the buttons to perform calculations.
4. Drag the widget using the handle in the bottom-left corner to reposition it.
5. Resize the widget using the handle in the bottom-right corner.

## Customization
You can customize the following aspects of the Calculator Widget:

1. Background Color
2. Text Color
3. Button Color

To access the settings:
1. Right-click on the widget to open the settings dialog.
2. Use the color pickers to choose your preferred colors.
3. Click 'OK' to apply the changes.

## Configuration
The widget's configuration is automatically saved to `calculator_widget_config.json` in the same directory as the widget file. This ensures that your settings persist between sessions.

## Troubleshooting
If you encounter any issues:
1. Check if the widget is properly registered in the widget manager.
2. Verify that all dependencies are correctly installed.
3. Check the application logs for any error messages.
4. Ensure you have the necessary permissions to write to the configuration file.

If problems persist, please contact the Imolia Desktop Customization Tool support team.