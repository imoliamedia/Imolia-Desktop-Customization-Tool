import unittest
import os
import json
from src.utils.settings import Settings

class TestSettings(unittest.TestCase):
    def setUp(self):
        self.test_filename = 'test_settings.json'
        self.settings = Settings(self.test_filename)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_set_and_get(self):
        self.settings.set('test_key', 'test_value')
        self.assertEqual(self.settings.get('test_key'), 'test_value')

    def test_save_and_load(self):
        self.settings.set('test_key', 'test_value')
        self.settings.save()

        new_settings = Settings(self.test_filename)
        self.assertEqual(new_settings.get('test_key'), 'test_value')

    def test_default_value(self):
        self.assertEqual(self.settings.get('non_existent_key', 'default'), 'default')

if __name__ == '__main__':
    unittest.main()