# Comprehensive Widget Development Guide for Imolia Desktop Customization Tool

## Introduction
Welcome to the comprehensive guide for creating custom widgets for the Imolia Desktop Customization Tool. This guide is designed to help developers of all skill levels create powerful, standalone widgets that seamlessly integrate with our desktop customization platform.

## License
All widgets developed for this tool must be compatible with the GNU General Public License v3.0. Please ensure you understand the implications of this license for your code before contributing.

## Table of Contents
1. Widget Basics
<<<<<<< Updated upstream
2. Creating Your First Widget
3. Widget Configuration and Customization
4. Styling Your Widget
5. Widget Settings
6. Making Your Widget Resizable and Draggable
7. Implementing Regular Updates
8. Best Practices
9. Adding Your Widget to the Application
10. Submitting Your Widget for Inclusion
=======
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
12. Specifying Dependencies
13. Troubleshooting Common Issues
14. Submitting Your Widget for Inclusion
>>>>>>> Stashed changes

## 1. Widget Basics
Widgets in our application are Python classes that inherit from `DraggableWidget`. This base class provides essential functionality such as dragging, resizing, and basic configuration management. Understanding the `DraggableWidget` class is crucial for developing effective widgets.

Key concepts:
- Widgets are self-contained modules
- Each widget manages its own configuration and appearance
- Widgets can be resized and moved by the user
- Widgets can have their own settings dialog

## 2. Setting Up Your Development Environment
Before you start developing widgets, ensure you have the following set up:
- Python 3.7 or higher
- PyQt5 installed (`pip install PyQt5`)
- A code editor (we recommend Visual Studio Code with the Python extension)
- Git for version control

Clone the Imolia Desktop Customization Tool repository to get started:
```
git clone https://github.com/ImoliMedia/desktop-customization-tool.git
cd desktop-customization-tool
pip install -r requirements.txt
```

## 3. Creating Your First Widget
Here's a template for a new widget:

```python
"""
MyCustomWidget

Dependencies:
PyQt5==5.15.6

Description:
This widget is a template for creating custom widgets.
"""

import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

class MyCustomWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'my_custom_widget_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {'color': 'white', 'size': (200, 100), 'position': (100, 100)}

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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_widget)
        self.timer.start(1000)  # Update every 1000 ms

    def updateStyle(self):
        color = self.config.get('color', 'white')
        self.label.setStyleSheet(f"color: {color}; background-color: transparent;")
        self.adjustFontSize()

    def adjustFontSize(self):
        font = QFont()
        font.setPixelSize(int(self.height() * 0.2))  # 20% of height
        self.label.setFont(font)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustFontSize()
        self.config['size'] = (self.width(), self.height())
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
- Use a `config` dictionary to store customizable properties of your widget.
<<<<<<< Updated upstream
- Implement `load_config()` and `save_config()` methods to manage persistent storage of your widget's configuration.
- The `updateConfig` method allows for dynamic updates to the widget's appearance and behavior.

## 4. Styling Your Widget
- Implement the `updateStyle` method to apply styles based on the configuration.
- Use transparent backgrounds to blend with the desktop.
- Adjust font sizes dynamically based on widget size.

## 5. Widget Settings
When developing a new widget, use the `WidgetSettingsDialog` as a base for your settings window:

1. Create a new class that inherits from `WidgetSettingsDialog`.
2. Override the `add_custom_section` method to add widget-specific settings.
3. Adjust the `get_config` method to include widget-specific settings.

Example:
=======
- Implement `load_config()` and `save_config()` methods for persistent storage.
- Use `updateConfig()` for dynamic updates to the widget's appearance and behavior.
- Create a custom settings dialog by extending `WidgetSettingsDialog`.
>>>>>>> Stashed changes

Example of adding a custom setting:
```python
def add_custom_section(self, layout):
    custom_group = QGroupBox("Custom Settings")
    custom_layout = QVBoxLayout()
    
    # Add a custom option
    self.custom_option = QCheckBox("Enable feature")
    self.custom_option.setChecked(self.widget.config.get('custom_feature', False))
    custom_layout.addWidget(self.custom_option)
    
    custom_group.setLayout(custom_layout)
    layout.addWidget(custom_group)

<<<<<<< Updated upstream
    def get_config(self):
        config = super().get_config()
        # Add your custom settings to config here
        return config
=======
def get_config(self):
    config = super().get_config()
    config.update({
        'custom_feature': self.custom_option.isChecked()
    })
    return config
```

## 5. Styling Your Widget
- Use Qt stylesheets for complex styling.
- Ensure your widget looks good on different desktop backgrounds.
- Consider using Qt's built-in color roles for consistent theming.

Example of advanced styling:
```python
def updateStyle(self):
    color = self.config.get('color', 'white')
    self.setStyleSheet(f"""
        QLabel {{
            color: {color};
            background-color: rgba(0, 0, 0, 100);
            border-radius: 10px;
            padding: 5px;
        }}
    """)
>>>>>>> Stashed changes
```

## 6. Making Your Widget Resizable and Draggable
The `DraggableWidget` base class provides built-in functionality for resizing and dragging. To customize this behavior:

- Override `mousePressEvent`, `mouseMoveEvent`, and `mouseReleaseEvent` for custom dragging behavior.
- Implement custom resize handles by overriding `paintEvent` and `mousePressEvent`.

Example of custom resize handle:
```python
def paintEvent(self, event):
    super().paintEvent(event)
    painter = QPainter(self)
    painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
    painter.drawRect(self.width() - 20, self.height() - 20, 20, 20)

