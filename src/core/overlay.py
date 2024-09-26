from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from src.widgets.clock_widget import ClockWidget

class Overlay(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.initUI()

    def initUI(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnBottomHint |  # Add this flag
            Qt.Tool  # This helps to keep the window out of the taskbar
        )

        layout = QVBoxLayout()
        self.clock_widget = ClockWidget()
        layout.addWidget(self.clock_widget)
        
        self.setLayout(layout)

        # Set initial position and size from settings
        geometry = self.settings.get('overlay_geometry', (100, 100, 300, 200))
        self.setGeometry(*geometry)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = event.globalPos() - self.oldPos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def closeEvent(self, event):
        # Save current position and size to settings
        self.settings.set('overlay_geometry', self.geometry().getRect())
        super().closeEvent(event)

    def showEvent(self, event):
        # Ensure the overlay stays on the bottom when shown
        self.lower()
        super().showEvent(event)

    def toggle_foreground(self):
        if self.windowFlags() & Qt.WindowStaysOnBottomHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnBottomHint)
            self.show()
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnBottomHint)
            self.show()
            self.lower()