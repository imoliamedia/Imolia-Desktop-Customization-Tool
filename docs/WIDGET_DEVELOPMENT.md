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
1. Ensure you have Python 3.9 or higher installed.
2. Clone the Imolia Desktop Customization Tool repository:
   ```
   git clone https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool.git
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
Here's a template for creating a basic widget, following the same
`DraggableWidget` + `WidgetSettingsDialog` pattern used by every bundled
widget (clock, calculator, system monitor, ...) - not the standalone
`BaseWidgetSettingsDialog` utility class, which exists in the codebase but
isn't actually used by any real widget:

```python
"""
MyCustomWidget

Dependencies:
PyQt5==5.15.6
"""

import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

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

class MyCustomWidgetSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def add_custom_section(self, layout):
        # Add your widget-specific settings here. If you want a color
        # picker, see "Creating a Widget Settings Dialog" below - the
        # base class's own get_config() expects a self.color_button to
        # exist, so skipping it will crash the dialog on Save.
        pass

    def get_config(self):
        config = super().get_config()
        # Add your widget-specific fields to the returned dict here.
        return config

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
Use `WidgetSettingsDialog` (from `src.utils.draggable_widget`) to create a
consistent settings experience - this is the base class every bundled
widget's settings dialog actually inherits from. It already builds the
dialog's "Save"/"Cancel" buttons and a "Behavior" section with an
update-interval spinner; you only need to override `add_custom_section()`
(to add your own fields to the UI) and `get_config()` (to include their
values in the dict that gets saved):

```python
from PyQt5.QtWidgets import QLineEdit, QLabel, QHBoxLayout
from src.utils.draggable_widget import WidgetSettingsDialog

class MyWidgetSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def add_custom_section(self, layout):
        setting_layout = QHBoxLayout()
        setting_layout.addWidget(QLabel("My Setting:"))
        self.my_setting_input = QLineEdit(self.widget.config.get('my_setting', ''))
        setting_layout.addWidget(self.my_setting_input)
        layout.addLayout(setting_layout)

    def get_config(self):
        config = super().get_config()
        config.update({
            'my_setting': self.my_setting_input.text(),
        })
        return config
```

Saving is already wired up for you: the dialog's "Save" button calls
`get_config()` and passes the result to `widget.updateConfig()`, which
merges it into `widget.config` and calls `save_config()`. You don't need
to (and shouldn't) write your own save button or call `save_config()`
directly from the dialog.

**A gotcha worth knowing:** `WidgetSettingsDialog`'s own `get_config()`
tries to read a color from `self.color_button` (via its Qt palette). If
your `add_custom_section()` doesn't create a `self.color_button`, calling
`super().get_config()` will raise an `AttributeError` the moment the user
clicks "Save" - a real bug that shipped in the System Monitor widget for a
while. If you want a color picker, follow `clock_widget.py`'s pattern:

```python
from PyQt5.QtWidgets import QPushButton, QColorDialog
from PyQt5.QtGui import QColor

def add_custom_section(self, layout):
    self.color_button = QPushButton()
    self.color_button.setStyleSheet(f"background-color: {self.widget.config.get('color', 'white')};")
    self.color_button.clicked.connect(self.choose_color)
    layout.addWidget(self.color_button)

def choose_color(self):
    # Override this too: setStyleSheet() doesn't update the button's
    # QPalette, so the base class's palette-based color read would
    # otherwise always return the wrong (default) color.
    color = QColorDialog.getColor(QColor(self.widget.config.get('color', 'white')))
    if color.isValid():
        self.color_button.setStyleSheet(f"background-color: {color.name()};")
        self.widget.config['color'] = color.name()

def get_config(self):
    config = super().get_config()
    config['color'] = self.widget.config.get('color', 'white')
    return config
```

If you don't need a color picker at all, just don't call
`super().get_config()` - build and return your own dict from
`get_config()` instead (see the ESP32 Web Dashboard widget for an example
of a settings dialog with no color/behavior section at all).

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
Dependencies are declared declaratively, not installed by your own code -
there is no `install_dependencies()` method to implement.

List every dependency as one `package==version` line per line, inside a
`Dependencies:` block in your widget file's module docstring:

```python
"""
MyCustomWidget

Dependencies:
PyQt5==5.15.6
requests==2.28.1
"""
```

`WidgetManager` parses this block automatically (see
`parse_dependencies()` in `src/utils/widget_loader.py`) and installs
anything missing via `PackageManager` before your widget is activated -
you don't write or call any install logic yourself. `PyQt5` is assumed
and doesn't strictly need to be listed, but doing so anyway is the
convention every bundled widget follows.

A few things worth knowing about how this works in practice:
- If the exact package (and version) is already importable in the running
  process - true for anything the app was built with, like `psutil` or
  `requests` - it's used as-is; nothing gets reinstalled.
- Otherwise, dependencies are installed into the app's own managed
  packages folder (`%APPDATA%\Imolia Desktop Customizer\packages`) via
  pip, using an embedded Python interpreter when running as a packaged
  `.exe`. This requires internet access and can take a moment the first
  time a genuinely new dependency is needed.
- Pin exact versions. An unpinned or since-removed version can make
  installation fail outright - `requests==2.22.1` in this project's own
  `requirements.txt` did exactly that after PyPI stopped distributing it.

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
  - If you copy a widget file to run multiple instances, make sure each
    copy's config filename is derived from its own filename (see the
    ESP32 Web Dashboard widget) - a fixed filename means every copy
    overwrites the same shared file.
- Settings dialog crashes on Save:
  - If your `get_config()` calls `super().get_config()`, make sure
    `add_custom_section()` created a `self.color_button` - see the
    gotcha explained under "Creating a Widget Settings Dialog".
- Dependency issues:
  - Double-check the `Dependencies:` block in your widget's docstring -
    package names and versions must match exactly what's installable
    from PyPI (a removed/yanked version will fail every time).
  - Installing a new dependency in a packaged `.exe` requires internet
    access; check the app log if it seems to hang or fail silently.

## Example Widgets
For more detailed examples, refer to the following widgets in the `widgets` folder:
- Clock Widget - color picker + font/format settings, the reference `choose_color`/`get_config` pattern
- System Monitor Widget - a periodic `QTimer` update, with its own defensive error handling
- Calculator Widget
- Modern Todo Widget
- Google Calendar Widget - fetching data from a network API
- ESP32 Web Dashboard Widget - `QWebEngineView`, a fully custom settings dialog with no color/behavior section, and a per-file (not fixed) config filename to safely support running multiple copies at once

These examples demonstrate various techniques and best practices for widget development.

Remember to thoroughly test your widget in various scenarios and with different configurations to ensure stability and performance. Always provide clear error messages and logging to help diagnose issues that may arise during development or use.