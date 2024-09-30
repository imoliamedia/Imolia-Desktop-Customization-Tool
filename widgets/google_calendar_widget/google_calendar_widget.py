"""
Google Calendar Widget for Imolia Desktop Customizer

Dependencies:
PyQt5==5.15.6
icalendar==5.0.7
recurring_ical_events==2.0.2
requests==2.28.1

Description:
This widget displays events from multiple Google Calendar feeds using iCal URLs.
It provides a calendar view and a list of upcoming events, with customizable colors and update intervals.
"""

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
            'update_interval': 3600000,  # 1 hour in milliseconds
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
        
        self.setLayout(layout)
        
        size = self.config.get('size', (400, 600))
        self.resize(*size)
        
        position = self.config.get('position', (100, 100))
        self.move(*position)
        
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
        dialog = GoogleCalendarSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

class GoogleCalendarSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)
        self.widget = widget
        self.init_ui()

    def init_ui(self):
        layout = self.layout()

        self.urlInputs = []
        for url in self.widget.config['ical_urls']:
            self.add_url_input(url, layout)

        add_calendar_button = QPushButton("Add Calendar")
        add_calendar_button.clicked.connect(lambda: self.add_url_input('', layout))
        layout.addWidget(add_calendar_button)

        self.update_interval_input = QSpinBox()
        self.update_interval_input.setRange(1, 24)
        self.update_interval_input.setValue(self.widget.config['update_interval'] // 3600000)
        layout.addWidget(QLabel("Update Interval (hours):"))
        layout.addWidget(self.update_interval_input)

        self.num_events_input = QSpinBox()
        self.num_events_input.setRange(1, 20)
        self.num_events_input.setValue(self.widget.config['num_events'])
        layout.addWidget(QLabel("Number of events to display:"))
        layout.addWidget(self.num_events_input)

        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(['dd/mm/yyyy', 'mm/dd/yyyy', 'yyyy-mm-dd'])
        self.date_format_combo.setCurrentText(self.widget.config['date_format'])
        layout.addWidget(QLabel("Date format:"))
        layout.addWidget(self.date_format_combo)

        self.init_color_buttons(layout)

    def add_url_input(self, url, layout):
        url_input = QLineEdit(url)
        url_input.setEchoMode(QLineEdit.Password)
        color_button = QPushButton()
        color = self.widget.config['colors'].get(url, '#FFB347')
        color_button.setStyleSheet(f"background-color: {color};")
        color_button.clicked.connect(lambda _, u=url_input, b=color_button: self.choose_color(u, b))
        
        hbox = QHBoxLayout()
        hbox.addWidget(url_input)
        hbox.addWidget(color_button)
        
        self.urlInputs.append((url_input, color_button))
        layout.addWidget(QLabel(f"Calendar URL {len(self.urlInputs)}:"))
        layout.addLayout(hbox)

    def init_color_buttons(self, layout):
        self.color_buttons = {}
        color_options = [
            ('widget_bg_color', 'Widget background'),
            ('widget_text_color', 'Widget text'),
            ('calendar_bg_color', 'Calendar background'),
            ('calendar_text_color', 'Calendar text'),
            ('selected_date_color', 'Selected date'),
            ('event_list_bg_color', 'Event list background'),
            ('event_list_text_color', 'Event list text')
        ]

        for color_key, color_name in color_options:
            button = QPushButton()
            button.setStyleSheet(f"background-color: {self.widget.config[color_key]};")
            button.clicked.connect(lambda _, k=color_key: self.choose_widget_color(k))
            layout.addWidget(QLabel(f"{color_name}:"))
            layout.addWidget(button)
            self.color_buttons[color_key] = button

    def choose_color(self, url_input, button):
        color = QColorDialog.getColor()
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()};")
            self.widget.config['colors'][url_input.text()] = color.name()

    def choose_widget_color(self, color_key):
        color = QColorDialog.getColor(QColor(self.widget.config[color_key]))
        if color.isValid():
            self.color_buttons[color_key].setStyleSheet(f"background-color: {color.name()};")
            self.widget.config[color_key] = color.name()

    def get_config(self):
        config = super().get_config()
        config.update({
            'ical_urls': [input.text() for input, _ in self.urlInputs if input.text()],
            'update_interval': self.update_interval_input.value() * 3600000,
            'num_events': self.num_events_input.value(),
            'date_format': self.date_format_combo.currentText(),
        })
        
        for url_input, color_button in self.urlInputs:
            url = url_input.text()
            if url:
                color = color_button.palette().button().color().name()
                config['colors'][url] = color

        for color_key, button in self.color_buttons.items():
            config[color_key] = button.palette().button().color().name()

        return config

# Important: The class must be named 'Widget' for the loader to recognize it
Widget = GoogleCalendarWidget