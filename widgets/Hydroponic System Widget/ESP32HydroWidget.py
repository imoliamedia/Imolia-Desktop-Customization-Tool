"""
ESP32 Hydro Widget voor Imolia Desktop Customizer

Dependencies:
PyQt5==5.15.6
PyQtWebEngine==5.15.6

"""

import json
import os
import logging
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, 
                             QLineEdit, QLabel, QDialog, QFormLayout, QGroupBox)
from PyQt5.QtCore import Qt, QUrl
# Probeer QtWebEngine te importeren met foutafhandeling
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    logger.error("QtWebEngine niet geïnstalleerd. Installeer PyQtWebEngine==5.15.6 met pip.")

from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

logger = logging.getLogger(__name__)

class ESP32HydroWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.systems = self.config.get('systems', [])
        self.initUI()
        
    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'esp32_hydro_widget_config.json')
        default_config = {
            'systems': [],
            'current_system': 0,
            'size': (800, 600),
            'position': (100, 100)
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.error(f"Fout bij laden configuratie: {e}")
        return default_config

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'esp32_hydro_widget_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuratie opgeslagen")
        except Exception as e:
            logger.error(f"Fout bij opslaan configuratie: {e}")

    def initUI(self):
        # Maak layout
        layout = QVBoxLayout()
        
        # Controls layout bovenaan
        controls_layout = QHBoxLayout()
        
        # System selector
        self.system_selector = QComboBox()
        self.update_system_selector()
        self.system_selector.currentIndexChanged.connect(self.change_system)
        controls_layout.addWidget(QLabel("Systeem:"))
        controls_layout.addWidget(self.system_selector)
        
        # Reload button
        reload_button = QPushButton("Herlaad")
        reload_button.clicked.connect(self.reload_page)
        controls_layout.addWidget(reload_button)
        
        layout.addLayout(controls_layout)
        
        # WebEngineView voor iframe inhoud (indien beschikbaar)
        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()
            self.web_view.setContextMenuPolicy(Qt.NoContextMenu)  # Contextmenu uitschakelen
            layout.addWidget(self.web_view)
        else:
            # Fallback als WebEngine niet beschikbaar is
            self.web_view = QLabel("QtWebEngine is niet geïnstalleerd.\nInstalleer PyQtWebEngine==5.15.6 met pip.")
            self.web_view.setAlignment(Qt.AlignCenter)
            self.web_view.setStyleSheet("background-color: #f0f0f0; padding: 20px; font-size: 14px;")
            layout.addWidget(self.web_view)
        
        # Laad de huidige pagina
        self.load_current_system()
        
        self.setLayout(layout)
        
        # Stel grootte en positie in vanuit configuratie
        size = self.config.get('size', (800, 600))
        self.resize(*size)
        
        position = self.config.get('position', (100, 100))
        self.move(*position)

    def update_system_selector(self):
        """Update de systeem selector met de beschikbare systemen"""
        self.system_selector.clear()
        for system in self.systems:
            self.system_selector.addItem(system['name'])

    def change_system(self, index):
        """Wissel naar een ander systeem"""
        if 0 <= index < len(self.systems):
            self.config['current_system'] = index
            self.save_config()
            self.load_current_system()
    
    def load_current_system(self):
        """Laad het huidige systeem in de webview"""
        if not self.systems:
            # Toon een bericht als er geen systemen zijn geconfigureerd
            if HAS_WEBENGINE:
                self.web_view.setHtml("<html><body><h2>Geen systemen geconfigureerd</h2><p>Gebruik de instellingen om een systeem toe te voegen.</p></body></html>")
            else:
                self.web_view.setText("Geen systemen geconfigureerd.\nGebruik de instellingen om een systeem toe te voegen.")
            return
            
        current_index = self.config.get('current_system', 0)
        if current_index >= len(self.systems):
            current_index = 0
            self.config['current_system'] = 0
            self.save_config()
            
        # Zorg ervoor dat de combo box de juiste index heeft
        if self.system_selector.currentIndex() != current_index:
            self.system_selector.setCurrentIndex(current_index)
            
        # Laad het systeem
        system = self.systems[current_index]
        url = system['ip']
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        logger.info(f"Laden van ESP32 systeem: {system['name']} op URL: {url}")
        
        if HAS_WEBENGINE:
            self.web_view.load(QUrl(url))
        else:
            self.web_view.setText(f"Zou {system['name']} laden van {url}\nInstaleer PyQtWebEngine==5.15.6 voor weergave.")
    
    def reload_page(self):
        """Herlaad de huidige pagina"""
        if HAS_WEBENGINE:
            self.web_view.reload()
            logger.info("Pagina herladen")
        else:
            # Herlaad de huidige systeem info voor het label
            self.load_current_system()

    def resizeEvent(self, event):
        """Verwerk resize event en sla nieuwe afmetingen op"""
        super().resizeEvent(event)
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        """Verwerk move event en sla nieuwe positie op"""
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

    def updateConfig(self, new_config):
        """Werk configuratie bij"""
        self.config.update(new_config)
        self.systems = self.config.get('systems', [])
        self.update_system_selector()
        self.load_current_system()
        self.save_config()

    def openSettings(self):
        """Open instellingen dialoog"""
        dialog = ESP32HydroSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

class ESP32HydroSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)
        self.setWindowTitle("ESP32 Hydro Widget Instellingen")
        self.resize(500, 400)

    def add_custom_section(self, layout):
        # Maak een gekloonde kopie van de systemen voor bewerking
        self.systems = list(self.widget.systems)
        
        # Systemen groep
        systems_group = QGroupBox("Hydrosystemen")
        systems_layout = QVBoxLayout()
        
        # Lijst van systemen
        self.systems_list = QComboBox()
        self.update_systems_list()
        systems_layout.addWidget(self.systems_list)
        
        # Formulier voor systeem details
        system_form = QFormLayout()
        
        self.system_name = QLineEdit()
        system_form.addRow("Systeemnaam:", self.system_name)
        
        self.system_ip = QLineEdit()
        system_form.addRow("IP-adres:", self.system_ip)
        
        systems_layout.addLayout(system_form)
        
        # Knoppen voor beheer
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Nieuw systeem")
        add_button.clicked.connect(self.add_system)
        buttons_layout.addWidget(add_button)
        
        update_button = QPushButton("Bijwerken")
        update_button.clicked.connect(self.update_system)
        buttons_layout.addWidget(update_button)
        
        delete_button = QPushButton("Verwijderen")
        delete_button.clicked.connect(self.delete_system)
        buttons_layout.addWidget(delete_button)
        
        systems_layout.addLayout(buttons_layout)
        systems_group.setLayout(systems_layout)
        layout.addWidget(systems_group)
        
        # Verbind signalen
        self.systems_list.currentIndexChanged.connect(self.load_system_details)
        
        # Laad eerste systeem indien beschikbaar
        if self.systems:
            self.load_system_details(0)

    def update_systems_list(self):
        """Update de systemenlijst"""
        self.systems_list.clear()
        for system in self.systems:
            self.systems_list.addItem(system['name'])
        
        # Voeg een lege optie toe als er geen systemen zijn
        if not self.systems:
            self.systems_list.addItem("Geen systemen")
            self.system_name.setEnabled(False)
            self.system_ip.setEnabled(False)
        else:
            self.system_name.setEnabled(True)
            self.system_ip.setEnabled(True)

    def load_system_details(self, index):
        """Laad details van geselecteerd systeem"""
        if 0 <= index < len(self.systems):
            system = self.systems[index]
            self.system_name.setText(system['name'])
            self.system_ip.setText(system['ip'])
        else:
            self.system_name.setText("")
            self.system_ip.setText("")

    def add_system(self):
        """Voeg nieuw systeem toe"""
        self.systems.append({
            'name': 'Nieuw systeem',
            'ip': '192.168.1.100'
        })
        self.update_systems_list()
        self.systems_list.setCurrentIndex(len(self.systems) - 1)

    def update_system(self):
        """Werk geselecteerd systeem bij"""
        index = self.systems_list.currentIndex()
        if 0 <= index < len(self.systems):
            self.systems[index] = {
                'name': self.system_name.text(),
                'ip': self.system_ip.text()
            }
            self.update_systems_list()
            self.systems_list.setCurrentIndex(index)

    def delete_system(self):
        """Verwijder geselecteerd systeem"""
        index = self.systems_list.currentIndex()
        if 0 <= index < len(self.systems):
            del self.systems[index]
            self.update_systems_list()
            if self.systems:
                self.systems_list.setCurrentIndex(0)

    def get_config(self):
        """Haal configuratie op uit dialoog"""
        return {
            'systems': self.systems,
            'current_system': min(self.widget.config.get('current_system', 0), max(0, len(self.systems) - 1))
        }

# De Widget-klasse moet deze naam hebben voor de loader
Widget = ESP32HydroWidget

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = ESP32HydroWidget()
    widget.show()
    sys.exit(app.exec_())