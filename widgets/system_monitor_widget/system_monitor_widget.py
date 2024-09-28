import json
import os
import psutil
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QSizeGrip, QSpinBox, QColorDialog, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt, QSize, QElapsedTimer
from PyQt5.QtGui import QFont, QResizeEvent, QColor
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

class SystemMonitorWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()
        self.last_net_io = psutil.net_io_counters()
        self.last_net_io_time = QElapsedTimer()
        self.last_net_io_time.start()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'system_monitor_widget_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {
            'color': 'white',
            'update_interval': 1000,
            'size': (250, 150)
        }

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'system_monitor_widget_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        layout = QVBoxLayout()
        self.cpu_label = QLabel("CPU: 0%")
        self.memory_label = QLabel("Memory: 0%")
        self.disk_label = QLabel("Disk: 0%")
        self.network_label = QLabel("Network: 0 Mbps")
        
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.memory_label)
        layout.addWidget(self.disk_label)
        layout.addWidget(self.network_label)
        
        self.setLayout(layout)

        self.setMinimumSize(200, 100)
        size = self.config.get('size', (250, 150))
        self.resize(*size)

        size_grip = QSizeGrip(self)
        layout.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

        self.updateStyle()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        update_interval = self.config.get('update_interval', 1000)
        self.timer.start(update_interval)

    def update_stats(self):
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        net_io = psutil.net_io_counters()
        net_speed = self.calculate_network_speed(net_io)

        self.cpu_label.setText(f"CPU: {cpu_percent}%")
        self.memory_label.setText(f"Memory: {memory_percent}%")
        self.disk_label.setText(f"Disk: {disk_percent}%")
        self.network_label.setText(f"Network: {net_speed:.2f} Mbps")

    def calculate_network_speed(self, net_io):
        time_elapsed = self.last_net_io_time.elapsed() / 1000.0  # Convert to seconds
        received = (net_io.bytes_recv - self.last_net_io.bytes_recv) * 8 / 1000000  # Convert to Mbits
        sent = (net_io.bytes_sent - self.last_net_io.bytes_sent) * 8 / 1000000  # Convert to Mbits
        
        self.last_net_io = net_io
        self.last_net_io_time.restart()
        
        return (received + sent) / time_elapsed if time_elapsed > 0 else 0

    def updateStyle(self):
        color = self.config.get('color', 'white')
        for label in [self.cpu_label, self.memory_label, self.disk_label, self.network_label]:
            label.setStyleSheet(f"color: {color};")
        self.adjustFontSize()

    def adjustFontSize(self):
        font = QFont()
        font.setPixelSize(int(self.height() * 0.15))  # 15% van de hoogte
        for label in [self.cpu_label, self.memory_label, self.disk_label, self.network_label]:
            label.setFont(font)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.adjustFontSize()
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def updateConfig(self, new_config):
        self.config.update(new_config)
        self.updateStyle()
        if 'update_interval' in new_config:
            self.timer.setInterval(new_config['update_interval'])
        self.save_config()

    def openSettings(self):
        dialog = SystemMonitorSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

class SystemMonitorSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def initUI(self):
        super().initUI()
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Update interval (ms):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 10000)
        self.interval_spin.setSingleStep(100)
        self.interval_spin.setValue(self.widget.config.get('update_interval', 1000))
        interval_layout.addWidget(self.interval_spin)
        self.layout().insertLayout(2, interval_layout)

    def get_config(self):
        return {
            'color': self.color_button.palette().button().color().name(),
            'update_interval': self.interval_spin.value()
        }

# Zorg ervoor dat de Widget klasse is gedefinieerd voor de loader
Widget = SystemMonitorWidget