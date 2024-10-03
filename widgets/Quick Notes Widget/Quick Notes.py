"""
Quick Notes Widget for Imolia Desktop Customizer

Dependencies:
PyQt5==5.15.6

"""

import json
import os
import logging
from PyQt5.QtWidgets import QVBoxLayout, QApplication, QTextEdit, QPushButton, QColorDialog, QFontDialog, QFormLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize
from PyQt5.QtGui import QFont, QPainter, QColor, QPen
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class QuickNotesWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.drag_position = None
        self.resizing = False
        self.resize_handle_size = 10
        self.initUI()
        logger.debug("QuickNotesWidget initialized")

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'quick_notes_widget_config.json')
        default_config = {
            'color': '#000000',
            'bg_color': '#FFFFA5',
            'border_color': '#000000',
            'font_family': 'Arial',
            'font_size': 12,
            'size': (250, 300),
            'position': (100, 100),
            'content': ''
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except json.JSONDecodeError:
                logger.error("Error loading config file. Using default config.")
        return default_config

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'quick_notes_widget_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f)
            logger.debug("Config saved successfully")
        except IOError:
            logger.error("Error saving config file")

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins for the border

        self.notes_edit = QTextEdit(self)
        self.notes_edit.setPlainText(self.config['content'])
        self.notes_edit.textChanged.connect(self.save_notes)
        layout.addWidget(self.notes_edit)

        self.setMinimumSize(100, 100)
        size = self.config.get('size', (250, 300))
        self.resize(*size)
        position = self.config.get('position', (100, 100))
        self.move(*position)

        self.updateStyle()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.save_notes)
        self.timer.start(30000)  # Auto-save every 30 seconds
        
        logger.debug("QuickNotesWidget UI initialized")

    def updateStyle(self):
        try:
            color = self.config.get('color', '#000000')
            bg_color = self.config.get('bg_color', '#FFFFA5')
            self.setStyleSheet(f"""
                QTextEdit {{
                    color: {color};
                    background-color: {bg_color};
                    border: none;
                }}
            """)
            self.adjustFont()
            logger.debug("Style updated")
        except Exception as e:
            logger.error(f"Error updating style: {e}")

    def adjustFont(self):
        font = QFont(self.config.get('font_family', 'Arial'))
        font.setPixelSize(int(self.config.get('font_size', 12)))
        self.notes_edit.setFont(font)

    def save_notes(self):
        try:
            self.config['content'] = self.notes_edit.toPlainText()
            self.save_config()
            logger.debug("Notes saved")
        except Exception as e:
            logger.error(f"Error saving notes: {e}")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(QColor(self.config['border_color']), 1, Qt.SolidLine))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Draw resize handle
        painter.setBrush(QColor(200, 200, 200))
        painter.drawRect(self.width() - self.resize_handle_size, self.height() - self.resize_handle_size,
                         self.resize_handle_size, self.resize_handle_size)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.isInResizeArea(event.pos()):
                self.resizing = True
            else:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.resizing:
                new_size = event.pos()
                self.resize(new_size.x(), new_size.y())
                self.config['size'] = (self.width(), self.height())
                self.save_config()
            elif self.drag_position:
                self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.drag_position = None
        self.config['position'] = (self.x(), self.y())
        self.save_config()

    def isInResizeArea(self, pos):
        return (self.width() - self.resize_handle_size <= pos.x() <= self.width() and
                self.height() - self.resize_handle_size <= pos.y() <= self.height())

    def updateConfig(self, new_config):
        try:
            self.config.update(new_config)
            self.updateStyle()
            self.save_config()
            logger.debug("Config updated")
        except Exception as e:
            logger.error(f"Error updating config: {e}")

    def openSettings(self):
        logger.debug("Opening settings dialog")
        dialog = QuickNotesSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

class QuickNotesSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def add_custom_section(self, layout):
        form_layout = QFormLayout()
        self.add_color_button(form_layout, "Text Color", 'color')
        self.add_color_button(form_layout, "Background Color", 'bg_color')
        self.add_color_button(form_layout, "Border Color", 'border_color')
        self.add_font_button(form_layout)
        layout.addLayout(form_layout)

    def add_color_button(self, layout, label, config_key):
        button = QPushButton(f"Choose {label}")
        button.clicked.connect(lambda: self.choose_color(config_key))
        layout.addRow(label, button)

    def choose_color(self, config_key):
        current_color = self.widget.config.get(config_key, '#000000')
        color = QColorDialog.getColor(QColor(current_color))
        if color.isValid():
            self.widget.config[config_key] = color.name()
        logger.debug(f"Color chosen for {config_key}: {self.widget.config[config_key]}")

    def add_font_button(self, layout):
        button = QPushButton("Choose Font")
        button.clicked.connect(self.choose_font)
        layout.addRow("Font", button)

    def choose_font(self):
        current_font = QFont(self.widget.config['font_family'], self.widget.config['font_size'])
        font, ok = QFontDialog.getFont(current_font)
        if ok:
            self.widget.config['font_family'] = font.family()
            self.widget.config['font_size'] = font.pointSize()
        logger.debug(f"Font chosen: {self.widget.config['font_family']}, {self.widget.config['font_size']}")

    def get_config(self):
        return self.widget.config

# Important: The class must be named 'Widget' for the loader to recognize it
Widget = QuickNotesWidget

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = QuickNotesWidget()
    widget.show()
    sys.exit(app.exec_())