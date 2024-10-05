from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QWidget, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import os

class BaseWidgetSettingsDialog(QDialog):
    def __init__(self, parent=None, widget_name="Widget"):
        super().__init__(parent)
        self.widget_name = widget_name
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{self.widget_name} Settings")
        self.setGeometry(300, 300, 400, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Set icon (assuming you have an icon file)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icons", "tray_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        main_layout = QVBoxLayout(self)

        # Header
        header_layout = QVBoxLayout()
        self.title_label = QLabel(f"{self.widget_name} Settings")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        header_layout.addWidget(line)

        main_layout.addLayout(header_layout)

        # Content area
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_settings_tab(), "Settings")
        main_layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color: #f44336; color: white; padding: 5px 15px;")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.apply_styles()

    def create_settings_tab(self):
        # This method should be overridden by subclasses to add specific settings
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Override this method to add widget-specific settings"))
        return tab

    def save_settings(self):
        # This method should be overridden by subclasses to save specific settings
        self.accept()

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 12px;
            }
            QTabBar::tab:selected {
                background-color: white;
            }
            QLabel {
                font-size: 14px;
            }
            QPushButton {
                padding: 5px;
                font-size: 14px;
            }
        """)