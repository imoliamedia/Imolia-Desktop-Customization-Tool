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

import os
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QPushButton, QTabWidget, QSplitter,
                             QWidget, QListWidget, QListWidgetItem, QStyle, QFrame,
                             QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap
from pathlib import Path
from src.config import APP_NAME, WIDGETS_FOLDER_NAME
from src.gui.widget_installation_dialog import WidgetInstallationDialog
from src.gui.widget_manager_dialog import WidgetManagerDialog

class SettingsWindow(QDialog):
    def __init__(self, settings, overlay):
        super().__init__()
        self.settings = settings
        self.overlay = overlay
        self.widget_manager_dialog = None
        self.pending_installations = {}  # Dictionary van widget_name -> status
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{APP_NAME} - Settings")
        self.setGeometry(300, 300, 500, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Probeer verschillende icoonfpaden
        icon_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icons", "tray_icon.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icons", "tray_icon.ico"),
            os.path.abspath("resources/icons/tray_icon.png"),
            os.path.abspath("resources/icons/tray_icon.ico")
        ]
        
        icon_set = False
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                logging.info(f"Icoon gevonden op pad: {icon_path}")
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
                icon_set = True
                break
        
        if not icon_set:
            logging.error("Geen icoon gevonden op de verwachte locaties.")
        
        main_layout = QVBoxLayout(self)
        
        # Top section with fixed size
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        self.setup_header(top_layout)
        top_widget.setFixedHeight(top_widget.sizeHint().height())
        
        # Bottom section (expandable)
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        self.setup_tabs(bottom_layout)
        self.setup_buttons(bottom_layout)
        
        # QSplitter to separate sections
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setStretchFactor(0, 0)  # Top section not stretchable
        splitter.setStretchFactor(1, 1)  # Bottom section stretchable
        
        main_layout.addWidget(splitter)
        
        # Connect widget manager signals
        self.overlay.widget_manager.install_status.connect(self.on_widget_install_status)
        self.overlay.widget_manager.install_progress.connect(self.on_widget_install_progress)
        self.overlay.widget_manager.install_complete.connect(self.on_widget_install_complete)
        
        self.apply_styles()

    def setup_header(self, layout):
        header_layout = QVBoxLayout()

        self.title_label = QLabel(APP_NAME)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)

        github_label = QLabel('<a href="https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/tree/main/widgets">Download widgets van GitHub</a>')
        github_label.setOpenExternalLinks(True)
        header_layout.addWidget(github_label)

        layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

    def setup_tabs(self, layout):
        # Voeg direct de Widgets tab toe, zonder tabbladen te gebruiken
        widgets_widget = self.createWidgetManagerTab()
        layout.addWidget(widgets_widget)

    def setup_buttons(self, layout):
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Opslaan")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Annuleren")
        self.cancel_button.setStyleSheet("background-color: #f44336; color: white; padding: 5px 15px;")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def createWidgetManagerTab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        widget_dir = Path.home() / "Documents" / WIDGETS_FOLDER_NAME
        self.info_label = QLabel(f"Widgets kunnen worden toegevoegd in:\n{widget_dir}")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Buttons for managing widgets
        button_layout = QHBoxLayout()
        
        self.open_folder_button = QPushButton("Open Widgets Map")
        self.open_folder_button.clicked.connect(lambda: os.startfile(str(widget_dir)))
        button_layout.addWidget(self.open_folder_button)
        
        self.manage_widgets_button = QPushButton("Widgets Beheren")
        self.manage_widgets_button.clicked.connect(self.open_widget_manager)
        button_layout.addWidget(self.manage_widgets_button)
        
        self.refresh_widgets_button = QPushButton("Vernieuwen")
        self.refresh_widgets_button.clicked.connect(self.refresh_widgets)
        button_layout.addWidget(self.refresh_widgets_button)
        
        layout.addLayout(button_layout)

        # Widget list with checkboxes
        self.widget_list = QListWidget()
        self.populate_widget_list()
        layout.addWidget(self.widget_list)

        tab.setLayout(layout)
        return tab

    def populate_widget_list(self):
        """Populate the widget list with available widgets."""
        self.widget_list.clear()
        available_widgets = self.overlay.widget_manager.get_available_widgets()
        active_widgets = self.settings.get('active_widgets', [])

        for widget_name in available_widgets:
            # Get widget info
            widget_info = self.overlay.widget_manager.get_widget_info(widget_name)
            if not widget_info:
                continue
                
            # Check if dependencies are installed
            is_installed, _ = self.overlay.widget_manager.check_dependencies(widget_name)
                
            # Create item widget
            item = QListWidgetItem()
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(5, 2, 5, 2)

            # Checkbox for enabling/disabling the widget
            checkbox = QCheckBox()
            checkbox.setChecked(widget_name in active_widgets)
            # Only enable checkbox if dependencies are installed
            checkbox.setEnabled(is_installed)
            item_layout.addWidget(checkbox)

            # Widget name and status
            label_layout = QVBoxLayout()
            title_label = QLabel(widget_info.display_name)
            title_label.setStyleSheet("font-weight: bold;")
            label_layout.addWidget(title_label)
            
            if not is_installed:
                status_label = QLabel("Dependencies moeten worden geïnstalleerd")
                status_label.setStyleSheet("color: #FF6347; font-size: 10px;")
                label_layout.addWidget(status_label)
                
                # Add install button in pending installations
                if widget_name in self.pending_installations:
                    status = self.pending_installations[widget_name]
                    status_bar = QProgressBar()
                    status_bar.setRange(0, 100)
                    if status.get('progress'):
                        status_bar.setValue(status['progress'])
                    else:
                        status_bar.setRange(0, 0)  # Indeterminate
                    label_layout.addWidget(status_bar)
                else:
                    install_button = QPushButton("Installeer")
                    install_button.setFixedWidth(80)
                    install_button.clicked.connect(lambda _, wn=widget_name: self.install_widget_dependencies(wn))
                    item_layout.addWidget(install_button)
            
            item_layout.addLayout(label_layout)
            item_layout.addStretch()

            # Settings button
            settings_button = QPushButton()
            settings_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
            settings_button.setToolTip("Widget instellingen")
            settings_button.clicked.connect(lambda _, wn=widget_name: self.open_widget_settings(wn))
            settings_button.setEnabled(widget_name in active_widgets)
            item_layout.addWidget(settings_button)

            # Set up item
            item_widget.setLayout(item_layout)
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.UserRole, widget_name)

            self.widget_list.addItem(item)
            self.widget_list.setItemWidget(item, item_widget)

    def refresh_widgets(self):
        """Refresh the widget list."""
        # Scan for new widgets
        self.overlay.widget_manager.scan_widgets()
        # Update the list
        self.populate_widget_list()
        
    def open_widget_manager(self):
        """Open the widget manager dialog."""
        if not self.widget_manager_dialog:
            self.widget_manager_dialog = WidgetManagerDialog(self.overlay.widget_manager, self)
            
        self.widget_manager_dialog.exec_()
        
        # Refresh widget list after manager closes
        self.refresh_widgets()
        
    def install_widget_dependencies(self, widget_name):
        """Install dependencies for a widget."""
        # Mark as pending
        self.pending_installations[widget_name] = {'status': 'pending', 'progress': 0}
        
        # Start installation
        self.overlay.widget_manager.install_dependencies(widget_name)
        
        # Update UI
        self.populate_widget_list()
        
    @pyqtSlot(str, str)
    def on_widget_install_status(self, widget_name, status_message):
        """Handle widget installation status update."""
        if widget_name in self.pending_installations:
            self.pending_installations[widget_name]['status'] = status_message
            
    @pyqtSlot(str, int, int)
    def on_widget_install_progress(self, widget_name, current, total):
        """Handle widget installation progress update."""
        if widget_name in self.pending_installations:
            progress = int((current / total) * 100)
            self.pending_installations[widget_name]['progress'] = progress
            # Update UI
            self.populate_widget_list()
            
    @pyqtSlot(str, bool, str)
    def on_widget_install_complete(self, widget_name, success, error_message):
        """Handle widget installation completion."""
        if widget_name in self.pending_installations:
            if success:
                # Remove from pending
                del self.pending_installations[widget_name]
                # Show success message
                QMessageBox.information(
                    self,
                    "Installatie voltooid",
                    f"De dependencies voor widget '{widget_name}' zijn succesvol geïnstalleerd."
                )
            else:
                # Mark as failed
                self.pending_installations[widget_name]['status'] = f"Mislukt: {error_message}"
                # Show error message
                QMessageBox.warning(
                    self,
                    "Installatie mislukt",
                    f"De dependencies voor widget '{widget_name}' konden niet worden geïnstalleerd.\n\nFoutmelding: {error_message}"
                )
                
            # Update UI
            self.populate_widget_list()

    def open_widget_settings(self, widget_name):
        """Open settings dialog for a specific widget."""
        if widget_name in self.overlay.widgets:
            self.overlay.widgets[widget_name].openSettings()
        else:
            # Widget is not active, show error message
            QMessageBox.information(
                self,
                "Widget niet actief",
                f"De widget '{widget_name}' is niet actief. Activeer de widget eerst door het vakje aan te vinken en op 'Opslaan' te klikken."
            )

    def save_settings(self):
        """Save settings and reload active widgets."""
        # Bewaar actieve widgets
        active_widgets = []
        for i in range(self.widget_list.count()):
            item = self.widget_list.item(i)
            widget_name = item.data(Qt.UserRole)
            checkbox = self.widget_list.itemWidget(item).layout().itemAt(0).widget()
            
            if checkbox.isChecked():
                # Check if dependencies are installed before activating
                is_installed, message = self.overlay.widget_manager.check_dependencies(widget_name)
                if is_installed:
                    active_widgets.append(widget_name)
                else:
                    # Dependencies not installed, show error
                    QMessageBox.warning(
                        self,
                        "Dependencies ontbreken",
                        f"De widget '{widget_name}' kan niet worden geactiveerd omdat de dependencies niet zijn geïnstalleerd.\n\nInstalleer de dependencies eerst."
                    )
                    # Uncheck the checkbox
                    checkbox.setChecked(False)

        self.settings.set('active_widgets', active_widgets)
        self.settings.save()

        # Reload active widgets
        self.overlay.load_active_widgets()

        self.accept()

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 12px;
            }
            QTabBar::tab:selected {
                background-color: white;
            }
            QLabel, QCheckBox {
                font-size: 14px;
            }
            QPushButton {
                padding: 5px;
                font-size: 14px;
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-radius: 4px;
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
            }
            QListWidget::item {
                border-bottom: 1px solid #e0e0e0;
                padding: 2px;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)