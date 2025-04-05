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

import logging
import os
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QMessageBox
from PyQt5.QtCore import Qt
from pathlib import Path
from src.config import APP_NAME, WIDGETS_FOLDER_NAME
from src.utils.widget_loader import WidgetManager

logger = logging.getLogger('DesktopCustomizer.Overlay')

class Overlay(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
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
        """Laad actieve widgets."""
        active_widgets = self.settings.get('active_widgets', [])
        available_widgets = self.widget_manager.get_available_widgets()
        
        logger.info(f"Actieve widgets laden: {active_widgets}")
        logger.info(f"Beschikbare widgets: {available_widgets}")
        
        # Verwijder inactieve widgets
        for widget_name in list(self.widgets.keys()):
            if widget_name not in active_widgets:
                logger.info(f"Widget {widget_name} deactiveren")
                self.widget_manager.deactivate_widget(widget_name)
                del self.widgets[widget_name]
        
        # Laad actieve widgets
        for widget_name in active_widgets:
            if widget_name in available_widgets and widget_name not in self.widgets:
                logger.info(f"Widget {widget_name} activeren")
                try:
                    widget = self.widget_manager.activate_widget(widget_name)
                    if widget:
                        self.widgets[widget_name] = widget
                        widget.setParent(self)
                        widget.show()
                        
                        # Positie uit configuratie laden of standaard zetten
                        if hasattr(widget, 'config') and 'position' in widget.config:
                            saved_position = widget.config['position']
                            widget.move(*saved_position)
                        else:
                            # Standaard positie
                            widget.move(50 * len(self.widgets), 50 * len(self.widgets))
                    else:
                        logger.error(f"Widget {widget_name} kon niet worden geactiveerd")
                        self.show_widget_error(widget_name)
                except Exception as e:
                    logger.exception(f"Fout bij activeren van widget {widget_name}")
                    self.show_widget_error(widget_name, str(e))

    def show_widget_error(self, widget_name, error_message=None):
        """Toon een foutmelding bij het laden van een widget."""
        error_text = f"De widget '{widget_name}' kon niet worden geladen."
        if error_message:
            error_text += f"\n\nFoutmelding: {error_message}"
        
        logger.error(error_text)
        
        QMessageBox.warning(
            self, 
            f"{APP_NAME} - Widget Fout",
            error_text
        )

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