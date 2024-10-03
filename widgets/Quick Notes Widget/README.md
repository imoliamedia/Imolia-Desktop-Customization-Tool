# Quick Notes Widget

## Description
The Quick Notes Widget is a simple yet powerful tool for the Imolia Desktop Customization Tool, allowing users to quickly jot down and view notes directly on their desktop. It provides an easy-to-use interface for creating, editing, and managing quick notes without the need to open a separate application.

## Features
- Draggable and resizable widget
- Real-time text editing
- Auto-save functionality (every 30 seconds)
- Clear button to quickly erase all notes
- Customizable appearance (background color, text color, and font)
- Persistent storage of notes and widget configuration

## Installation
1. Ensure you have the Imolia Desktop Customization Tool installed.
2. Copy the `quick_notes_widget.py` file to your Imolia Desktop Customizer Widgets folder (usually located at `C:\Users\[YourUsername]\Documents\Imolia Desktop Customizer Widgets\`).
3. Restart the Imolia Desktop Customization Tool or refresh the widget list.

## Usage
1. Open the Imolia Desktop Customization Tool settings.
2. Navigate to the Widgets tab.
3. Find and activate the "Quick Notes" widget.
4. The widget will appear on your desktop.
5. Click and drag to move the widget.
6. Click and drag the bottom-right corner to resize the widget.
7. Start typing to add notes.

## Customization
You can customize the appearance of the Quick Notes Widget:

1. Right-click on the widget and select "Settings" from the context menu.
2. In the settings dialog, you can:
   - Change the background color
   - Change the text color
   - Choose a different font and font size
3. Click "Save" to apply your changes.

## Configuration
The widget configuration is stored in a JSON file named `quick_notes_widget_config.json` in the same directory as the widget. This file contains:

- Background color
- Text color
- Font family and size
- Widget size and position
- Current note content

You can manually edit this file, but it's recommended to use the built-in settings dialog to make changes.

## Dependencies
This widget requires:
- PyQt5 (version 5.15.6 or later)

## Troubleshooting
If you encounter any issues:
1. Ensure your Imolia Desktop Customization Tool is up to date.
2. Check that the widget file is in the correct directory.
3. Verify that you have the required dependencies installed.
4. If problems persist, try deleting the `quick_notes_widget_config.json` file to reset the widget to default settings.

## Contributing
Feel free to fork this widget and make your own modifications. If you develop improvements that you think would benefit other users, consider submitting a pull request to the main Imolia Desktop Customization Tool repository.

## License
This widget is released under the GNU General Public License v3.0, in line with the Imolia Desktop Customization Tool's licensing.

## Support
For support, please open an issue on the Imolia Desktop Customization Tool's GitHub repository or contact the Imolia Media support team.