def mousePressEvent(self, event):
    if event.pos().x() > self.width() - 20 and event.pos().y() > self.height() - 20:
        self.resizing = True
        self.resize_start_pos = event.pos()
    else:
        super().mousePressEvent(event)
```

## 7. Implementing Regular Updates
For widgets that need to update regularly:
- Use `QTimer` for timed updates.
- Consider using `QThread` for heavy computations to keep the UI responsive.

Example of threaded updates:
```python
from PyQt5.QtCore import QThread, pyqtSignal

class UpdateThread(QThread):
    update_signal = pyqtSignal(str)

    def run(self):
        # Perform heavy computation here
        result = self.heavy_computation()
        self.update_signal.emit(result)

class MyWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.update_thread = UpdateThread()
        self.update_thread.update_signal.connect(self.update_display)
        self.update_thread.start()

    def update_display(self, result):
        # Update widget with the result
        pass
```

## 8. Advanced Widget Features
- Implement custom context menus for additional functionality.
- Use Qt's event system for complex interactions.
- Consider adding keyboard shortcuts for power users.

Example of custom context menu:
```python
def contextMenuEvent(self, event):
    context_menu = QMenu(self)
    refresh_action = context_menu.addAction("Refresh")
    action = context_menu.exec_(self.mapToGlobal(event.pos()))
    if action == refresh_action:
        self.refresh_widget()
```

## 9. Best Practices
- Follow PEP 8 style guidelines for Python code.
- Use meaningful variable and function names.
- Comment your code, especially for complex logic.
- Handle errors gracefully, especially when loading/saving configurations.
- Optimize for performance, especially if your widget updates frequently.
- Use Qt's layout system for responsive widget designs.
- Implement a `close()` method to clean up resources when the widget is closed.

<<<<<<< Updated upstream
## 9. Adding Your Widget to the Application
To add your widget to the Desktop Customization Tool:
=======
## 10. Testing Your Widget
- Create unit tests for your widget's core functionality.
- Test your widget in different scenarios (resizing, configuration changes, etc.).
- Use Qt's test framework for GUI testing.

Example of a simple test:
```python
import unittest
from PyQt5.QtWidgets import QApplication
from my_custom_widget import MyCustomWidget
>>>>>>> Stashed changes

class TestMyCustomWidget(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.widget = MyCustomWidget()

    def test_initial_size(self):
        self.assertEqual(self.widget.size(), (200, 100))

    def test_config_update(self):
        self.widget.updateConfig({'color': 'red'})
        self.assertEqual(self.widget.config['color'], 'red')

if __name__ == '__main__':
    unittest.main()
```

## 11. Adding Your Widget to the Application
1. Create a new Python file in `C:\Users\[YourUsername]\Documents\Imolia Desktop Customizer Widgets\`.
2. Implement your widget as described in this guide.
3. Ensure the main widget class is aliased as `Widget`.
4. Restart the Imolia Desktop Customizer application.
5. Your new widget will be available in the widget manager.

## 12. Specifying Dependencies
Include dependencies in a comment at the top of your widget file:
```python
"""
MyAwesomeWidget

Dependencies:
requests==2.25.1
beautifulsoup4==4.9.3

Description:
This widget does something awesome.
"""
```

<<<<<<< Updated upstream
## 10. Submitting Your Widget for Inclusion
If you've developed a widget that you believe would be valuable to other users, you can submit it for inclusion in the main Imolia Desktop Customizer repository:

1. Ensure your widget follows all the guidelines outlined in this document.
2. Fork the Imolia Desktop Customizer repository on GitHub.
3. Add your widget to the `widgets` directory in your forked repository, following the structure outlined in the "Widget Basics" section.
4. Create a pull request with your new widget.
5. In the pull request description, provide a brief overview of your widget's functionality and any dependencies it may have.
6. Our team will review your submission. We may provide feedback or request changes.
7. If approved, your widget will be added to the main repository and will be available to all users in future releases.

Please note that while we appreciate all contributions, we reserve the right to reject or request modifications to submitted widgets to ensure they meet our quality and security standards.

## Note on Configuration Files
Each widget saves its configuration in a separate JSON file in the same directory as the widget. This ensures that each widget remains independent and can manage its own settings without relying on the main application.

## Conclusion
By following this guide, you can create custom, standalone widgets that seamlessly integrate with the Desktop Customization Tool. Remember to focus on functionality, user-friendliness, customizability, and performance in your widget design. Your widgets should be able to operate independently, managing their own configurations and adapting to user preferences. Always ensure your widget code complies with the GPL v3 license.


=======
## 13. Troubleshooting Common Issues
- Widget not appearing: Check if it's properly registered in the widget manager.
- Styling issues: Ensure all style properties are properly set and updated.
- Performance problems: Profile your code and optimize heavy operations.
- Configuration not saving: Verify the `save_config` method is called appropriately.

## 14. Submitting Your Widget for Inclusion
1. Ensure your widget follows all guidelines in this document.
2. Fork the Imolia Desktop Customizer repository on GitHub.
3. Add your widget to the `widgets` directory in your forked repository.
4. Create a pull request with a description of your widget's functionality and any dependencies.
5. Our team will review your submission and may provide feedback.

## Conclusion
By following this comprehensive guide, you can create powerful, customizable widgets for the Imolia Desktop Customization Tool. Remember to focus on user experience, performance, and maintainability in your widget designs. Happy coding!
>>>>>>> Stashed changes
