"""
Modern Todo Widget for Imolia Desktop Customizer

Dependencies:
PyQt5==5.15.6

"""

import json
import os
from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QSizeGrip, QLineEdit, 
                             QPushButton, QListWidget, QHBoxLayout, QWidget,
                             QListWidgetItem, QColorDialog)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont, QColor
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

class ModernToDoWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'modern_todo_widget_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {
            'bg_color': '#2C3E50',
            'text_color': '#ECF0F1',
            'button_color': '#3498DB',
            'item_bg_color': '#34495E',
            'item_text_color': '#ECF0F1',
            'size': (300, 450),
            'position': (100, 100)
        }

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'modern_todo_widget_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        self.title = QLabel("To Do List")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        # Input field and Add button
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter a new task...")
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_task)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)

        # Task list
        self.task_list = QListWidget()
        self.task_list.setSpacing(2)
        self.task_list.itemDoubleClicked.connect(self.edit_task)
        layout.addWidget(self.task_list)

        # Complete and Remove buttons
        button_layout = QHBoxLayout()
        self.complete_button = QPushButton("Complete")
        self.complete_button.clicked.connect(self.complete_task)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_task)
        button_layout.addWidget(self.complete_button)
        button_layout.addWidget(self.remove_button)
        layout.addLayout(button_layout)

        # Add size grip for resizing
        size_grip = QSizeGrip(self)
        layout.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

        self.setLayout(layout)
        
        # Set minimum size and default size
        self.setMinimumSize(250, 350)
        size = self.config.get('size', (300, 450))
        self.resize(*size)

        # Set position
        position = self.config.get('position', (100, 100))
        self.move(*position)

        self.updateStyle()

    def updateStyle(self):
        bg_color = self.config.get('bg_color', '#2C3E50')
        text_color = self.config.get('text_color', '#ECF0F1')
        button_color = self.config.get('button_color', '#3498DB')
        item_bg_color = self.config.get('item_bg_color', '#34495E')
        item_text_color = self.config.get('item_text_color', '#ECF0F1')

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 10px;
            }}
            QLabel {{
                font-weight: bold;
            }}
            QLineEdit {{
                background-color: {item_bg_color};
                color: {item_text_color};
                border: none;
                padding: 5px;
                border-radius: 5px;
            }}
            QPushButton {{
                background-color: {button_color};
                color: {text_color};
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(button_color)};
            }}
            QListWidget {{
                background-color: {item_bg_color};
                border: none;
                border-radius: 5px;
            }}
            QListWidget::item {{
                background-color: {item_bg_color};
                color: {item_text_color};
                border: none;
                padding: 5px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {self.lighten_color(item_bg_color)};
            }}
        """)
        self.adjustFontSize()

    def lighten_color(self, color, factor=1.3):
        color = QColor(color)
        hsl_hue = color.hslHue()
        hsl_saturation = color.hslSaturation()
        hsl_lightness = min(round(color.lightness() * factor), 255)
        return QColor.fromHsl(hsl_hue, hsl_saturation, hsl_lightness).name()

    def adjustFontSize(self):
        font = QFont()
        font.setPixelSize(int(self.height() * 0.05))  # 5% of height
        font.setBold(True)
        self.title.setFont(font)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustFontSize()
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

    @pyqtSlot()
    def add_task(self):
        task = self.input_field.text()
        if task:
            item = QListWidgetItem(task)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.task_list.addItem(item)
            self.input_field.clear()

    @pyqtSlot(QListWidgetItem)
    def edit_task(self, item):
        self.task_list.editItem(item)

    @pyqtSlot()
    def complete_task(self):
        current_item = self.task_list.currentItem()
        if current_item:
            current_text = current_item.text()
            if not current_text.startswith("✓ "):
                current_item.setText(f"✓ {current_text}")
                current_item.setForeground(QColor(self.config.get('button_color', '#3498DB')))

    @pyqtSlot()
    def remove_task(self):
        current_row = self.task_list.currentRow()
        if current_row >= 0:
            self.task_list.takeItem(current_row)

    def updateConfig(self, new_config):
        self.config.update(new_config)
        self.updateStyle()
        self.save_config()

    def openSettings(self):
        dialog = ModernToDoWidgetSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

class ModernToDoWidgetSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)
        self.widget = widget
        self.init_color_buttons()

    def init_color_buttons(self):
        layout = self.layout()
        self.color_buttons = {}
        for color_name in ['bg_color', 'text_color', 'button_color', 'item_bg_color', 'item_text_color']:
            button = QPushButton(f"Choose {color_name.replace('_', ' ').title()}")
            button.clicked.connect(lambda _, cn=color_name: self.choose_color(cn))
            layout.addWidget(button)
            self.color_buttons[color_name] = button

    def choose_color(self, color_name):
        color = QColorDialog.getColor(QColor(self.widget.config.get(color_name)))
        if color.isValid():
            self.color_buttons[color_name].setStyleSheet(f"background-color: {color.name()};")

    def get_config(self):
        return {
            color_name: button.palette().button().color().name()
            for color_name, button in self.color_buttons.items()
        }

# Important: The class must be named 'Widget' for the loader to recognize it
Widget = ModernToDoWidget