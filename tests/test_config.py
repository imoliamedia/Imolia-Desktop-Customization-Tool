import unittest

from src.config import APP_NAME, WIDGETS_FOLDER_NAME


class TestConfig(unittest.TestCase):
    def test_app_name_is_set(self):
        self.assertTrue(APP_NAME)
        self.assertIsInstance(APP_NAME, str)

    def test_widgets_folder_name_derived_from_app_name(self):
        self.assertTrue(WIDGETS_FOLDER_NAME.startswith(APP_NAME))
        self.assertIn("Widgets", WIDGETS_FOLDER_NAME)


if __name__ == "__main__":
    unittest.main()
