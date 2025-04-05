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
                             QPushButton, QFrame, QListWidget, QListWidgetItem,
                             QApplication)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon

import os
import logging

from src.gui.widget_installation_dialog import WidgetInstallationDialog

logger = logging.getLogger('DesktopCustomizer.WidgetManager')

class WidgetManagerDialog(QDialog):
    """Dialog for managing widgets and their dependencies."""
    
    def __init__(self, widget_manager, parent=None):
        super().__init__(parent)
        self.widget_manager = widget_manager
        self.installation_dialog = None
        self.initUI()
        self.connectSignals()
        
    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("Widget Beheer")
        self.setMinimumSize(600, 400)
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
        self.title_label = QLabel("Widget Beheer")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        self.subtitle_label = QLabel("Installeer en beheer widgets voor Imolia Desktop Customizer")
        header_layout.addWidget(self.subtitle_label)
        
        header_line = QFrame()
        header_line.setFrameShape(QFrame.HLine)
        header_line.setFrameShadow(QFrame.Sunken)
        header_layout.addWidget(header_line)
        
        main_layout.addLayout(header_layout)
        
        # Widget list
        self.widget_list = QListWidget()
        self.widget_list.setAlternatingRowColors(True)
        main_layout.addWidget(self.widget_list)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Vernieuwen")
        self.refresh_button.clicked.connect(self.refresh_widgets)
        button_layout.addWidget(self.refresh_button)
        
        self.install_button = QPushButton("Installeren")
        self.install_button.clicked.connect(self.install_selected_widget)
        self.install_button.setEnabled(False)
        button_layout.addWidget(self.install_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Sluiten")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        # Apply styling
        self.apply_styles()
        
        # Populate widget list
        self.refresh_widgets()
    
    def apply_styles(self):
        """Apply custom styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 14px;
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
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #d0d0d0;
            }
        """)
    
    def connectSignals(self):
        """Connect signals."""
        self.widget_list.itemSelectionChanged.connect(self.update_button_states)
        self.widget_list.itemDoubleClicked.connect(self.install_selected_widget)
        
        # Connect widget manager signals
        self.widget_manager.widget_added.connect(self.on_widget_added)
        self.widget_manager.widget_removed.connect(self.on_widget_removed)
        self.widget_manager.widget_updated.connect(self.on_widget_updated)
    
    def refresh_widgets(self):
        """Refresh the widget list."""
        self.widget_list.clear()
        
        # Scan for widgets
        self.widget_manager.scan_widgets()
        
        # Add widgets to list
        for widget_name in self.widget_manager.get_available_widgets():
            widget_info = self.widget_manager.get_widget_info(widget_name)
            if widget_info:
                is_installed, _ = self.widget_manager.check_dependencies(widget_name)
                
                # Create list item
                item = QListWidgetItem(widget_info.display_name)
                item.setData(Qt.UserRole, widget_name)
                
                # Set icon based on installation status
                if is_installed:
                    item.setIcon(QApplication.style().standardIcon(QApplication.style().SP_DialogApplyButton))
                else:
                    item.setIcon(QApplication.style().standardIcon(QApplication.style().SP_DialogHelpButton))
                
                # Add to list
                self.widget_list.addItem(item)
    
    def update_button_states(self):
        """Update the state of buttons based on selection."""
        selected_items = self.widget_list.selectedItems()
        self.install_button.setEnabled(len(selected_items) > 0)
    
    def install_selected_widget(self):
        """Install the selected widget."""
        selected_items = self.widget_list.selectedItems()
        if not selected_items:
            return
            
        # Get the widget name
        widget_name = selected_items[0].data(Qt.UserRole)
        if not widget_name:
            return
            
        # Check if dependencies are already installed
        is_installed, _ = self.widget_manager.check_dependencies(widget_name)
        if is_installed:
            # Widget is already installed, nothing to do
            return
            
        # Create installation dialog if needed
        if not self.installation_dialog:
            self.installation_dialog = WidgetInstallationDialog(self.widget_manager, self)
            self.installation_dialog.installation_requested.connect(self.widget_manager.install_dependencies)
            
        # Request installation
        self.installation_dialog.request_installation(widget_name)
        
        # Show the dialog
        self.installation_dialog.exec_()
        
        # Refresh widget list after installation
        self.refresh_widgets()
    
    def on_widget_added(self, widget_name):
        """Handle a widget being added."""
        self.refresh_widgets()
    
    def on_widget_removed(self, widget_name):
        """Handle a widget being removed."""
        self.refresh_widgets()
    
    def on_widget_updated(self, widget_name):
        """Handle a widget being updated."""
        self.refresh_widgets()