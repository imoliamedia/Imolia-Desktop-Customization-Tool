"""
CalculatorWidget

Dependencies:
PyQt5==5.15.6
"""

import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QGridLayout, QPushButton, QLineEdit, QColorDialog, QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QPainter, QPolygon
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

class CalculatorWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()
        self.move_handle = MoveHandle(self)
        self.move_handle.move(0, self.height() - 20)

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'calculator_widget_config.json')
        default_config = {
            'background_color': '#2C3E50',
            'text_color': '#ECF0F1',
            'button_color': '#34495E',
            'size': (300, 400),
            'position': (100, 100),
        }
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        return default_config

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'calculator_widget_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        layout = QVBoxLayout()
        
        self.display = QLineEdit()
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        layout.addWidget(self.display)

        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]

        grid_layout = QGridLayout()

        positions = [(i, j) for i in range(4) for j in range(4)]
        for position, button in zip(positions, buttons):
            btn = QPushButton(button)
            btn.clicked.connect(self.on_button_click)
            grid_layout.addWidget(btn, *position)

        layout.addLayout(grid_layout)
        
        self.setLayout(layout)
        
        self.setMinimumSize(200, 300)
        size = self.config.get('size', (300, 400))
        self.resize(*size)
        
        position = self.config.get('position', (100, 100))
        self.move(*position)

        self.updateStyle()

    def updateStyle(self):
        bg_color = self.config.get('background_color', '#2C3E50')
        text_color = self.config.get('text_color', '#ECF0F1')
        button_color = self.config.get('button_color', '#34495E')
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
                font-size: 18px;
            }}
            QPushButton {{
                background-color: {button_color};
                border: none;
                padding: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(button_color)};
            }}
            QLineEdit {{
                border: none;
                padding: 10px;
                font-size: 24px;
            }}
        """)

    def lighten_color(self, color):
        c = QColor(color)
        h, s, l, _ = c.getHsl()
        return QColor.fromHsl(h, s, min(l + 20, 255), 255).name()

    def on_button_click(self):
        button = self.sender()
        current = self.display.text()
        
        if button.text() == '=':
            try:
                result = eval(current)
                self.display.setText(str(result))
            except Exception as e:
                self.display.setText("Error")
                logger.error(f"Calculation error: {e}")
        else:
            self.display.setText(current + button.text())

    def updateConfig(self, new_config):
        self.config.update(new_config)
        self.updateStyle()
        self.save_config()

    def openSettings(self):
        dialog = CalculatorWidgetSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.move_handle.move(0, self.height() - 20)
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

class CalculatorWidgetSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def add_custom_section(self, layout):
        self.add_color_setting(layout, "Background Color", self.widget.config['background_color'], 'background_color')
        self.add_color_setting(layout, "Text Color", self.widget.config['text_color'], 'text_color')
        self.add_color_setting(layout, "Button Color", self.widget.config['button_color'], 'button_color')

    def add_color_setting(self, layout, label, initial_color, config_key):
        color_button = QPushButton(label)
        color_button.setStyleSheet(f"background-color: {initial_color};")
        color_button.clicked.connect(lambda: self.choose_color(color_button, config_key))
        layout.addWidget(color_button)

    def choose_color(self, button, config_key):
        color = QColorDialog.getColor()
        if color.isValid():
            self.widget.config[config_key] = color.name()
            button.setStyleSheet(f"background-color: {color.name()};")

    def get_config(self):
        return self.widget.config

# Important: The class must be named 'Widget' for the loader to recognize it
Widget = CalculatorWidget