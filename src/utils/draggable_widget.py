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

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QDialog, QLabel, QSpinBox, QColorDialog, QPushButton, QHBoxLayout, QGroupBox
from PyQt5.QtCore import Qt, QPoint, QSize, QEvent
from PyQt5.QtGui import QCursor, QColor, QResizeEvent, QPainter, QPen, QBrush

class DraggableWidget(QWidget):
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