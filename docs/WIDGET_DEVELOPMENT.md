# Comprehensive Widget Development Guide for Imolia Desktop Customization Tool

## Introduction
This guide reflects the current state of widget development for the Imolia Desktop Customization Tool, based on our working widgets including Clock, System Monitor, Google Calendar, Modern Todo, and Calculator.

## Table of Contents
1. Widget Basics
2. Setting Up Your Development Environment
3. Creating Your First Widget
4. Widget Configuration and Customization
5. Styling Your Widget
6. Making Your Widget Resizable and Draggable
7. Implementing Regular Updates
8. Advanced Widget Features
9. Best Practices
10. Testing Your Widget
11. Adding Your Widget to the Application
12. Handling Dependencies
13. Error Handling and Logging
14. Troubleshooting Common Issues

## 1. Widget Basics
All widgets should inherit from the `DraggableWidget` class, which provides essential functionality like dragging, resizing, and basic configuration management.

Key concepts:
- Widgets are self-contained modules
- Each widget manages its own configuration
- Widgets can be resized and moved by the user
- Widgets should have their own settings dialog
- Consider implementing a custom move handle for easier widget repositioning

## 2. Setting Up Your Development Environment
Ensure you have:
- Python 3.7 or higher
- PyQt5 installed (`pip install PyQt5`)
- Any additional dependencies specific to your widget

Clone the Imolia Desktop Customization Tool repository and install requirements.

## 3. Creating Your First Widget
Here's an updated template based on our working widgets:

```python
"""
MyCustomWidget

Dependencies:
PyQt5==5.15.6
# List any other dependencies here
"""

import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor, QPainter, QPolygon
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

class MoveHandle(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.SizeAllCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(100, 100, 100))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(QPolygon([QPoint(0, 20), QPoint(20, 20), QPoint(0, 0)]))

class MyCustomWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()
        self.move_handle = MoveHandle(self)
        self.move_handle.move(0, self.height() - 20)

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'my_custom_widget_config.json')
        default_config = {
            'color': 'white',
            'size': (200, 100),
            'position': (100, 100),
            # Add other default configuration options here
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

        # Setup timer for regular updates if needed
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_widget)
        self.timer.start(1000)  # Update every 1000 ms

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
        font.setPixelSize(int(self.height() * 0.2))  # 20% of height
        self.label.setFont(font)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustFontSize()
        self.move_handle.move(0, self.height() - 20)
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

    def update_widget(self):
        # Implement any regular updates here
        pass

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
        # Add custom settings here

    def get_config(self):
        config = super().get_config()
        # Add custom settings to config here
        return config

# Important: The class must be named 'Widget' for the loader to recognize it
Widget = MyCustomWidget
```

## 4. Widget Configuration and Customization
- Use a `config` dictionary to store customizable properties.
- Implement `load_config()` and `save_config()` methods for persistent storage.
- Use `updateConfig()` for dynamic updates to the widget's appearance and behavior.

## 5. Styling Your Widget
- Implement the `updateStyle` method to apply styles based on the configuration.
- Use Qt stylesheets for complex styling.
- Consider using transparent backgrounds for better desktop integration.

## 6. Making Your Widget Resizable and Draggable
The `DraggableWidget` base class provides basic functionality for resizing and moving. 
- Override `resizeEvent` and `moveEvent` to handle size and position changes.
- Consider implementing a custom move handle (like `MoveHandle`) for easier repositioning.

## 7. Implementing Regular Updates
Use `QTimer` for timed updates, as seen in the System Monitor and Clock widgets.

## 8. Advanced Widget Features
- Implement custom context menus for additional functionality.
- Use Qt's event system for complex interactions.
- Consider adding keyboard shortcuts for power users.

## 9. Best Practices
- Follow PEP 8 style guidelines.
- Use meaningful variable and function names.
- Comment your code, especially for complex logic.
- Handle errors gracefully, especially when loading/saving configurations.
- Optimize for performance, especially if your widget updates frequently.

## 10. Testing Your Widget
- Create unit tests for your widget's core functionality.
- Test your widget in different scenarios (resizing, configuration changes, etc.).
- Use Qt's test framework for GUI testing.

## 11. Adding Your Widget to the Application
1. Create a new Python file in the designated widgets folder.
2. Implement your widget as described in this guide.
3. Ensure the main widget class is aliased as `Widget`.
4. Restart the Imolia Desktop Customizer application.

## 12. Handling Dependencies
- List all dependencies at the top of your widget file in a comment block.
- Use the virtual environment system implemented in the application to manage widget-specific dependencies.
- Implement a method to install dependencies if necessary. For example:

```python
@staticmethod
def install_dependencies():
    try:
        python_executable = sys.executable
        pip_command = [python_executable, "-m", "pip", "install", "PyQt5==5.15.6"]
        result = subprocess.run(pip_command, capture_output=True, text=True, check=True)
        logger.info(f"Pip install output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e}")
        logger.error(f"Pip install error output: {e.stderr}")
        return False
```

## 13. Error Handling and Logging
- Implement comprehensive logging in your widget to facilitate debugging.
- Use Python's `logging` module to create informative log messages.
- Log important events, errors, and state changes in your widget.
- Example of setting up logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Usage
logger.debug("Debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

## 14. Troubleshooting Common Issues
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
- Move handle not working properly:
  - Ensure the `MoveHandle` is correctly positioned and sized.
  - Verify that `resizeEvent` is updating the position of the move handle.

Remember to thoroughly test your widget in various scenarios and with different configurations to ensure stability and performance. Always provide clear error messages and logging to help diagnose issues that may arise during development or use.