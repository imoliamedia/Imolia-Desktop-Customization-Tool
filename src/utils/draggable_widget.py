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

import functools
import logging

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QDialog, QLabel, QSpinBox, QColorDialog,
                             QPushButton, QHBoxLayout, QGroupBox)
from PyQt5.QtCore import Qt, QPoint, QThread, QTimer
from PyQt5.QtGui import QColor, QPainter, QBrush

logger = logging.getLogger('DesktopCustomizer.DraggableWidget')

# Zo lang moet het stil zijn voordat een gewijzigde configuratie echt naar schijf gaat.
SAVE_DELAY_MS = 400


def _debounced(original):
    """Maak van de save_config() van een widget een versie die schrijfacties bundelt.

    Tijdens slepen of schalen komt er per muisbeweging een save_config()-aanroep
    binnen, vaak zelfs meerdere (de basisklasse én de widget zelf). Zonder bundelen
    betekende dat tientallen keer per seconde het configbestand herschrijven. Nu
    wordt pas SAVE_DELAY_MS na de laatste aanroep geschreven, en altijd nog bij
    sluiten van de widget en bij afsluiten van de app (zie flush_config()).
    """
    @functools.wraps(original)
    def save_config(self, *args, **kwargs):
        self._request_save(original, args, kwargs)

    save_config._is_debounced = True
    return save_config


class DraggableWidget(QWidget):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        own = cls.__dict__.get('save_config')
        if own is not None and not getattr(own, '_is_debounced', False):
            cls.save_config = _debounced(own)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.dragging = False
        self.resizing = False
        self.offset = QPoint()
        self.resize_handle_size = 10  # Kleinere resize handle
        self.setMouseTracking(True)
        self.config = self.load_config()

    def load_config(self):
        # Deze methode moet worden overschreven door kindklassen
        return {}

    def save_config(self):
        # Deze methode moet worden overschreven door kindklassen
        pass

    def _request_save(self, original, args, kwargs):
        # Alleen op de UI-thread bundelen; een QTimer starten vanuit een andere
        # thread werkt niet, dus dan gewoon direct schrijven.
        if QThread.currentThread() != self.thread():
            original(self, *args, **kwargs)
            return
        self._pending_save = (original, args, kwargs)
        timer = getattr(self, '_save_timer', None)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(self.flush_config)
            self._save_timer = timer
            app = QApplication.instance()
            if app is not None:
                app.aboutToQuit.connect(self.flush_config)
        timer.start(SAVE_DELAY_MS)

    def flush_config(self):
        """Schrijf een nog openstaande (uitgestelde) configuratiewijziging meteen weg."""
        pending = getattr(self, '_pending_save', None)
        self._pending_save = None
        timer = getattr(self, '_save_timer', None)
        if timer is not None:
            timer.stop()
        if pending:
            original, args, kwargs = pending
            try:
                original(self, *args, **kwargs)
            except Exception:
                logger.exception("Configuratie opslaan mislukt")

    def closeEvent(self, event):
        self.flush_config()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.isInResizeArea(event.pos()):
                self.resizing = True
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.dragging = True
                self.setCursor(Qt.ClosedHandCursor)
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.resizing:
            global_pos = event.globalPos()
            top_left = self.mapToGlobal(QPoint(0, 0))
            new_size = global_pos - top_left
            self.resize(max(new_size.x(), self.minimumWidth()), 
                        max(new_size.y(), self.minimumHeight()))
            event.accept()
        elif self.dragging:
            new_pos = self.mapToParent(event.pos() - self.offset)
            self.move(new_pos)
            self.config['position'] = (new_pos.x(), new_pos.y())
            self.save_config()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.setCursor(Qt.ArrowCursor)
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def enterEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)

    def isInResizeArea(self, pos):
        return (self.width() - self.resize_handle_size <= pos.x() <= self.width() and
                self.height() - self.resize_handle_size <= pos.y() <= self.height())

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        
        # Teken alleen de resize handle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(200, 200, 200, 128)))  # Semi-transparante grijze kleur
        painter.drawRect(self.width() - self.resize_handle_size, 
                         self.height() - self.resize_handle_size,
                         self.resize_handle_size,
                         self.resize_handle_size)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def updateConfig(self, new_config):
        self.config.update(new_config)
        self.save_config()
        if 'color' in new_config:
            self.update()

    def openSettings(self):
        dialog = WidgetSettingsDialog(self)
        if dialog.exec_():
            self.updateConfig(dialog.get_config())

class WidgetSettingsDialog(QDialog):
    def __init__(self, widget, parent=None):
        super().__init__(parent)
        self.widget = widget
        self.setWindowTitle(f"{self.widget.__class__.__name__} Settings")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        self.add_behavior_section(layout)
        self.add_custom_section(layout)
        
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def add_behavior_section(self, layout):
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        update_layout = QHBoxLayout()
        update_layout.addWidget(QLabel("Update interval (seconds):"))
        self.update_interval = QSpinBox()
        self.update_interval.setRange(1, 3600)
        self.update_interval.setValue(self.widget.config.get('update_interval', 60))
        update_layout.addWidget(self.update_interval)
        behavior_layout.addLayout(update_layout)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

    def add_custom_section(self, layout):
        # Deze methode kan door specifieke widgets worden overschreven
        pass

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_button.setStyleSheet(f"background-color: {color.name()};")

    def save_settings(self):
        new_config = self.get_config()
        self.widget.updateConfig(new_config)
        self.accept()

    def get_config(self):
        return {
            'color': self.color_button.palette().button().color().name(),
            'update_interval': self.update_interval.value()
        }