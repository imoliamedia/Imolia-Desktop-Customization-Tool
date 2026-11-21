import logging
import os
import tempfile
import unittest
from logging.handlers import RotatingFileHandler
from unittest import mock

from src.utils import logger as logger_module


class TestSetupLogger(unittest.TestCase):
    def setUp(self):
        self.appdata = tempfile.TemporaryDirectory()
        self.addCleanup(self.appdata.cleanup)
        patcher = mock.patch.dict(os.environ, {'APPDATA': self.appdata.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.logger = logging.getLogger('DesktopCustomizer')
        self._old_handlers = list(self.logger.handlers)
        self.logger.handlers.clear()
        self.addCleanup(self._restore_handlers)

    def _restore_handlers(self):
        for handler in list(self.logger.handlers):
            handler.close()
            self.logger.removeHandler(handler)
        for handler in self._old_handlers:
            self.logger.addHandler(handler)

    def test_log_file_rotates_instead_of_growing_forever(self):
        logger_module.setup_logger()
        file_handlers = [h for h in self.logger.handlers if isinstance(h, RotatingFileHandler)]
        self.assertEqual(len(file_handlers), 1)
        self.assertEqual(file_handlers[0].maxBytes, logger_module.LOG_MAX_BYTES)
        self.assertEqual(file_handlers[0].backupCount, logger_module.LOG_BACKUP_COUNT)

    def test_a_flood_of_errors_stays_within_the_size_limit(self):
        with mock.patch.object(logger_module, 'LOG_MAX_BYTES', 20_000):
            logger_module.setup_logger()
        for i in range(2000):
            self.logger.error(f"dezelfde fout, steeds weer {i}")
        log_dir = os.path.join(self.appdata.name, 'Imolia Desktop Customizer', 'logs')
        sizes = [os.path.getsize(os.path.join(log_dir, name)) for name in os.listdir(log_dir)]
        self.assertLessEqual(len(sizes), logger_module.LOG_BACKUP_COUNT + 1)
        self.assertLessEqual(max(sizes), 20_000)

    def test_calling_it_twice_does_not_duplicate_log_lines(self):
        logger_module.setup_logger()
        handlers_after_first = len(self.logger.handlers)
        logger_module.setup_logger()
        self.assertEqual(len(self.logger.handlers), handlers_after_first)

    def test_unicode_messages_do_not_break_the_file_handler(self):
        logger_module.setup_logger()
        self.logger.info("Geïnitialiseerd … en nog meer ✓")  # mag niet crashen op de codepage


if __name__ == '__main__':
    unittest.main()
