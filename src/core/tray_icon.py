from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QCoreApplication
from src.gui.settings_window import SettingsWindow
from src.utils.translation import _

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, overlay, settings):
        super().__init__(icon)
        self.overlay = overlay
        self.settings = settings
        self.initUI()
        self.show()

    def initUI(self):
        menu = QMenu()

        toggle_overlay = QAction(_("Toggle Overlay"), self)
        toggle_overlay.triggered.connect(self.toggle_overlay)
        menu.addAction(toggle_overlay)

        toggle_foreground = QAction(_("Toggle Foreground"), self)
        toggle_foreground.triggered.connect(self.overlay.toggle_foreground)
        menu.addAction(toggle_foreground)

        settings_action = QAction(_("Settings"), self)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        exit_action = QAction(_("Exit"), self)
        exit_action.triggered.connect(QCoreApplication.instance().quit)
        menu.addAction(exit_action)

        self.setContextMenu(menu)

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    def open_settings(self):
        settings_window = SettingsWindow(self.settings)
        settings_window.exec_()