import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QSizeGrip, QDialog, QSpinBox, QColorDialog, QPushButton, QHBoxLayout, QComboBox
from PyQt5.QtCore import QTimer, QTime, Qt, QSize
from PyQt5.QtGui import QFont, QResizeEvent, QColor
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

class ClockWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'clock_widget_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {
            'color': 'white',
            'time_format': 'hh:mm:ss',
            'size': (250, 100)
        }

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'clock_widget_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        layout = QVBoxLayout()
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        self.setLayout(layout)

        self.setMinimumSize(110, 50)
        size = self.config.get('size', (250, 100))
        self.resize(*size)

        size_grip = QSizeGrip(self)
        layout.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

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
        self.time_label.setStyleSheet(f"color: {color};")
        self.adjustFontSize()

    def adjustFontSize(self):
        font = self.time_label.font()
        font.setPixelSize(int(self.height() * 0.5))  # 50% van de hoogte
        self.time_label.setFont(font)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.adjustFontSize()
        self.config['size'] = (self.width(), self.height())
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

    def initUI(self):
        super().initUI()
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Time format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['hh:mm', 'hh:mm:ss', 'hh:mm:ss ap'])
        self.format_combo.setCurrentText(self.widget.config.get('time_format', 'hh:mm:ss'))
        format_layout.addWidget(self.format_combo)
        self.layout().insertLayout(2, format_layout)

    def get_config(self):
        return {
            'color': self.color_button.palette().button().color().name(),
            'time_format': self.format_combo.currentText()
        }

# Zorg ervoor dat de Widget klasse is gedefinieerd voor de loader
Widget = ClockWidget