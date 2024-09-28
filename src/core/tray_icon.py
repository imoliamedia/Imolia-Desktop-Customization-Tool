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

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QCoreApplication
from src.gui.settings_window import SettingsWindow
from src.config import APP_NAME
from src.utils.translation import _

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, overlay, settings):
        super().__init__(icon)
        self.setToolTip(APP_NAME)
        self.overlay = overlay
        self.settings = settings
        self.initUI()
        self.show()
        self.activated.connect(self.on_tray_icon_activated)

    def initUI(self):
        menu = QMenu()

        toggle_overlay = QAction(_("Toggle Overlay"), self)
        toggle_overlay.triggered.connect(self.toggle_overlay)
        menu.addAction(toggle_overlay)

        settings_action = QAction(_("Settings"), self)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        exit_action = QAction(_("Exit"), self)
        exit_action.triggered.connect(QCoreApplication.instance().quit)
        menu.addAction(exit_action)

        self.setContextMenu(menu)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_overlay()

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    def open_settings(self):
        settings_window = SettingsWindow(self.settings, self.overlay)
        settings_window.exec_()