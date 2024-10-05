"""
Clock Widget for Imolia Desktop Customizer

Dependencies:
PyQt5==5.15.6

"""

import json
import os
from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QDialog, QSpinBox, QColorDialog, 
                             QPushButton, QHBoxLayout, QComboBox, QGroupBox, QFontComboBox)
from PyQt5.QtCore import QTimer, QTime, Qt, QSize, QPoint
from PyQt5.QtGui import QFont, QResizeEvent, QColor, QPainter, QPen
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

class ClockWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.resize_handle_size = 10
        self.initUI()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'clock_widget_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {
            'color': 'white',
            'time_format': 'hh:mm:ss',
            'size': (250, 100),
            'position': (100, 100),
            'font_family': 'Arial',
            'font_style': 'Normal'
        }

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'clock_widget_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        self.setLayout(layout)

        self.setMinimumSize(110, 50)
        size = self.config.get('size', (250, 100))
        self.resize(*size)
        position = self.config.get('position', (100, 100))
        self.move(*position)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.updateStyle()
        
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        
        self.update_time()

    def update_time(self):
        current_time = QTime.currentTime()
        time_format = self.config.get('time_format', 'hh:mm:ss')
        time_text = current_time.toString(time_format)
        self.time_label.setText(time_text)

    def updateStyle(self):
        color = self.config.get('color', 'white')
        self.time_label.setStyleSheet(f"color: {color}; background-color: transparent;")
        self.adjustFont()

    def adjustFont(self):
        font = QFont(self.config.get('font_family', 'Arial'))
        font.setPixelSize(int(self.height() * 0.7))
        font_style = self.config.get('font_style', 'Normal')
        if font_style == 'Bold':
            font.setBold(True)
        elif font_style == 'Italic':
            font.setItalic(True)
        elif font_style == 'Bold Italic':
            font.setBold(True)
            font.setItalic(True)
        self.time_label.setFont(font)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Teken alleen de resize handle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(200, 200, 200, 128))
        painter.drawRect(self.width() - self.resize_handle_size, 
                         self.height() - self.resize_handle_size,
                         self.resize_handle_size,
                         self.resize_handle_size)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustFont()
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

    def updateConfig(self, new_config):
        self.config.update(new_config)
        self.updateStyle()
        self.update_time()
        self.save_config()

    def openSettings(self):
        dialog = ClockSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

class ClockSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def add_custom_section(self, layout):
        custom_group = QGroupBox("Clock Settings")
        custom_layout = QVBoxLayout()
        
        # Time format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Time format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['hh:mm', 'hh:mm:ss', 'hh:mm:ss ap'])
        self.format_combo.setCurrentText(self.widget.config.get('time_format', 'hh:mm:ss'))
        format_layout.addWidget(self.format_combo)
        custom_layout.addLayout(format_layout)
        
        # Font family
        font_family_layout = QHBoxLayout()
        font_family_layout.addWidget(QLabel("Font family:"))
        self.font_family_combo = QFontComboBox()
        self.font_family_combo.setCurrentFont(QFont(self.widget.config.get('font_family', 'Arial')))
        font_family_layout.addWidget(self.font_family_combo)
        custom_layout.addLayout(font_family_layout)

        # Font style
        font_style_layout = QHBoxLayout()
        font_style_layout.addWidget(QLabel("Font style:"))
        self.font_style_combo = QComboBox()
        self.font_style_combo.addItems(['Normal', 'Bold', 'Italic', 'Bold Italic'])
        self.font_style_combo.setCurrentText(self.widget.config.get('font_style', 'Normal'))
        font_style_layout.addWidget(self.font_style_combo)
        custom_layout.addLayout(font_style_layout)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)

    def get_config(self):
        config = super().get_config()
        config.update({
            'time_format': self.format_combo.currentText(),
            'font_family': self.font_family_combo.currentFont().family(),
            'font_style': self.font_style_combo.currentText()
        })
        return config

# Important: The Widget class must be named 'Widget' for the loader to recognize it
Widget = ClockWidget

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())