import importlib.util
import os
import types
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtWidgets import QApplication, QSpinBox

_app = QApplication.instance() or QApplication([])

_WIDGET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'widgets', 'system_monitor_widget', 'system_monitor_widget.py')
_spec = importlib.util.spec_from_file_location('system_monitor_widget_under_test', _WIDGET_FILE)
monitor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(monitor)


class TestSettingsDialog(unittest.TestCase):
    """De dialoog heeft een eenvoudige stand-in voor de widget nodig; een echte widget is niet nodig."""

    def setUp(self):
        self.widget = types.SimpleNamespace(config={'color': '#aa00ff', 'update_interval': 2500})
        self.dialog = monitor.SystemMonitorSettingsDialog(self.widget)
        self.addCleanup(self.dialog.deleteLater)

    def test_there_is_exactly_one_update_interval_field(self):
        # Eerder stond er ook een tweede veld (in seconden) dat genegeerd werd.
        self.assertEqual(len(self.dialog.findChildren(QSpinBox)), 1)

    def test_the_field_shows_the_current_interval_in_milliseconds(self):
        self.assertEqual(self.dialog.interval_spin.value(), 2500)

    def test_get_config_returns_the_interval_and_the_color(self):
        self.dialog.interval_spin.setValue(1500)
        self.assertEqual(self.dialog.get_config(), {'update_interval': 1500, 'color': '#aa00ff'})

    def test_saving_works_without_ever_touching_the_color_button(self):
        # Vroeger crashte opslaan met een AttributeError als het dialoog geen kleurknop had.
        self.assertEqual(self.dialog.get_config()['color'], '#aa00ff')


if __name__ == '__main__':
    unittest.main()
