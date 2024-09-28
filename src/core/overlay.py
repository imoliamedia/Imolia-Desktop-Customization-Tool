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

from PyQt5.QtWidgets import QWidget, QDesktopWidget
from PyQt5.QtCore import Qt
from pathlib import Path
from src.config import APP_NAME, WIDGETS_FOLDER_NAME
from src.utils.widget_loader import WidgetManager

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.widgets = {}

        user_documents = Path.home() / "Documents"
        default_widget_dir = user_documents / WIDGETS_FOLDER_NAME
        
        default_widget_dir.mkdir(parents=True, exist_ok=True)
        
        widget_dir = str(default_widget_dir)
        self.widget_manager = WidgetManager(widget_dir)

    def initUI(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnBottomHint |
            Qt.Tool
        )

        desktop = QDesktopWidget()
        primary_screen = desktop.screenNumber(desktop.cursor().pos())
        desktop_rect = desktop.screenGeometry(primary_screen)
        self.setGeometry(desktop_rect)

        self.load_active_widgets()

    def load_active_widgets(self):
        available_widgets = self.widget_manager.get_available_widgets()
        for widget_name in available_widgets:
            if widget_name not in self.widgets:
                widget = self.widget_manager.activate_widget(widget_name)
                if widget:
                    self.widgets[widget_name] = widget
                    widget.setParent(self)
                    widget.show()
                    
                    # Gebruik de opgeslagen positie als deze beschikbaar is
                    saved_position = widget.config.get('position')
                    if saved_position:
                        widget.move(*saved_position)
                    else:
                        # Als er geen opgeslagen positie is, gebruik een standaardpositie
                        widget.move(50 * len(self.widgets), 50 * len(self.widgets))

    def resizeEvent(self, event):
        desktop = QDesktopWidget()
        primary_screen = desktop.screenNumber(desktop.cursor().pos())
        self.setGeometry(desktop.screenGeometry(primary_screen))
        super().resizeEvent(event)

    def showEvent(self, event):
        self.lower()
        super().showEvent(event)

    def closeEvent(self, event):
        for widget in self.widgets.values():
            widget.close()
        QWidget.closeEvent(self, event)