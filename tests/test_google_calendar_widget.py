import importlib.util
import os
import time
import unittest
from datetime import date, timedelta
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

_WIDGET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'widgets', 'google_calendar_widget', 'google_calendar_widget.py')
_spec = importlib.util.spec_from_file_location('google_calendar_widget_under_test', _WIDGET_FILE)
calendar_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calendar_module)

URL = 'http://example.invalid/test.ics'



def _ics(day):
    return ('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//test//EN\r\nBEGIN:VEVENT\r\nUID:1\r\n'
            f'DTSTAMP:20260101T000000Z\r\nDTSTART;VALUE=DATE:{day:%Y%m%d}\r\nSUMMARY:Test afspraak\r\n'
            'END:VEVENT\r\nEND:VCALENDAR\r\n')


def _response(text, status=200):
    return mock.Mock(status_code=status, text=text)


def _config():
    return {
        'ical_urls': [URL], 'colors': {}, 'update_interval': 3600000, 'num_events': 5,
        'widget_bg_color': '#FFFFFF', 'widget_text_color': '#000000', 'calendar_bg_color': '#F0F0F0',
        'calendar_text_color': '#000000', 'selected_date_color': '#3498DB',
        'event_list_bg_color': '#FFFFFF', 'event_list_text_color': '#000000',
        'date_format': 'dd/mm/yyyy', 'size': (400, 600), 'position': (100, 100),
    }


def _wait_until(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        _app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


class TestCalendarFetchesInTheBackground(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        patchers = [
            mock.patch.object(calendar_module.GoogleCalendarWidget, 'load_config', lambda self: _config()),
            mock.patch.object(calendar_module.GoogleCalendarWidget, 'save_config', lambda self: None),
            mock.patch.object(calendar_module.GoogleCalendarWidget, 'initialCalendarUpdate', lambda self: None),
        ]
        for patcher in patchers:
            patcher.start()
            cls.addClassCleanup(patcher.stop)
        # Eén widget voor alle tests: veel losse Qt-widgets aanmaken en weggooien terwijl er
        # achtergrondthreads draaien laat Qt in de testomgeving (offscreen) soms crashen.
        cls.widget = calendar_module.GoogleCalendarWidget()
        cls.addClassCleanup(cls.widget.close)

    def setUp(self):
        widget = self.widget
        _wait_until(lambda: not widget._fetching)
        widget.config['ical_urls'] = [URL]
        widget._events = None
        widget._fetching = False
        widget._refetch_requested = None
        widget.events_loaded = False
        widget.eventList.clear()

    def test_updating_does_not_block_the_ui_thread_on_a_slow_network(self):
        def slow_get(url, timeout=None):
            time.sleep(0.6)
            return _response(_ics(date.today() + timedelta(days=1)))

        with mock.patch.object(calendar_module.requests, 'get', side_effect=slow_get):
            started = time.time()
            self.widget.updateCalendar()
            self.assertLess(time.time() - started, 0.3)  # kwam eerder pas na de hele download terug
            self.assertTrue(_wait_until(lambda: self.widget._events is not None))
        self.assertEqual(len(self.widget._events), 1)
        self.assertTrue(self.widget.events_loaded)

    def test_a_failed_refresh_keeps_the_previously_loaded_events(self):
        old_events = ['eerder opgehaald']
        self.widget._events = old_events
        self.widget.events_loaded = True
        error = calendar_module.requests.exceptions.ConnectionError('geen internet')
        with mock.patch.object(calendar_module.requests, 'get', side_effect=error), \
                mock.patch.object(calendar_module.QMessageBox, 'warning') as warning:
            self.widget.updateCalendar(show_errors=False)
            self.assertTrue(_wait_until(lambda: not self.widget._fetching))
        self.assertEqual(self.widget._events, old_events)
        warning.assert_not_called()

    def test_a_failed_first_load_says_so_in_the_list(self):
        error = calendar_module.requests.exceptions.ConnectionError('geen internet')
        with mock.patch.object(calendar_module.requests, 'get', side_effect=error), \
                mock.patch.object(calendar_module.QTimer, 'singleShot'):
            self.widget.updateCalendar()
            self.assertTrue(_wait_until(lambda: not self.widget._fetching))
        self.assertIsNone(self.widget._events)
        self.assertFalse(self.widget.events_loaded)
        self.assertIn('Fout bij laden', self.widget.eventList.item(0).text())

    def test_errors_are_shown_when_the_user_asked_for_a_refresh(self):
        error = calendar_module.requests.exceptions.ConnectionError('geen internet')
        with mock.patch.object(calendar_module.requests, 'get', side_effect=error), \
                mock.patch.object(calendar_module.QTimer, 'singleShot'), \
                mock.patch.object(calendar_module.QMessageBox, 'warning') as warning:
            self.widget.updateCalendar(show_errors=True)
            self.assertTrue(_wait_until(lambda: warning.called))

    def test_picking_a_date_uses_the_cache_and_never_touches_the_network(self):
        self.widget._events = []
        with mock.patch.object(calendar_module.requests, 'get') as get:
            self.widget.updateEventList()
            self.widget.showUpcomingEvents()
        get.assert_not_called()

    def test_lists_say_loading_until_the_first_download_is_done(self):
        self.widget._events = None
        self.widget.showUpcomingEvents()
        self.assertEqual(self.widget.eventList.item(0).text(), 'Agenda gebeurtenissen laden...')

    def test_a_change_made_during_a_download_is_fetched_afterwards(self):
        calls = []

        def slow_get(url, timeout=None):
            calls.append(url)
            time.sleep(0.3)
            return _response(_ics(date.today() + timedelta(days=1)))

        with mock.patch.object(calendar_module.requests, 'get', side_effect=slow_get):
            self.widget.updateCalendar()
            self.widget.updateCalendar()  # tweede verzoek terwijl de eerste download nog loopt
            self.assertTrue(_wait_until(lambda: len(calls) == 2 and not self.widget._fetching))
        self.assertEqual(len(calls), 2)

    def test_no_urls_means_nothing_to_do(self):
        self.widget.config['ical_urls'] = []
        with mock.patch.object(calendar_module.requests, 'get') as get:
            self.assertFalse(self.widget.updateCalendar())
        get.assert_not_called()


if __name__ == '__main__':
    unittest.main()
