"""
Google Calendar Widget voor Imolia Desktop Customizer

Dependencies:
PyQt5==5.15.6
icalendar==5.0.7
recurring_ical_events==2.0.2
requests==2.28.1

"""

import json
import os
import logging
from datetime import datetime, timedelta, date
import traceback

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QCalendarWidget, 
                             QListWidget, QListWidgetItem, QPushButton, QDialog, 
                             QFormLayout, QLineEdit, QSpinBox, QLabel, QColorDialog, QComboBox,
                             QApplication, QMessageBox, QGroupBox, QWidget)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QColor, QTextCharFormat

# Importeer dependencies voor Google Calendar
try:
    import icalendar
    import recurring_ical_events
    import requests
except ImportError as e:
    # Toon foutmelding maar crash niet
    logging.error(f"Fout bij importeren van Google Calendar dependencies: {e}")

# Probeer eerst de absolute import voor draggable_widget
try:
    from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog
except ImportError:
    # Als dat niet lukt, probeer relatieve import vanuit de huidige map
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog
    except ImportError:
        # Als laatste optie, probeer het bestand direct te importeren
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        sys.path.insert(0, parent_dir)
        
        # Fallback implementatie als niets werkt
        from PyQt5.QtWidgets import QWidget
        
        class DraggableWidget(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                self.setAttribute(Qt.WA_TranslucentBackground)
                self.dragging = False
                self.offset = None
                self.config = self.load_config()
            
            def load_config(self):
                return {}
                
            def save_config(self):
                pass
                
            def mousePressEvent(self, event):
                if event.button() == Qt.LeftButton:
                    self.dragging = True
                    self.offset = event.pos()

            def mouseMoveEvent(self, event):
                if self.dragging and self.offset:
                    self.move(self.mapToParent(event.pos() - self.offset))
                    
            def mouseReleaseEvent(self, event):
                self.dragging = False
                
            def updateConfig(self, new_config):
                pass
                
            def openSettings(self):
                pass
        
        class WidgetSettingsDialog(QDialog):
            def __init__(self, widget, parent=None):
                super().__init__(parent)
                self.widget = widget
                
            def get_config(self):
                return {}

# Logger instellen
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GoogleCalendarWidget")

class GoogleCalendarWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.events_loaded = False  # Bijhouden of events zijn geladen
        self.initUI()
        self.setupUpdateTimer()
        
        # Startupbericht toevoegen om beter te kunnen debuggen
        logger.info("Google Calendar Widget geïnitialiseerd, directe update van agenda gepland...")
        
        # De eerste updateCalendar aanroep uitstellen om ervoor te zorgen dat de widget volledig is geïnitialiseerd
        QTimer.singleShot(500, self.initialCalendarUpdate)

    def initialCalendarUpdate(self):
        """Initiële kalenderupdate met betere foutafhandeling"""
        logger.info("Eerste kalenderupdate uitvoeren...")
        try:
            # Probeer events op te halen en agendawidget bij te werken
            success = self.updateCalendar(show_errors=True)
            if success:
                logger.info("Eerste kalenderupdate succesvol voltooid.")
                self.events_loaded = True
            else:
                # Als de eerste update mislukt, plan een snelle herpoging (na 10 seconden)
                logger.warning("Eerste kalenderupdate mislukt, nieuwe poging gepland over 10 seconden.")
                QTimer.singleShot(10000, lambda: self.updateCalendar(show_errors=True))
        except Exception as e:
            logger.error(f"Onverwachte fout bij initiële kalenderupdate: {e}")
            logger.error(traceback.format_exc())

    def load_config(self):
        """Laad configuratie uit bestand of gebruik standaardwaarden."""
        config_path = os.path.join(os.path.dirname(__file__), 'google_calendar_widget_config.json')
        default_config = {
            'ical_urls': [],
            'colors': {},
            'update_interval': 3600000,  # 1 uur in milliseconden
            'num_events': 5,
            'widget_bg_color': '#FFFFFF',
            'widget_text_color': '#000000',
            'calendar_bg_color': '#F0F0F0',
            'calendar_text_color': '#000000',
            'selected_date_color': '#3498DB',
            'event_list_bg_color': '#FFFFFF',
            'event_list_text_color': '#000000',
            'date_format': 'dd/mm/yyyy',
            'size': (400, 600),
            'position': (100, 100)
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    logger.info(f"Configuratie geladen uit: {config_path}")
                    # Update default_config met instellingen uit bestand
                    default_config.update(loaded_config)
            except Exception as e:
                logger.error(f"Fout bij laden configuratie: {e}")
                logger.error(traceback.format_exc())
        else:
            logger.info(f"Geen configuratiebestand gevonden, standaardinstellingen worden gebruikt")
        
        return default_config

    def save_config(self):
        """Sla configuratie op in bestand."""
        config_path = os.path.join(os.path.dirname(__file__), 'google_calendar_widget_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuratie opgeslagen naar: {config_path}")
        except Exception as e:
            logger.error(f"Fout bij opslaan configuratie: {e}")
            logger.error(traceback.format_exc())

    def initUI(self):
        """Initialiseer gebruikersinterface."""
        try:
            layout = QVBoxLayout(self)
            
            self.calendar = QCalendarWidget()
            self.calendar.setSelectedDate(QDate.currentDate())
            self.calendar.selectionChanged.connect(self.updateEventList)
            layout.addWidget(self.calendar)
            
            self.eventList = QListWidget()
            layout.addWidget(self.eventList)
            
            # Voeg een handmatige vernieuwknop toe om events direct te kunnen bijwerken
            refresh_button = QPushButton("Agenda verversen")
            refresh_button.clicked.connect(lambda: self.updateCalendar(show_errors=True))
            layout.addWidget(refresh_button)
            
            self.setLayout(layout)
            
            # Stel grootte en positie in vanuit configuratie
            size = self.config.get('size', (400, 600))
            self.resize(*size)
            
            position = self.config.get('position', (100, 100))
            self.move(*position)
            
            # Pas stijl aan
            self.updateStyle()
            
            logger.info("UI geïnitialiseerd")
        except Exception as e:
            logger.error(f"Fout bij initialiseren UI: {e}")
            logger.error(traceback.format_exc())

    def setupUpdateTimer(self):
        """Stel timer in voor automatisch verversen van kalendergebeurtenissen."""
        try:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.updateCalendar)
            
            # Gebruik een kortere interval (5 minuten) in plaats van een uur voor frequentere updates
            update_interval = min(self.config['update_interval'], 300000)  # Max 5 minuten als standaard
            
            self.timer.start(update_interval)
            logger.info(f"Update timer ingesteld op {update_interval} ms")
        except Exception as e:
            logger.error(f"Fout bij instellen update timer: {e}")
            logger.error(traceback.format_exc())

    def updateCalendar(self, show_errors=False):
        """Haal events op en werk de kalender bij."""
        try:
            logger.info("Kalender bijwerken gestart...")
            
            # Controleer of er URLs zijn geconfigureerd
            if not self.config['ical_urls']:
                logger.warning("Geen iCal URLs geconfigureerd, kan agenda niet bijwerken")
                if show_errors:
                    QMessageBox.warning(self, "Geen agenda's geconfigureerd",
                                       "Er zijn geen agenda-URLs geconfigureerd. Ga naar instellingen om agenda's toe te voegen.")
                return False
                
            # Statusmelding in de eventList als er events worden opgehaald
            if self.eventList.count() == 0:
                self.eventList.addItem("Agenda gebeurtenissen laden...")
            
            # Events ophalen
            events = self.fetchEvents(show_errors)
            
            if events is None:  # Fout bij het ophalen van events
                if self.eventList.count() == 1 and self.eventList.item(0).text() == "Agenda gebeurtenissen laden...":
                    self.eventList.clear()
                    self.eventList.addItem("Fout bij laden van agenda. Probeer opnieuw.")
                return False
                
            # Kalender bijwerken met events
            self.updateCalendarWithEvents(events)
            
            # Eventuele status berichten verwijderen
            if self.eventList.count() == 1:
                item_text = self.eventList.item(0).text()
                if item_text in ["Agenda gebeurtenissen laden...", "Fout bij laden van agenda. Probeer opnieuw."]:
                    self.eventList.clear()
            
            # Toon aankomende events of events voor geselecteerde datum
            self.updateEventList()
            
            logger.info("Kalender succesvol bijgewerkt")
            return True
            
        except Exception as e:
            logger.error(f"Fout bij bijwerken kalender: {e}")
            logger.error(traceback.format_exc())
            
            if show_errors:
                QMessageBox.warning(self, "Fout bij bijwerken agenda",
                                   f"Er is een fout opgetreden bij het bijwerken van de agenda:\n\n{str(e)}")
            return False

    def fetchEvents(self, show_errors=False):
        """Haal gebeurtenissen op van ical URLs."""
        all_events = []
        
        if not self.config['ical_urls']:
            logger.warning("Geen iCal URLs geconfigureerd")
            return all_events
        
        error_messages = []
            
        for url in self.config['ical_urls']:
            try:
                logger.info(f"Events ophalen van: {url}")
                
                # Timeout instellen om te voorkomen dat de widget vastloopt bij langzame verbindingen
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    error_msg = f"URL {url} retourneerde status code {response.status_code}"
                    logger.error(error_msg)
                    error_messages.append(error_msg)
                    continue
                    
                cal_text = response.text
                
                if not cal_text.startswith('BEGIN:VCALENDAR'):
                    error_msg = f"URL is geen geldige iCalendar feed: {url}"
                    logger.error(error_msg)
                    error_messages.append(error_msg)
                    continue
                    
                cal = icalendar.Calendar.from_ical(cal_text)
                start_date = datetime.now().date()
                end_date = start_date + timedelta(days=365)
                events = recurring_ical_events.of(cal).between(start_date, end_date)
                
                for event in events:
                    event['CALENDAR_URL'] = url
                    
                all_events.extend(events)
                logger.info(f"{len(events)} events opgehaald van {url}")
            except requests.exceptions.RequestException as e:
                error_msg = f"Netwerk fout bij ophalen kalender van {url}: {str(e)}"
                logger.error(error_msg)
                error_messages.append(error_msg)
            except Exception as e:
                error_msg = f"Fout bij ophalen kalender van {url}: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                error_messages.append(error_msg)
        
        # Toon fouten als er geen events zijn opgehaald maar er wel URLs zijn geconfigureerd
        if not all_events and error_messages and show_errors:
            error_text = "\n".join(error_messages)
            QMessageBox.warning(self, "Fout bij ophalen agenda", 
                               f"Er zijn fouten opgetreden bij het ophalen van de agenda's:\n\n{error_text}")
            return None
                
        return all_events

    def updateCalendarWithEvents(self, events):
        """Werk kalender bij met events en markeer datums met gebeurtenissen."""
        try:
            # Reset alle datums naar standaard stijl
            self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
            
            if not events:
                logger.info("Geen events om kalender mee bij te werken")
                return
                
            for event in events:
                event_date = event.get('DTSTART').dt
                if isinstance(event_date, datetime):
                    event_date = event_date.date()
                    
                # Maak een tekstopmaak voor deze datum
                format = QTextCharFormat()
                event_color = self.config['colors'].get(event['CALENDAR_URL'], '#FFB347')
                format.setBackground(QColor(event_color))
                
                # Stel de opmaak in voor deze datum
                qdate = QDate(event_date.year, event_date.month, event_date.day)
                self.calendar.setDateTextFormat(qdate, format)
            
            logger.info(f"Kalender bijgewerkt met {len(events)} events")
        except Exception as e:
            logger.error(f"Fout bij bijwerken kalender met events: {e}")
            logger.error(traceback.format_exc())

    def updateEventList(self):
        """Werk eventlijst bij voor geselecteerde datum."""
        try:
            selected_date = self.calendar.selectedDate().toPyDate()
            
            # Als vandaag is geselecteerd, toon aankomende events
            if selected_date == datetime.now().date():
                self.showUpcomingEvents()
                return
            
            # Wis de huidige lijst
            self.eventList.clear()
            
            # Toon een laadmelding
            loading_item = QListWidgetItem("Events laden...")
            self.eventList.addItem(loading_item)
            
            # Force update van de UI
            QApplication.processEvents()
            
            # Haal events op en filter op geselecteerde datum
            events = self.fetchEvents()
            
            # Verwijder de laadmelding
            self.eventList.clear()
            
            if not events:
                self.eventList.addItem("Geen events gevonden.")
                return
                
            events_on_date = []
            
            for e in events:
                start_dt = e.get('DTSTART').dt
                event_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
                if event_date == selected_date:
                    events_on_date.append(e)
            
            # Sorteer op starttijd
            events_on_date.sort(key=lambda x: x.get('DTSTART').dt)
            
            # Voeg events toe aan lijst (beperkt tot ingesteld aantal)
            if events_on_date:
                for event in events_on_date[:self.config['num_events']]:
                    start_time = event.get('DTSTART').dt
                    if isinstance(start_time, datetime):
                        start_time_str = start_time.strftime('%H:%M')
                    else:
                        start_time_str = "Hele dag"
                        
                    summary = event.get('SUMMARY', '')
                    item = QListWidgetItem(f"{start_time_str} - {summary}")
                    
                    # Stel de achtergrondkleur in o.b.v. de URL
                    color = self.config['colors'].get(event['CALENDAR_URL'], '#FFB347')
                    item.setBackground(QColor(color))
                    
                    self.eventList.addItem(item)
            else:
                self.eventList.addItem("Geen events voor deze datum.")
                
            logger.info(f"{len(events_on_date)} events getoond voor {selected_date}")
        except Exception as e:
            logger.error(f"Fout bij bijwerken eventlijst: {e}")
            logger.error(traceback.format_exc())
            self.eventList.clear()
            self.eventList.addItem("Fout bij laden van events.")

    def showUpcomingEvents(self):
        """Toon aankomende gebeurtenissen in de eventlijst."""
        try:
            self.eventList.clear()
            
            # Toon een laadmelding
            loading_item = QListWidgetItem("Aankomende events laden...")
            self.eventList.addItem(loading_item)
            
            # Force update van de UI
            QApplication.processEvents()
            
            # Events ophalen
            events = self.fetchEvents()
            
            # Verwijder de laadmelding
            self.eventList.clear()
            
            if not events:
                self.eventList.addItem("Geen aankomende events gevonden.")
                return
                
            now = datetime.now()
            
            # Hulpfunctie voor het omzetten van datum naar datetime
            def get_start_datetime(event):
                start = event.get('DTSTART').dt
                if isinstance(start, date) and not isinstance(start, datetime):
                    return datetime.combine(start, datetime.min.time())
                return start.replace(tzinfo=None) if start.tzinfo else start
            
            # Filter events die in de toekomst liggen
            upcoming_events = []
            for e in events:
                event_start = get_start_datetime(e)
                if event_start >= now:
                    upcoming_events.append((event_start, e))
            
            # Sorteer op startdatum/-tijd
            upcoming_events.sort(key=lambda x: x[0])
            
            # Voorkom dubbele events
            displayed_events = []
            
            # Toon events in de lijst
            if upcoming_events:
                for start_time, event in upcoming_events:
                    if len(displayed_events) >= self.config['num_events']:
                        break
                    
                    # Maak een unieke sleutel voor dit event
                    event_key = (start_time, event.get('SUMMARY', ''))
                    
                    # Voeg toe als dit event nog niet is weergegeven
                    if event_key not in displayed_events:
                        displayed_events.append(event_key)
                        
                        # Formatteer de datum/tijd
                        start_time_str = self.format_date(start_time)
                        
                        # Maak een nieuw item
                        item = QListWidgetItem(f"{start_time_str} - {event.get('SUMMARY', '')}")
                        
                        # Stel de achtergrondkleur in
                        item.setBackground(QColor(self.config['colors'].get(event['CALENDAR_URL'], '#FFB347')))
                        
                        # Voeg toe aan lijst
                        self.eventList.addItem(item)
            else:
                self.eventList.addItem("Geen aankomende events gevonden.")
                    
            logger.info(f"{len(displayed_events)} aankomende events getoond")
        except Exception as e:
            logger.error(f"Fout bij tonen aankomende events: {e}")
            logger.error(traceback.format_exc())
            self.eventList.clear()
            self.eventList.addItem("Fout bij laden van aankomende events.")

    def format_date(self, date_obj):
        """Formatteer datum volgens ingesteld formaat."""
        try:
            date_format = self.config['date_format']
            if date_format == 'dd/mm/yyyy':
                return date_obj.strftime('%d/%m/%Y %H:%M') if isinstance(date_obj, datetime) else date_obj.strftime('%d/%m/%Y')
            elif date_format == 'mm/dd/yyyy':
                return date_obj.strftime('%m/%d/%Y %H:%M') if isinstance(date_obj, datetime) else date_obj.strftime('%m/%d/%Y')
            else:  # yyyy-mm-dd
                return date_obj.strftime('%Y-%m-%d %H:%M') if isinstance(date_obj, datetime) else date_obj.strftime('%Y-%m-%d')
        except Exception as e:
            logger.error(f"Fout bij formatteren datum: {e}")
            logger.error(traceback.format_exc())
            # Fallback formaat
            return str(date_obj)

    def updateStyle(self):
        """Pas styling van de widget aan op basis van de configuratie."""
        try:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.config['widget_bg_color']};
                    color: {self.config['widget_text_color']};
                }}
                QCalendarWidget {{
                    background-color: {self.config['calendar_bg_color']};
                    color: {self.config['calendar_text_color']};
                }}
                QCalendarWidget QToolButton {{
                    color: {self.config['calendar_text_color']};
                }}
                QCalendarWidget QMenu {{
                    color: {self.config['calendar_text_color']};
                }}
                QCalendarWidget QTableView {{
                    selection-background-color: {self.config['selected_date_color']};
                }}
                QListWidget {{
                    background-color: {self.config['event_list_bg_color']};
                    color: {self.config['event_list_text_color']};
                }}
                QPushButton {{
                    background-color: {self.config['selected_date_color']};
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: #2980b9;
                }}
            """)
            logger.info("Widget stijl bijgewerkt")
        except Exception as e:
            logger.error(f"Fout bij bijwerken stijl: {e}")
            logger.error(traceback.format_exc())

    def updateConfig(self, new_config):
        """Werk de configuratie bij en pas de widget aan."""
        try:
            # Update de huidige configuratie
            self.config.update(new_config)
            
            # Pas de stijl aan
            self.updateStyle()
            
            # Sla configuratie op
            self.save_config()
            
            # Werk kalender direct bij
            self.updateCalendar(show_errors=True)
            
            # Pas de update timer aan indien nodig
            if 'update_interval' in new_config:
                # Gebruik een kortere interval (5 minuten) als minimum
                update_interval = min(self.config['update_interval'], 300000)
                self.timer.start(update_interval)
                
            logger.info("Configuratie bijgewerkt")
        except Exception as e:
            logger.error(f"Fout bij bijwerken configuratie: {e}")
            logger.error(traceback.format_exc())

    def openSettings(self):
        """Open het instellingenvenster."""
        try:
            dialog = GoogleCalendarSettingsDialog(self)
            if dialog.exec_():
                new_config = dialog.get_config()
                self.updateConfig(new_config)
                logger.info("Instellingen opgeslagen")
        except Exception as e:
            logger.error(f"Fout bij openen instellingen: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.warning(self, "Fout", f"Er is een fout opgetreden bij het openen van de instellingen: {e}")

    def resizeEvent(self, event):
        """Verwerk resize event en sla nieuwe afmetingen op."""
        try:
            super().resizeEvent(event)
            self.config['size'] = (self.width(), self.height())
            self.save_config()
        except Exception as e:
            logger.error(f"Fout in resizeEvent: {e}")

    def moveEvent(self, event):
        """Verwerk move event en sla nieuwe positie op."""
        try:
            super().moveEvent(event)
            self.config['position'] = (self.x(), self.y())
            self.save_config()
        except Exception as e:
            logger.error(f"Fout in moveEvent: {e}")

class ColorButton(QPushButton):
    """Knop voor kleurkeuze met veilige fooutafhandeling."""
    def __init__(self, color="#FFFFFF", parent=None):
        super().__init__(parent)
        self.setColor(color)
        self.clicked.connect(self.chooseColor)
        
    def setColor(self, color):
        """Stel de kleur van de knop in."""
        try:
            self.color = color
            self.setStyleSheet(f"background-color: {color}; min-width: 60px; min-height: 20px;")
        except Exception as e:
            logger.error(f"Fout bij instellen kleur op knop: {e}")
            self.color = "#FFFFFF"  # Fallback naar wit
            
    def chooseColor(self):
        """Open de kleurkiezer en verwerk de keuze."""
        try:
            color = QColorDialog.getColor(QColor(self.color))
            if color.isValid():
                self.setColor(color.name())
        except Exception as e:
            logger.error(f"Fout bij kiezen kleur: {e}")
            QMessageBox.warning(self, "Fout", f"Er is een fout opgetreden bij het kiezen van een kleur: {e}")
            
    def getColor(self):
        """Haal de huidige kleur op."""
        return self.color

class GoogleCalendarSettingsDialog(QDialog):
    """Verbeterde instellingendialoog voor Google Calendar Widget."""
    def __init__(self, widget, parent=None):
        super().__init__(parent)
        self.widget = widget
        self.temp_config = dict(widget.config)  # Maak een kopie van de config
        self.url_inputs = []  # Lijst van URL inputs
        
        self.setWindowTitle("Google Calendar Instellingen")
        self.setMinimumWidth(500)
        self.initUI()
        
    def initUI(self):
        """Initialiseer de UI van de instellingendialoog."""
        try:
            main_layout = QVBoxLayout(self)
            
            # URLs sectie
            url_group = QGroupBox("Kalender URLs")
            url_layout = QVBoxLayout()
            
            # Instructie label
            url_help = QLabel("Voeg iCalendar (*.ics) URL's toe van je Google Calendar of andere agenda's. Je kunt deze URL's vinden in je Google Calendar instellingen onder 'Integratie'.")
            url_help.setWordWrap(True)
            url_layout.addWidget(url_help)
            
            # Voeg bestaande URLs toe
            for url in self.temp_config['ical_urls']:
                self.addUrlInput(url_layout, url)
            
            # Knop om URL toe te voegen
            add_button = QPushButton("Voeg Kalender URL toe")
            add_button.clicked.connect(lambda: self.addUrlInput(url_layout))
            url_layout.addWidget(add_button)
            
            url_group.setLayout(url_layout)
            main_layout.addWidget(url_group)
            
            # Algemene instellingen sectie
            general_group = QGroupBox("Algemene Instellingen")
            general_layout = QFormLayout()
            
            # Update interval
            self.update_interval = QSpinBox()
            self.update_interval.setRange(1, 60)
            self.update_interval.setValue(self.temp_config['update_interval'] // 60000)  # Omzetten naar minuten
            self.update_interval.setSuffix(" minuten")
            general_layout.addRow("Update interval:", self.update_interval)
            
            # Aantal events
            self.num_events = QSpinBox()
            self.num_events.setRange(1, 20)
            self.num_events.setValue(self.temp_config['num_events'])
            general_layout.addRow("Aantal events om te tonen:", self.num_events)
            
            # Datumformaat
            self.date_format = QComboBox()
            self.date_format.addItems(['dd/mm/yyyy', 'mm/dd/yyyy', 'yyyy-mm-dd'])
            self.date_format.setCurrentText(self.temp_config['date_format'])
            general_layout.addRow("Datumformaat:", self.date_format)
            
            general_group.setLayout(general_layout)
            main_layout.addWidget(general_group)
            
            # Kleurinstellingen sectie
            colors_group = QGroupBox("Kleuren")
            colors_layout = QFormLayout()
            
            # Maak kleurknoppen voor alle kleuren in de config
            self.color_buttons = {}
            color_keys = [
                ('widget_bg_color', 'Widget achtergrond'),
                ('widget_text_color', 'Widget tekst'),
                ('calendar_bg_color', 'Kalender achtergrond'),
                ('calendar_text_color', 'Kalender tekst'),
                ('selected_date_color', 'Geselecteerde datum'),
                ('event_list_bg_color', 'Eventlijst achtergrond'),
                ('event_list_text_color', 'Eventlijst tekst')
            ]
            
            for key, label in color_keys:
                color_button = ColorButton(self.temp_config[key])
                colors_layout.addRow(label + ":", color_button)
                self.color_buttons[key] = color_button
            
            colors_group.setLayout(colors_layout)
            main_layout.addWidget(colors_group)
            
            # Knoppen onderaan
            buttons_layout = QHBoxLayout()
            save_button = QPushButton("Opslaan")
            save_button.clicked.connect(self.accept)
            cancel_button = QPushButton("Annuleren")
            cancel_button.clicked.connect(self.reject)
            
            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(cancel_button)
            main_layout.addLayout(buttons_layout)
            
            logger.info("Google Calendar instellingendialoog geïnitialiseerd")
        except Exception as e:
            logger.error(f"Fout bij initialiseren instellingendialoog UI: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Fout", f"Er is een fout opgetreden bij het initialiseren van de instellingendialoog: {e}")
    
    def addUrlInput(self, layout, url=""):
        """Voeg een URL input toe aan de layout."""
        try:
            # Maak een container voor deze rij
            url_container = QWidget()
            url_row = QHBoxLayout(url_container)
            url_row.setContentsMargins(0, 0, 0, 0)
            
            # URL input veld
            url_input = QLineEdit(url)
            url_input.setPlaceholderText("Voer iCal URL in (https://...)")
            url_row.addWidget(url_input)
            
            # Kleurknop voor deze URL
            color = self.temp_config['colors'].get(url, "#FFB347")  # Standaardkleur als de URL nieuw is
            color_button = ColorButton(color)
            url_row.addWidget(color_button)
            
            # Verwijderknop
            remove_button = QPushButton("Verwijderen")
            remove_button.clicked.connect(lambda: self.removeUrlInput(url_container))
            url_row.addWidget(remove_button)
            
            # Voeg container toe aan layout
            layout.insertWidget(layout.count() - 1, url_container)  # Invoegen boven de "Voeg toe" knop
            
            # Bewaar referentie naar deze inputs
            self.url_inputs.append((url_input, color_button, url_container))
            
            logger.info(f"URL input toegevoegd: {url}")
        except Exception as e:
            logger.error(f"Fout bij toevoegen URL input: {e}")
            logger.error(traceback.format_exc())
    
    def removeUrlInput(self, container):
        """Verwijder een URL input uit de layout."""
        try:
            # Zoek de juiste input in onze lijst
            for i, (url_input, color_button, url_container) in enumerate(self.url_inputs):
                if url_container == container:
                    # Verwijder uit lijst
                    self.url_inputs.pop(i)
                    
                    # Verwijder widget
                    container.setParent(None)
                    container.deleteLater()
                    
                    logger.info("URL input verwijderd")
                    break
        except Exception as e:
            logger.error(f"Fout bij verwijderen URL input: {e}")
            logger.error(traceback.format_exc())
    
    def accept(self):
        """Verwerk instellingen bij accepteren van de dialoog."""
        try:
            # Verzamel instellingen
            new_config = self.get_config()
            
            # Sla op in widget
            super().accept()
            
            logger.info("Instellingendialoog geaccepteerd")
        except Exception as e:
            logger.error(f"Fout bij accepteren instellingendialoog: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Fout", f"Er is een fout opgetreden bij het opslaan van de instellingen: {e}")
    
    def get_config(self):
        """Verzamel alle instellingen uit de dialoog."""
        try:
            # Bouw een nieuwe configuratie op
            new_config = {}
            
            # Verzamel URLs en kleuren
            urls = []
            colors = {}
            
            for url_input, color_button, _ in self.url_inputs:
                url = url_input.text().strip()
                if url:  # Alleen valide URLs toevoegen
                    urls.append(url)
                    colors[url] = color_button.getColor()
            
            new_config['ical_urls'] = urls
            new_config['colors'] = colors
            
            # Verzamel algemene instellingen
            new_config['update_interval'] = self.update_interval.value() * 60000  # Omzetten naar milliseconden
            new_config['num_events'] = self.num_events.value()
            new_config['date_format'] = self.date_format.currentText()
            
            # Verzamel kleurinstellingen
            for key, button in self.color_buttons.items():
                new_config[key] = button.getColor()
            
            # Behoud originele grootte en positie
            new_config['size'] = self.widget.config['size']
            new_config['position'] = self.widget.config['position']
            
            logger.info("Configuratie verzameld uit instellingendialoog")
            return new_config
        except Exception as e:
            logger.error(f"Fout bij verzamelen configuratie: {e}")
            logger.error(traceback.format_exc())
            # Return originele config als er iets fout gaat
            return dict(self.widget.config)

# De Widget-klasse moet deze naam hebben voor de loader
Widget = GoogleCalendarWidget

# Voor standalone tests
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())