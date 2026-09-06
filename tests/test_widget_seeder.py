import os
import tempfile
import unittest

from src.utils.widget_seeder import find_bundled_widgets_dir, seed_default_widgets


class TestFindBundledWidgetsDir(unittest.TestCase):
    def test_finds_the_projects_widgets_folder_when_run_from_source(self):
        source_dir = find_bundled_widgets_dir()
        self.assertIsNotNone(source_dir)
        self.assertTrue(os.path.isdir(source_dir))
        # Een bekende, meegeleverde widget-submap moet erin zitten.
        self.assertIn('clock_widget', os.listdir(source_dir))


class TestSeedDefaultWidgets(unittest.TestCase):
    def setUp(self):
        self.target_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.target_dir.cleanup)

    def test_copies_bundled_widgets_into_empty_target(self):
        seeded = seed_default_widgets(self.target_dir.name)

        self.assertIn('clock_widget', seeded)
        self.assertIn('calculator', seeded)
        self.assertTrue(os.path.exists(os.path.join(self.target_dir.name, 'clock_widget.py')))

    def test_does_not_overwrite_existing_widget_file(self):
        target_path = os.path.join(self.target_dir.name, 'clock_widget.py')
        with open(target_path, 'w') as f:
            f.write("# aangepaste versie van de gebruiker\nWidget = Something\n")

        seed_default_widgets(self.target_dir.name)

        with open(target_path) as f:
            content = f.read()
        self.assertIn('aangepaste versie van de gebruiker', content)

    def test_running_twice_is_idempotent(self):
        first = seed_default_widgets(self.target_dir.name)
        second = seed_default_widgets(self.target_dir.name)

        self.assertTrue(first)
        self.assertEqual(second, [])


if __name__ == "__main__":
    unittest.main()
