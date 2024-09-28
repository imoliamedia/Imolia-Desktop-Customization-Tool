# Imolia Desktop Customizer Widgets

This directory contains the widgets available for the Imolia Desktop Customizer. As an open-source project, we welcome contributions from the community in the form of new widgets or improvements to existing ones.

## Widget Directory Structure

Each widget should have the following structure:

```
widget_name\
├── widget_name.py
├── README.md
└── screenshots\
    └── widget_screenshot.png
```

## How to Use Widgets

1. Open the Imolia Desktop Customizer application.
2. Click on the system tray icon to open the menu.
3. Select "Settings" from the menu.
4. In the Settings window, go to the "Widgets" tab.
5. You will see a list of available widgets. Check the box next to the widget you want to activate.
6. Click "Save" to apply your changes.
7. The selected widgets will now appear on your desktop.

## Adding Custom Widgets

To add your own custom widgets for personal use:

1. In the Settings window, go to the "Widgets" tab.
2. Click on the "Open Widgets Folder" button. This will open the folder where custom widgets should be placed.
3. Create a new folder for your widget following the structure outlined above.
4. Place your custom widget Python file, README, and screenshots in this folder.
5. Restart the Imolia Desktop Customizer application.
6. Your new widget should now appear in the list of available widgets.

The exact path for custom widgets is:
```
C:\Users\[YourUsername]\Documents\Imolia Desktop Customizer Widgets\
```

## Creating Your Own Widget

To create your own widget, please refer to our [Widget Development Guide](../../docs/WIDGET_DEVELOPMENT.md) for detailed instructions.

## Contributing Widgets to the Project

We encourage the community to contribute new widgets to the Imolia Desktop Customizer project. Here's how you can do that:

1. Develop your widget following the guidelines in our Widget Development Guide.
2. Fork the Imolia Desktop Customizer repository on GitHub.
3. Add your widget to the `widgets` directory in your forked repository, following the structure outlined above.
4. Create a pull request with your new widget.
5. Our team will review your submission. If approved, your widget will be added to the main repository and will be available to all users in future releases.

Please note that while anyone can create and use custom widgets locally, only reviewed and approved widgets will be added to the official GitHub repository. This ensures the quality and security of the widgets available to all users.

For more details on contributing, please see our [Contribution Guidelines](../../CONTRIBUTING.md).

## Widget Marketplace

Currently, there is no official widget marketplace. All approved widgets are included in the main Imolia Desktop Customizer repository. We may consider implementing a widget marketplace in the future to make it easier for users to discover and install community-created widgets.

If you have ideas or suggestions for improving widget distribution and discovery, please open an issue on our GitHub repository to start a discussion.