# Comprehensive Widget Development Guide for Imolia Desktop Customization Tool

## Table of Contents
1. [Introduction](#introduction)
2. [Setting Up Your Development Environment](#setting-up-your-development-environment)
3. [Widget Basics](#widget-basics)
4. [Creating Your First Widget](#creating-your-first-widget)
5. [Widget Configuration and Customization](#widget-configuration-and-customization)
6. [Styling Your Widget](#styling-your-widget)
7. [Making Your Widget Resizable and Draggable](#making-your-widget-resizable-and-draggable)
8. [Implementing Regular Updates](#implementing-regular-updates)
9. [Creating a Widget Settings Dialog](#creating-a-widget-settings-dialog)
10. [Advanced Widget Features](#advanced-widget-features)
11. [Best Practices](#best-practices)
12. [Testing Your Widget](#testing-your-widget)
13. [Adding Your Widget to the Application](#adding-your-widget-to-the-application)
14. [Handling Dependencies](#handling-dependencies)
15. [Error Handling and Logging](#error-handling-and-logging)
16. [Troubleshooting Common Issues](#troubleshooting-common-issues)
17. [Example Widgets](#example-widgets)

## Introduction
This guide provides comprehensive instructions for developing widgets for the Imolia Desktop Customization Tool. By following this guide, you'll be able to create custom widgets that seamlessly integrate with the application.

## Setting Up Your Development Environment
1. Ensure you have Python 3.7 or higher installed.
2. Clone the Imolia Desktop Customization Tool repository:
   ```
   git clone https://github.com/ImoliMedia/desktop-customization-tool.git
   ```
3. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Widget Basics
All widgets in the Imolia Desktop Customization Tool should inherit from the `DraggableWidget` class, which provides essential functionality:
- Dragging and resizing capabilities
- Basic configuration management
- Integration with the main application

Key concepts:
- Widgets are self-contained modules
- Each widget manages its own configuration
- Widgets can be resized and moved by the user
- Widgets should have their own settings dialog

## Creating Your First Widget
Here's a template for creating a basic widget:

```python
"""
MyCustomWidget

Dependencies:
PyQt5==5.15.6
"""

import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from src.utils.draggable_widget import DraggableWidget
from src.utils.base_widget_settings_dialog import BaseWidgetSettingsDialog

class MyCustomWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'my_custom_widget_config.json')
        default_config = {
            'color': 'white',
            'size': (200, 100),
            'position': (100, 100),
        }
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        return default_config

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'my_custom_widget_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        layout = QVBoxLayout()
        self.label = QLabel("Hello, I'm a custom widget!")
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.setMinimumSize(100, 50)
        size = self.config.get('size', (200, 100))
        self.resize(*size)
        
        position = self.config.get('position', (100, 100))
        self.move(*position)

        self.updateStyle()

    def updateStyle(self):
        color = self.config.get('color', 'white')
        self.setStyleSheet(f"""
            QWidget {{
                color: {color};
                background-color: rgba(0, 0, 0, 100);
                border-radius: 10px;
            }}
        """)
        self.adjustFontSize()

    def adjustFontSize(self):
        font = QFont()
        font.setPixelSize(int(self.height() * 0.2))
        self.label.setFont(font)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustFontSize()
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

    def updateConfig(self, new_config):
        self.config.update(new_config)
        self.updateStyle()
        self.save_config()

    def openSettings(self):
        dialog = MyCustomWidgetSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

class MyCustomWidgetSettingsDialog(BaseWidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(parent, widget_name="My Custom Widget")
        self.widget = widget

    def create_settings_tab(self):
        tab = super().create_settings_tab()
        layout = tab.layout()
        
        # Add your widget-specific settings here
        
        return tab

    def save_settings(self):
        # Save your widget-specific settings here
        super().save_settings()

# Important: The class must be named 'Widget' for the loader to recognize it
Widget = MyCustomWidget
```

## Widget Configuration and Customization
- Use a `config` dictionary to store customizable properties.
- Implement `load_config()` and `save_config()` methods for persistent storage.
- Use `updateConfig()` for dynamic updates to the widget's appearance and behavior.

## Styling Your Widget
- Implement the `updateStyle` method to apply styles based on the configuration.
- Use Qt stylesheets for complex styling.
- Consider using transparent backgrounds for better desktop integration.

## Making Your Widget Resizable and Draggable
The `DraggableWidget` base class provides basic functionality for resizing and moving. 
- Override `resizeEvent` and `moveEvent` to handle size and position changes.
- Save the new size and position in these events to persist them.

## Implementing Regular Updates
If your widget needs to update regularly (e.g., a clock or system monitor):
1. Set up a QTimer in your `initUI` method:
   ```python
   self.timer = QTimer(self)
   self.timer.timeout.connect(self.update_widget)
   self.timer.start(1000)  # Update every 1000 ms
   ```
2. Implement the `update_widget` method:
   ```python
   def update_widget(self):
       # Update your widget's content here
       pass
   ```

## Creating a Widget Settings Dialog
Use the `BaseWidgetSettingsDialog` to create a consistent settings experience:

```python
from src.utils.base_widget_settings_dialog import BaseWidgetSettingsDialog

class MyWidgetSettingsDialog(BaseWidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(parent, widget_name="My Widget")
        self.widget = widget

    def create_settings_tab(self):
        tab = super().create_settings_tab()
        layout = tab.layout()
        
        # Add your widget-specific settings here
        # Example:
        layout.addWidget(QLabel("My Setting:"))
        self.my_setting_input = QLineEdit(self.widget.config.get('my_setting', ''))
        layout.addWidget(self.my_setting_input)
        
        return tab

    def save_settings(self):
        # Save your widget-specific settings
        self.widget.config['my_setting'] = self.my_setting_input.text()
        self.widget.save_config()
        super().save_settings()
```

## Advanced Widget Features
- Implement custom context menus for additional functionality.
- Use Qt's event system for complex interactions.
- Consider adding keyboard shortcuts for power users.

## Best Practices
- Follow PEP 8 style guidelines.
- Use meaningful variable and function names.
- Comment your code, especially for complex logic.
- Handle errors gracefully, especially when loading/saving configurations.
- Optimize for performance, especially if your widget updates frequently.

## Testing Your Widget
- Create unit tests for your widget's core functionality.
- Test your widget in different scenarios (resizing, configuration changes, etc.).
- Use Qt's test framework for GUI testing.

## Adding Your Widget to the Application
1. Create a new Python file in the `widgets` folder.
2. Implement your widget as described in this guide.
3. Ensure the main widget class is aliased as `Widget`.
4. Restart the Imolia Desktop Customizer application.

## Handling Dependencies
- List all dependencies at the top of your widget file in a comment block.
- Use the virtual environment system implemented in the application to manage widget-specific dependencies.
- Implement a method to install dependencies if necessary:

```python
@staticmethod
def install_dependencies():
    try:
        python_executable = sys.executable
        pip_command = [python_executable, "-m", "pip", "install", "your-dependency==1.0.0"]
        result = subprocess.run(pip_command, capture_output=True, text=True, check=True)
        logger.info(f"Pip install output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e}")
        logger.error(f"Pip install error output: {e.stderr}")
        return False
```

## Error Handling and Logging
- Use Python's `logging` module for comprehensive logging:

```python
import logging

logger = logging.getLogger(__name__)

# Usage
logger.debug("Debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

- Log important events, errors, and state changes in your widget.
- Use try-except blocks to handle potential errors gracefully.

## Troubleshooting Common Issues
- Widget not appearing: 
  - Check if it's properly registered in the widget manager.
  - Verify that all dependencies are correctly installed.
  - Check the application logs for any error messages during widget initialization.
- Styling issues: 
  - Ensure all style properties are properly set and updated.
  - Verify that the `updateStyle` method is called after any configuration changes.
- Performance problems: 
  - Profile your code and optimize heavy operations.
  - Consider using background threads for time-consuming tasks.
- Configuration not saving: 
  - Verify the `save_config` method is called appropriately.
  - Check file permissions for the configuration file location.
- Dependency issues:
  - Ensure that the `install_dependencies` method is implemented and called.
  - Verify that the correct Python interpreter is being used (especially in virtual environments).
  - Check for any conflicts between widget dependencies and the main application.

## Example Widgets
For more detailed examples, refer to the following widgets in the `widgets` folder:
- Clock Widget
- System Monitor Widget
- Calculator Widget
- Modern Todo Widget
- Google Calendar Widget

These examples demonstrate various techniques and best practices for widget development.

Remember to thoroughly test your widget in various scenarios and with different configurations to ensure stability and performance. Always provide clear error messages and logging to help diagnose issues that may arise during development or use.