import json
import os
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QCalendarWidget, 
                             QListWidget, QListWidgetItem, QPushButton, QDialog, 
                             QFormLayout, QLineEdit, QSpinBox, QLabel, QColorDialog, QComboBox)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QColor, QTextCharFormat
import icalendar
import recurring_ical_events
import requests
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog
from datetime import datetime, timedelta, date

class GoogleCalendarWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()
        self.setupUpdateTimer()

    def load_config(self):
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
            'date_format': 'dd/mm/yyyy'  # Nieuwe optie voor datumformaat
        }
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        return default_config

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'google_calendar_widget_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        layout = QVBoxLayout(self)
        
        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.selectionChanged.connect(self.updateEventList)
        layout.addWidget(self.calendar)
        
        self.eventList = QListWidget()
        layout.addWidget(self.eventList)
        
        self.updateStyle()
        self.updateCalendar()

    def setupUpdateTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateCalendar)
        self.timer.start(self.config['update_interval'])

    def updateCalendar(self):
        events = self.fetchEvents()
        self.updateCalendarWithEvents(events)
        self.showUpcomingEvents()

    def fetchEvents(self):
        all_events = []
        for url in self.config['ical_urls']:
            try:
                response = requests.get(url)
                if not response.text.startswith('BEGIN:VCALENDAR'):
                    print(f"Error: The URL {url} does not appear to be a valid iCalendar feed.")
                    continue
                cal = icalendar.Calendar.from_ical(response.text)
                start_date = datetime.now().date()
                end_date = start_date + timedelta(days=365)
                events = recurring_ical_events.of(cal).between(start_date, end_date)
                for event in events:
                    event['CALENDAR_URL'] = url
                all_events.extend(events)
            except Exception as e:
                print(f"Error fetching calendar from {url}: {e}")
        return all_events

    def updateCalendarWithEvents(self, events):
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        for event in events:
            event_date = event.get('DTSTART').dt
            if isinstance(event_date, datetime):
                event_date = event_date.date()
            format = QTextCharFormat()
            format.setBackground(QColor(self.config['colors'].get(event['CALENDAR_URL'], '#FFB347')))
            self.calendar.setDateTextFormat(QDate(event_date), format)

    def updateEventList(self):
        selected_date = self.calendar.selectedDate().toPyDate()
        if selected_date == datetime.now().date():
            self.showUpcomingEvents()
        else:
            self.eventList.clear()
            events = self.fetchEvents()
            events_on_date = [
                e for e in events
                if (isinstance(e.get('DTSTART').dt, datetime) and e.get('DTSTART').dt.date() == selected_date) or
                   (isinstance(e.get('DTSTART').dt, date) and e.get('DTSTART').dt == selected_date)
            ]
            
            events_on_date.sort(key=lambda x: x.get('DTSTART').dt)
            for event in events_on_date[:self.config['num_events']]:
                start_time = event.get('DTSTART').dt
                if isinstance(start_time, datetime):
                    start_time_str = start_time.strftime('%H:%M')
                else:
                    start_time_str = "All day"
                item = QListWidgetItem(f"{start_time_str} - {event.get('SUMMARY', '')}")
                item.setBackground(QColor(self.config['colors'].get(event['CALENDAR_URL'], '#FFB347')))
                self.eventList.addItem(item)

    def showUpcomingEvents(self):
        self.eventList.clear()
        events = self.fetchEvents()
        now = datetime.now()
        
        def get_start_datetime(event):
            start = event.get('DTSTART').dt
            if isinstance(start, date) and not isinstance(start, datetime):
                return datetime.combine(start, datetime.min.time())
            return start.replace(tzinfo=None) if start.tzinfo else start

        upcoming_events = []
        for e in events:
            event_start = get_start_datetime(e)
            if event_start >= now:
                upcoming_events.append((event_start, e))
        
        upcoming_events.sort(key=lambda x: x[0])

        for _, event in upcoming_events[:self.config['num_events']]:
            start_time = get_start_datetime(event)
            if isinstance(start_time, datetime):
                start_time_str = self.format_date(start_time)
            else:
                start_time_str = self.format_date(start_time)
            item = QListWidgetItem(f"{start_time_str} - {event.get('SUMMARY', '')}")
            item.setBackground(QColor(self.config['colors'].get(event['CALENDAR_URL'], '#FFB347')))
            self.eventList.addItem(item)

    def format_date(self, date):
        date_format = self.config['date_format']
        if date_format == 'dd/mm/yyyy':
            return date.strftime('%d/%m/%Y %H:%M') if isinstance(date, datetime) else date.strftime('%d/%m/%Y')
        elif date_format == 'mm/dd/yyyy':
            return date.strftime('%m/%d/%Y %H:%M') if isinstance(date, datetime) else date.strftime('%m/%d/%Y')
        else:  # yyyy-mm-dd
            return date.strftime('%Y-%m-%d %H:%M') if isinstance(date, datetime) else date.strftime('%Y-%m-%d')

    def updateStyle(self):
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
        """)

    def updateConfig(self, new_config):
        self.config.update(new_config)
        self.updateStyle()
        self.save_config()
        self.updateCalendar()
        self.setupUpdateTimer()

    def openSettings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.updateConfig(self.config)  # Update with potentially changed config

class SettingsDialog(QDialog):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.setWindowTitle("Google Calendar Widget Instellingen")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.urlInputs = []
        for url in self.widget.config['ical_urls']:
            self.addUrlInput(url, form_layout)

        addCalendarButton = QPushButton("Kalender Toevoegen")
        addCalendarButton.clicked.connect(lambda: self.addUrlInput('', form_layout))
        form_layout.addRow(addCalendarButton)

        self.updateIntervalInput = QSpinBox()
        self.updateIntervalInput.setRange(1, 24)
        self.updateIntervalInput.setValue(self.widget.config['update_interval'] // 3600000)
        form_layout.addRow("Update Interval (uren):", self.updateIntervalInput)

        self.numEventsInput = QSpinBox()
        self.numEventsInput.setRange(1, 20)
        self.numEventsInput.setValue(self.widget.config['num_events'])
        form_layout.addRow("Aantal weer te geven gebeurtenissen:", self.numEventsInput)

        # Datumformaat optie
        self.dateFormatCombo = QComboBox()
        self.dateFormatCombo.addItems(['dd/mm/yyyy', 'mm/dd/yyyy', 'yyyy-mm-dd'])
        self.dateFormatCombo.setCurrentText(self.widget.config['date_format'])
        form_layout.addRow("Datumformaat:", self.dateFormatCombo)

        # Kleurinstellingen
        self.color_buttons = {}
        color_options = [
            ('widget_bg_color', 'Widget achtergrond'),
            ('widget_text_color', 'Widget tekst'),
            ('calendar_bg_color', 'Kalender achtergrond'),
            ('calendar_text_color', 'Kalender tekst'),
            ('selected_date_color', 'Geselecteerde datum'),
            ('event_list_bg_color', 'Gebeurtenissenlijst achtergrond'),
            ('event_list_text_color', 'Gebeurtenissenlijst tekst')
        ]

        for color_key, color_name in color_options:
            button = QPushButton()
            button.setStyleSheet(f"background-color: {self.widget.config[color_key]};")
            button.clicked.connect(lambda _, k=color_key: self.chooseWidgetColor(k))
            form_layout.addRow(f"{color_name}:", button)
            self.color_buttons[color_key] = button

        layout.addLayout(form_layout)

        buttonBox = QHBoxLayout()
        saveButton = QPushButton("Opslaan")
        saveButton.clicked.connect(self.saveSettings)
        cancelButton = QPushButton("Annuleren")
        cancelButton.clicked.connect(self.reject)
        buttonBox.addWidget(saveButton)
        buttonBox.addWidget(cancelButton)
        layout.addLayout(buttonBox)

    def addUrlInput(self, url, layout):
        urlInput = QLineEdit(url)
        urlInput.setEchoMode(QLineEdit.Password)
        colorButton = QPushButton()
        color = self.widget.config['colors'].get(url, '#FFB347')
        colorButton.setStyleSheet(f"background-color: {color};")
        colorButton.clicked.connect(lambda _, u=urlInput, b=colorButton: self.chooseColor(u, b))
        
        hbox = QHBoxLayout()
        hbox.addWidget(urlInput)
        hbox.addWidget(colorButton)
        
        self.urlInputs.append((urlInput, colorButton))
        layout.insertRow(layout.rowCount() - 1, f"Kalender URL {len(self.urlInputs)}:", hbox)

    def chooseColor(self, urlInput, button):
        color = QColorDialog.getColor()
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()};")
            self.widget.config['colors'][urlInput.text()] = color.name()

    def chooseWidgetColor(self, color_key):
        color = QColorDialog.getColor(QColor(self.widget.config[color_key]))
        if color.isValid():
            self.color_buttons[color_key].setStyleSheet(f"background-color: {color.name()};")
            self.widget.config[color_key] = color.name()

    def saveSettings(self):
        self.widget.config['ical_urls'] = [input.text() for input, _ in self.urlInputs if input.text()]
        self.widget.config['update_interval'] = self.updateIntervalInput.value() * 3600000
        self.widget.config['num_events'] = self.numEventsInput.value()
        self.widget.config['date_format'] = self.dateFormatCombo.currentText()
        
        for urlInput, colorButton in self.urlInputs:
            url = urlInput.text()
            if url:
                color = colorButton.palette().button().color().name()
                self.widget.config['colors'][url] = color

        # Nieuwe kleurinstellingen opslaan
        for color_key, button in self.color_buttons.items():
            self.widget.config[color_key] = button.palette().button().color().name()

        self.accept()

Widget = GoogleCalendarWidget