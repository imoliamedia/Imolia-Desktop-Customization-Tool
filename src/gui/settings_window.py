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
import sys
import winreg
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QComboBox, QPushButton, QTabWidget, 
                             QWidget, QListWidget, QListWidgetItem, QStyle, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from pathlib import Path
from src.config import APP_NAME, WIDGETS_FOLDER_NAME
from src.utils.translation import _, update_language

class SettingsWindow(QDialog):
    def __init__(self, settings, overlay):
        super().__init__()
        self.settings = settings
        self.overlay = overlay
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{APP_NAME} - " + _("Settings"))
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
        self.tab_widget.addTab(self.createWidgetManagerTab(), _("Widgets"))
        self.tab_widget.addTab(self.createGeneralTab(), _("General"))
        self.main_layout.addWidget(self.tab_widget)

    def setup_buttons(self):
        button_layout = QHBoxLayout()
        self.save_button = QPushButton(_("Save"))
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton(_("Cancel"))
        self.cancel_button.setStyleSheet("background-color: #f44336; color: white; padding: 5px 15px;")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(button_layout)

    def createGeneralTab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(_("Language:"))
        lang_layout.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['English', 'Nederlands'])
        current_lang = self.settings.get('language', 'en')
        self.lang_combo.setCurrentText('English' if current_lang == 'en' else 'Nederlands')
        self.lang_combo.currentTextChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        self.start_with_windows = QCheckBox(_("Start with Windows"))
        self.start_with_windows.setChecked(self.is_start_with_windows())
        layout.addWidget(self.start_with_windows)

        tab.setLayout(layout)
        return tab

    def createWidgetManagerTab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        widget_dir = Path.home() / "Documents" / WIDGETS_FOLDER_NAME
        self.info_label = QLabel(_("Widgets can be added in:") + f"\n{widget_dir}")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.open_folder_button = QPushButton(_("Open Widgets Folder"))
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
            'clock_widget': _('Clock'),
            'system_monitor_widget': _('System Monitor'),
            'todo_widget': _('To-Do List')
        }
        return display_names.get(widget_name, widget_name.replace('_', ' ').title())

    def open_widget_settings(self, widget_name):
        if widget_name in self.overlay.widgets:
            self.overlay.widgets[widget_name].openSettings()

    def on_language_changed(self, language):
        new_lang = 'en' if language == 'English' else 'nl'
        update_language(new_lang)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(f"{APP_NAME} - " + _("Settings"))
        self.tab_widget.setTabText(0, _("Widgets"))
        self.tab_widget.setTabText(1, _("General"))
        self.lang_label.setText(_("Language:"))
        self.start_with_windows.setText(_("Start with Windows"))
        self.info_label.setText(_("Widgets can be added in:") + f"\n{self.info_label.text().split(':')[1]}")
        self.open_folder_button.setText(_("Open Widgets Folder"))
        self.save_button.setText(_("Save"))
        self.cancel_button.setText(_("Cancel"))
        self.populate_widget_list()

    def is_start_with_windows(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def set_start_with_windows(self, enable):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        if enable:
            app_path = sys.executable
            if app_path.endswith('python.exe'):  # Running from script
                app_path = os.path.abspath(sys.argv[0])
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{app_path}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except WindowsError:
                pass
        winreg.CloseKey(key)

    def save_settings(self):
        new_language = 'en' if self.lang_combo.currentText() == 'English' else 'nl'
        if new_language != self.settings.get('language'):
            self.settings.set('language', new_language)
            update_language(new_language)
        
        start_with_windows = self.start_with_windows.isChecked()
        try:
            self.set_start_with_windows(start_with_windows)
            self.settings.set('start_with_windows', start_with_windows)
        except Exception as e:
            print(f"Error setting 'Start with Windows': {e}")

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
            QComboBox, QPushButton {
                padding: 5px;
                font-size: 14px;
            }
        """)