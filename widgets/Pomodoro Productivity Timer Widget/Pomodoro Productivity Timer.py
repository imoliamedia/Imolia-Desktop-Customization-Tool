"""
Pomodoro Timer Widget for Imolia Desktop Customizer

Dependencies:
PyQt5==5.15.6
"""

import json
import os
import logging
import sys
import subprocess
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QGroupBox
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PomodoroTimer(DraggableWidget):
    timer_update = pyqtSignal(int)

    def __init__(self):
        logger.debug("Initializing PomodoroTimer")
        super().__init__()
        self.config = self.load_config()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.remaining_time = 0
        self.is_work_phase = True
        self.initUI()
        logger.debug("PomodoroTimer initialized successfully")

    @staticmethod
    def install_dependencies():
        logger.info("Installing dependencies for Pomodoro Timer widget")
        try:
            # Gebruik sys.executable om het huidige Python-interpreterpad te krijgen
            python_executable = sys.executable
            pip_command = [python_executable, "-m", "pip", "install", "PyQt5==5.15.6"]
            
            result = subprocess.run(pip_command, capture_output=True, text=True, check=True)
            logger.info(f"Pip install output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error installing dependencies: {e}")
            logger.error(f"Pip install error output: {e.stderr}")
            return False

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'pomodoro_timer_config.json')
        default_config = {
            'work_duration': 25,
            'break_duration': 5,
            'color': '#FF6347',
            'size': (250, 150),
            'position': (100, 100)
        }
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        return default_config

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'pomodoro_timer_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        layout = QVBoxLayout()

        self.timer_label = QLabel("25:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 36px; font-weight: bold;")
        layout.addWidget(self.timer_label)

        self.status_label = QLabel("Ready to start")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_timer)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        
        self.setMinimumSize(200, 100)
        size = self.config.get('size', (250, 150))
        self.resize(*size)
        
        position = self.config.get('position', (100, 100))
        self.move(*position)
        
        self.updateStyle()

    def updateStyle(self):
        color = self.config.get('color', '#FF6347')
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                color: white;
                border-radius: 10px;
            }}
            QPushButton {{
                background-color: white;
                color: {color};
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #f0f0f0;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """)

    def start_timer(self):
        logger.debug("Starting timer")
        if not self.timer.isActive():
            self.is_work_phase = True
            self.remaining_time = self.config['work_duration'] * 60
            self.timer.start(1000)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Work phase")
        self.update_display()

    def stop_timer(self):
        logger.debug("Stopping timer")
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Timer stopped")
        self.update_display()

    def update_timer(self):
        self.remaining_time -= 1
        if self.remaining_time <= 0:
            self.switch_phase()
        self.update_display()

    def switch_phase(self):
        logger.debug("Switching phase")
        if self.is_work_phase:
            self.is_work_phase = False
            self.remaining_time = self.config['break_duration'] * 60
            self.status_label.setText("Break phase")
        else:
            self.is_work_phase = True
            self.remaining_time = self.config['work_duration'] * 60
            self.status_label.setText("Work phase")

    def update_display(self):
        minutes, seconds = divmod(self.remaining_time, 60)
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def updateConfig(self, new_config):
        logger.debug(f"Updating config: {new_config}")
        self.config.update(new_config)
        self.updateStyle()
        self.save_config()

    def openSettings(self):
        logger.debug("Opening settings dialog")
        dialog = PomodoroSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

class PomodoroSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)
        logger.debug("Initializing PomodoroSettingsDialog")

    def add_custom_section(self, layout):
        custom_group = QGroupBox("Pomodoro Settings")
        custom_layout = QVBoxLayout()
        
        work_layout = QHBoxLayout()
        work_layout.addWidget(QLabel("Work duration (minutes):"))
        self.work_spin = QSpinBox()
        self.work_spin.setRange(1, 60)
        self.work_spin.setValue(self.widget.config['work_duration'])
        work_layout.addWidget(self.work_spin)
        custom_layout.addLayout(work_layout)
        
        break_layout = QHBoxLayout()
        break_layout.addWidget(QLabel("Break duration (minutes):"))
        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 30)
        self.break_spin.setValue(self.widget.config['break_duration'])
        break_layout.addWidget(self.break_spin)
        custom_layout.addLayout(break_layout)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)

    def get_config(self):
        config = super().get_config()
        config.update({
            'work_duration': self.work_spin.value(),
            'break_duration': self.break_spin.value()
        })
        logger.debug(f"New config from settings dialog: {config}")
        return config

# Important: The class must be named 'Widget' for the loader to recognize it
Widget = PomodoroTimer

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    if not PomodoroTimer.install_dependencies():
        logger.error("Failed to install dependencies. Exiting.")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())