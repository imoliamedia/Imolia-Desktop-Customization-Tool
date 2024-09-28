# Copyright (C) 2024 Imolia Media
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QPushButton, QTabWidget, 
                             QWidget, QListWidget, QListWidgetItem, QStyle, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from pathlib import Path
from src.config import APP_NAME, WIDGETS_FOLDER_NAME

class SettingsWindow(QDialog):
    def __init__(self, settings, overlay):
        super().__init__()
        self.settings = settings
        self.overlay = overlay
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{APP_NAME} - Settings")
        self.setGeometry(300, 300, 500, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.main_layout = QVBoxLayout()
        
        self.setup_header()
        self.setup_tabs()
        self.setup_buttons()

        self.setLayout(self.main_layout)
        self.apply_styles()

    def setup_header(self):
        header_layout = QHBoxLayout()
        self.logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icons", "tray_icon.png")
        try:
            logo_pixmap = QPixmap(logo_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(logo_pixmap)
        except:
            print(f"Could not load logo from {logo_path}")
        header_layout.addWidget(self.logo_label)
        self.title_label = QLabel(APP_NAME)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.main_layout.addWidget(line)

    def setup_tabs(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.createWidgetManagerTab(), "Widgets")
        self.main_layout.addWidget(self.tab_widget)

    def setup_buttons(self):
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("background-color: #f44336; color: white; padding: 5px 15px;")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(button_layout)

    def createWidgetManagerTab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        widget_dir = Path.home() / "Documents" / WIDGETS_FOLDER_NAME
        self.info_label = QLabel(f"Widgets can be added in:\n{widget_dir}")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.open_folder_button = QPushButton("Open Widgets Folder")
        self.open_folder_button.clicked.connect(lambda: os.startfile(str(widget_dir)))
        layout.addWidget(self.open_folder_button)

        self.widget_list = QListWidget()
        self.populate_widget_list()
        layout.addWidget(self.widget_list)

        tab.setLayout(layout)
        return tab

    def populate_widget_list(self):
        self.widget_list.clear()
        available_widgets = self.overlay.widget_manager.get_available_widgets()
        active_widgets = self.settings.get('active_widgets', [])

        for widget_name in available_widgets:
            item = QListWidgetItem()
            item_widget = QWidget()
            item_layout = QHBoxLayout()

            checkbox = QCheckBox()
            checkbox.setChecked(widget_name in active_widgets)
            item_layout.addWidget(checkbox)

            label = QLabel(self.get_widget_display_name(widget_name))
            item_layout.addWidget(label)

            settings_button = QPushButton()
            settings_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
            settings_button.clicked.connect(lambda _, wn=widget_name: self.open_widget_settings(wn))
            item_layout.addWidget(settings_button)

            item_widget.setLayout(item_layout)
            item.setSizeHint(item_widget.sizeHint())

            self.widget_list.addItem(item)
            self.widget_list.setItemWidget(item, item_widget)

    def get_widget_display_name(self, widget_name):
        display_names = {
            'clock_widget': 'Clock',
            'system_monitor_widget': 'System Monitor',
            'todo_widget': 'To-Do List'
        }
        return display_names.get(widget_name, widget_name.replace('_', ' ').title())

    def open_widget_settings(self, widget_name):
        if widget_name in self.overlay.widgets:
            self.overlay.widgets[widget_name].openSettings()

    def save_settings(self):
        active_widgets = []
        for i in range(self.widget_list.count()):
            item = self.widget_list.item(i)
            checkbox = self.widget_list.itemWidget(item).layout().itemAt(0).widget()
            if checkbox.isChecked():
                widget_name = self.overlay.widget_manager.get_available_widgets()[i]
                active_widgets.append(widget_name)

        self.settings.set('active_widgets', active_widgets)

        self.overlay.load_active_widgets()

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
            QLabel, QCheckBox {
                font-size: 14px;
            }
            QPushButton {
                padding: 5px;
                font-size: 14px;
            }
        """)