# Widget Development Guide for Desktop Customization Tool

## Introduction
This guide provides comprehensive instructions for creating custom, standalone widgets for the Desktop Customization Tool. Widgets are designed to be independent, self-contained modules that manage their own configuration and appearance.

## License
All widgets developed for this tool must be compatible with the GNU General Public License v3.0. Make sure you understand the implications of this license for your code.

## Table of Contents
1. Widget Basics
2. Creating Your First Widget
3. Widget Configuration and Customization
4. Styling Your Widget
5. Making Your Widget Resizable and Draggable
6. Implementing Regular Updates
7. Best Practices
8. Adding Your Widget to the Application

## 1. Widget Basics
Widgets in our application are Python classes that inherit from `DraggableWidget`. This base class provides essential functionality such as dragging, resizing, and basic configuration management.

## 2. Creating Your First Widget
Here's a template for a new widget:

```python
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

    def get_config(self):
        return {
            'color': self.color_button.palette().button().color().name(),
        }

# Important: The class must be named 'Widget' for the loader to recognize it
Widget = MyCustomWidget
```

## 3. Widget Configuration and Customization
- Use a `config` dictionary to store customizable properties of your widget.
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

```python
class MyWidgetSettingsDialog(WidgetSettingsDialog):
    def add_custom_section(self, layout):
        custom_group = QGroupBox("My Widget Settings")
        custom_layout = QVBoxLayout()
        
        # Add your custom settings here
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)

    def get_config(self):
        config = super().get_config()
        # Add your custom settings to config here
        return config

## 6. Making Your Widget Resizable and Draggable
- The `DraggableWidget` base class provides built-in functionality for resizing and dragging.
- Implement `resizeEvent` to handle size changes and save the new size in your widget's configuration.
- The widget's position is automatically saved when dragged.

## 7. Implementing Regular Updates
If your widget needs to update regularly (like a clock or system monitor):
- Use a `QTimer` to trigger updates at set intervals.
- Implement an update method (e.g., `update_widget`) to refresh the widget's content.

## 8. Best Practices
- Keep your widget modular and self-contained.
- Manage all widget-specific settings within the widget itself.
- Use clear, descriptive variable names.
- Comment your code thoroughly, especially for complex logic.
- Handle errors gracefully, especially when loading/saving configurations.
- Optimize for performance, especially if your widget updates frequently.
- Test your widget thoroughly in different scenarios (resizing, configuration changes, etc.).
- Ensure your widget looks good on different desktop backgrounds by using appropriate colors and transparency.

## 9. Adding Your Widget to the Application

To add your widget to the Desktop Customization Tool:

* Create a new Python file for your widget in the user's Documents folder, under the "Imolia Desktop Customizer Widgets" directory. 
  - The exact path will be: `C:\Users\[YourUsername]\Documents\Imolia Desktop Customizer Widgets\`
  - For example, if your widget is called "MyAwesomeWidget", you might name the file `my_awesome_widget.py`

* In your widget file, ensure your main widget class is aliased as `Widget` at the end of the file:

  ```python
  class MyAwesomeWidget(DraggableWidget):
      # Your widget implementation here
      ...

  Widget = MyAwesomeWidget
  ```

* Test your widget thoroughly in various scenarios.

* If your widget requires additional Python packages, include this information in a comment at the top of your widget file:

  ```python
  """
  MyAwesomeWidget
  
  Dependencies:
  - requests==2.25.1
  - beautifulsoup4==4.9.3
  
  Please ensure these packages are installed before using this widget.
  """
  ```

Widgets placed in this folder will be automatically detected and made available in the application's widget manager.

## Submitting Your Widget for Inclusion

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