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

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QScrollArea, QWidget,
                             QFrame, QApplication, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFont

import logging
import os
import sys

logger = logging.getLogger('DesktopCustomizer.WidgetDialog')

class WidgetInstallationDialog(QDialog):
    """Dialog for displaying widget installation progress and status."""
    
    installation_requested = pyqtSignal(str)  # Signal to request installation of a widget
    
    def __init__(self, widget_manager, parent=None):
        super().__init__(parent)
        self.widget_manager = widget_manager
        self.widgets_in_progress = set()
        self.widgets_completed = set()
        self.widgets_failed = {}  # widget_name -> error_message
        self.initUI()
        self.connectSignals()
        
    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("Widget Installatie")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Try to set dialog icon
        icon_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icons", "tray_icon.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icons", "tray_icon.ico")
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                self.setWindowIcon(QIcon(path))
                break
        
        main_layout = QVBoxLayout(self)
        
        # Header section
        header_layout = QVBoxLayout()
        self.title_label = QLabel("Widget Installatie")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        self.subtitle_label = QLabel("Installeren van benodigde pakketten voor de widget")
        header_layout.addWidget(self.subtitle_label)
        
        header_line = QFrame()
        header_line.setFrameShape(QFrame.HLine)
        header_line.setFrameShadow(QFrame.Sunken)
        header_layout.addWidget(header_line)
        
        main_layout.addLayout(header_layout)
        
        # Status list area
        self.status_list = QListWidget()
        self.status_list.setAlternatingRowColors(True)
        main_layout.addWidget(self.status_list)
        
        # Current operation section
        current_operation_layout = QVBoxLayout()
        
        self.current_widget_label = QLabel("Widget: -")
        current_operation_layout.addWidget(self.current_widget_label)
        
        self.current_status_label = QLabel("Status: -")
        current_operation_layout.addWidget(self.current_status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        current_operation_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(current_operation_layout)
        
        # Bottom section with buttons
        button_layout = QHBoxLayout()
        
        self.details_button = QPushButton("Details weergeven")
        self.details_button.setCheckable(True)
        self.details_button.clicked.connect(self.toggle_details)
        button_layout.addWidget(self.details_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Sluiten")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        # Details area (hidden by default)
        self.details_area = QScrollArea()
        self.details_area.setWidgetResizable(True)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_log = QLabel("Log details zullen hier verschijnen...")
        self.details_log.setWordWrap(True)
        self.details_layout.addWidget(self.details_log)
        self.details_layout.addStretch()
        self.details_area.setWidget(self.details_widget)
        self.details_area.setVisible(False)
        main_layout.addWidget(self.details_area)
        
        # Set default button states
        self.close_button.setEnabled(True)
        
        # Apply styling
        self.apply_styles()
    
    def apply_styles(self):
        """Apply custom styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 14px;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
                margin: 0.5px;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #a0a0a0;
            }
            QScrollArea {
                border: 1px solid #cccccc;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #d0d0d0;
            }
        """)
    
    def connectSignals(self):
        """Connect signals from widget manager to dialog slots."""
        self.widget_manager.install_status.connect(self.update_status)
        self.widget_manager.install_progress.connect(self.update_progress)
        self.widget_manager.install_complete.connect(self.installation_complete)
    
    def toggle_details(self, checked):
        """Toggle visibility of details area."""
        self.details_area.setVisible(checked)
        self.details_button.setText("Details verbergen" if checked else "Details weergeven")
        
        # Resize dialog based on details visibility
        if checked:
            self.resize(self.width(), self.height() + 150)
        else:
            self.resize(self.width(), self.height() - 150)
    
    def add_log_message(self, message):
        """Add a message to the details log."""
        current_text = self.details_log.text()
        if current_text == "Log details zullen hier verschijnen...":
            self.details_log.setText(message)
        else:
            self.details_log.setText(f"{current_text}\n{message}")
    
    def add_status_item(self, widget_name, message, status="pending"):
        """Add or update an item in the status list."""
        # Check if item already exists
        for i in range(self.status_list.count()):
            item = self.status_list.item(i)
            if item.data(Qt.UserRole) == widget_name:
                # Update existing item
                item.setText(f"{widget_name}: {message}")
                if status == "success":
                    item.setIcon(self.get_status_icon("success"))
                elif status == "error":
                    item.setIcon(self.get_status_icon("error"))
                elif status == "pending":
                    item.setIcon(self.get_status_icon("pending"))
                return
        
        # Create new item
        item = QListWidgetItem(f"{widget_name}: {message}")
        item.setData(Qt.UserRole, widget_name)
        if status == "success":
            item.setIcon(self.get_status_icon("success"))
        elif status == "error":
            item.setIcon(self.get_status_icon("error"))
        elif status == "pending":
            item.setIcon(self.get_status_icon("pending"))
        
        self.status_list.addItem(item)
        self.status_list.scrollToBottom()
    
    def get_status_icon(self, status):
        """Get an icon for the status."""
        if status == "success":
            # Try to get a check icon from the style
            return QApplication.style().standardIcon(QApplication.style().SP_DialogApplyButton)
        elif status == "error":
            # Try to get an error icon from the style
            return QApplication.style().standardIcon(QApplication.style().SP_DialogCancelButton)
        elif status == "pending":
            # Try to get a pending icon from the style
            return QApplication.style().standardIcon(QApplication.style().SP_BrowserReload)
        
        # Return an empty icon if nothing else works
        return QIcon()
    
    @pyqtSlot(str, str)
    def update_status(self, widget_name, status_message):
        """Update the status for a widget installation."""
        # Add widget to in-progress set if not there already
        if widget_name not in self.widgets_in_progress:
            self.widgets_in_progress.add(widget_name)
            self.add_status_item(widget_name, "Installatie gestart...", "pending")
        
        # Update current operation display
        self.current_widget_label.setText(f"Widget: {widget_name}")
        self.current_status_label.setText(f"Status: {status_message}")
        
        # Update status item
        self.add_status_item(widget_name, status_message, "pending")
        
        # Add to log
        self.add_log_message(f"[{widget_name}] {status_message}")
    
    @pyqtSlot(str, int, int)
    def update_progress(self, widget_name, current, total):
        """Update the progress for a widget installation."""
        if current > 0 and total > 0:
            progress_percent = int((current / total) * 100)
            self.progress_bar.setValue(progress_percent)
            
            # Add to log
            self.add_log_message(f"[{widget_name}] Voortgang: {current}/{total} ({progress_percent}%)")
    
    @pyqtSlot(str, bool, str)
    def installation_complete(self, widget_name, success, error_message):
        """Handle completion of a widget installation."""
        if success:
            # Installation succeeded
            self.widgets_completed.add(widget_name)
            if widget_name in self.widgets_in_progress:
                self.widgets_in_progress.remove(widget_name)
            
            # Update status item
            self.add_status_item(widget_name, "Installatie voltooid", "success")
            
            # Add to log
            self.add_log_message(f"[{widget_name}] Installatie succesvol voltooid")
        else:
            # Installation failed
            self.widgets_failed[widget_name] = error_message
            if widget_name in self.widgets_in_progress:
                self.widgets_in_progress.remove(widget_name)
            
            # Update status item
            self.add_status_item(widget_name, f"Fout: {error_message}", "error")
            
            # Add to log
            self.add_log_message(f"[{widget_name}] Installatie mislukt: {error_message}")
        
        # Update UI if nothing is in progress
        if not self.widgets_in_progress:
            self.current_widget_label.setText("Widget: -")
            self.current_status_label.setText("Status: Alle installaties voltooid")
            self.progress_bar.setValue(100)
    
    def request_installation(self, widget_name):
        """Request installation of a widget."""
        # Emit signal to request installation
        self.installation_requested.emit(widget_name)
        
        # Add to in-progress set
        if widget_name not in self.widgets_in_progress:
            self.widgets_in_progress.add(widget_name)
            self.add_status_item(widget_name, "Installatie aangevraagd...", "pending")