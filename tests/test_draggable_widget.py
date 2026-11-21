import os
import threading
import time
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QApplication

from src.utils import draggable_widget
from src.utils.draggable_widget import DraggableWidget

_app = QApplication.instance() or QApplication([])


class RecordingWidget(DraggableWidget):
    """Kijkt zoals een echte widget: eigen save_config() die de config wegschrijft."""

    def __init__(self):
        super().__init__()
        self.writes = []

    def load_config(self):
        return {'position': (0, 0)}

    def save_config(self):
        self.writes.append(dict(self.config))


class ChildWidget(RecordingWidget):
    """Een widget dat save_config() van een andere widget uitbreidt."""

    def save_config(self):
        self.extra = True
        super().save_config()


def _pump(seconds):
    end = time.time() + seconds
    while time.time() < end:
        _app.processEvents()
        time.sleep(0.01)


class TestSavesAreBundled(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.widget = RecordingWidget()
        cls.addClassCleanup(cls.widget.close)

    def setUp(self):
        self.widget.flush_config()
        self.widget.writes.clear()
        self.widget.config = {'position': (0, 0)}

    def test_dragging_does_not_write_once_per_mouse_move(self):
        for x in range(300):  # zoals bij het slepen van een widget
            self.widget.config['position'] = (x, x)
            self.widget.save_config()
        self.assertEqual(self.widget.writes, [])  # nog niets naar schijf
        _pump(draggable_widget.SAVE_DELAY_MS / 1000 + 0.3)
        self.assertEqual(len(self.widget.writes), 1)

    def test_the_latest_state_is_what_gets_written(self):
        for x in range(50):
            self.widget.config['position'] = (x, x)
            self.widget.save_config()
        _pump(draggable_widget.SAVE_DELAY_MS / 1000 + 0.3)
        self.assertEqual(self.widget.writes[-1]['position'], (49, 49))

    def test_flush_writes_immediately_and_only_once(self):
        self.widget.save_config()
        self.widget.flush_config()
        self.assertEqual(len(self.widget.writes), 1)
        _pump(draggable_widget.SAVE_DELAY_MS / 1000 + 0.3)
        self.assertEqual(len(self.widget.writes), 1)

    def test_flush_without_pending_changes_writes_nothing(self):
        self.widget.flush_config()
        self.assertEqual(self.widget.writes, [])

    def test_saving_from_another_thread_is_written_directly(self):
        worker = threading.Thread(target=self.widget.save_config)
        worker.start()
        worker.join()
        self.assertEqual(len(self.widget.writes), 1)

    def test_app_quit_flushes_a_pending_change(self):
        self.widget.save_config()
        _app.aboutToQuit.emit()
        self.assertEqual(len(self.widget.writes), 1)


class TestClosingFlushes(unittest.TestCase):
    def test_closing_the_widget_writes_a_pending_change(self):
        widget = RecordingWidget()
        widget.save_config()
        self.assertEqual(widget.writes, [])
        widget.close()
        self.assertEqual(len(widget.writes), 1)


class TestSubclassing(unittest.TestCase):
    def test_a_widget_without_its_own_save_config_still_works(self):
        class Bare(DraggableWidget):
            pass
        bare = Bare()
        bare.save_config()  # de lege basisversie, mag niets doen en niet crashen
        bare.close()

    def test_extending_a_parent_save_config_does_not_loop_or_lose_the_write(self):
        widget = ChildWidget()
        widget.save_config()
        widget.flush_config()
        _pump(draggable_widget.SAVE_DELAY_MS / 1000 + 0.3)
        self.assertTrue(widget.extra)
        self.assertGreaterEqual(len(widget.writes), 1)
        self.assertLessEqual(len(widget.writes), 2)
        widget.close()


if __name__ == '__main__':
    unittest.main()
