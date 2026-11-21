import importlib.util
import os
import sys
import unittest
from unittest import mock

from src.utils.package_manager import LooseVersion, PackageManager


class TestLooseVersion(unittest.TestCase):
    def test_compares_numbers_numerically_not_as_text(self):
        self.assertTrue(LooseVersion('1.10') > LooseVersion('1.9'))
        self.assertTrue(LooseVersion('5.15.6') >= LooseVersion('5.15.0'))
        self.assertTrue(LooseVersion('7.2.2') > LooseVersion('7.2.1'))

    def test_equal_and_not_equal(self):
        self.assertEqual(LooseVersion('2.28.1'), LooseVersion('2.28.1'))
        self.assertNotEqual(LooseVersion('2.28.1'), LooseVersion('2.28.2'))

    def test_all_comparison_operators_used_by_the_package_manager(self):
        low, high = LooseVersion('1.2.3'), LooseVersion('1.2.4')
        self.assertTrue(low < high)
        self.assertTrue(low <= high)
        self.assertTrue(high > low)
        self.assertTrue(high >= low)
        self.assertFalse(high < low)

    def test_mixing_a_number_and_text_raises_like_distutils_did(self):
        # package_manager.py vangt dit af en gaat dan uit van "voldoet".
        with self.assertRaises(TypeError):
            LooseVersion('1.0') < LooseVersion('1.a')

    def test_the_module_loads_without_distutils(self):
        """Python 3.12 heeft geen distutils meer; zonder setuptools kon deze module niet laden."""
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'src', 'utils', 'package_manager.py')
        spec = importlib.util.spec_from_file_location('package_manager_without_distutils', path)
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {'distutils': None, 'distutils.version': None}):
            spec.loader.exec_module(module)
        self.assertTrue(module.LooseVersion('2.0') > module.LooseVersion('1.9'))


class TestParsePackageSpec(unittest.TestCase):
    """Test de spec-parser zonder een echte PackageManager te instantiëren
    (dat zou pip/embedded Python willen aanspreken en is niets voor een
    snelle, offline unit test)."""

    def _parse(self, spec):
        return PackageManager._parse_package_spec(None, spec)

    def test_plain_name_without_version(self):
        self.assertEqual(self._parse('requests'), ('requests', None, None))

    def test_exact_version(self):
        self.assertEqual(self._parse('requests==2.28.1'), ('requests', '==', '2.28.1'))

    def test_minimum_version(self):
        self.assertEqual(self._parse('PyQt5>=5.15.0'), ('PyQt5', '>=', '5.15.0'))

    def test_compatible_release(self):
        self.assertEqual(self._parse('icalendar~=5.0.7'), ('icalendar', '~=', '5.0.7'))

    def test_strips_whitespace(self):
        self.assertEqual(self._parse(' requests == 2.28.1 '), ('requests', '==', '2.28.1'))


class TestImportableInCurrentProcess(unittest.TestCase):
    """Test de kortsluit-check die voorkomt dat de app dependencies die al
    in het huidige (mogelijk gebundelde) proces beschikbaar zijn, alsnog
    via een los pip-subprocess probeert te (her)installeren."""

    def _check(self, package_name, operator=None, version=None):
        # __new__ i.p.v. PackageManager(...) om __init__ over te slaan: die
        # zou embedded Python/pip willen aanspreken, wat niets voor een
        # snelle, offline unit test is. De methode gebruikt verder alleen
        # het klasse-attribuut _IMPORT_NAME_OVERRIDES, geen instance state.
        instance = PackageManager.__new__(PackageManager)
        return instance._importable_in_current_process(package_name, operator, version)

    def test_stdlib_module_without_version_constraint_is_available(self):
        self.assertTrue(self._check('os'))

    def test_nonexistent_module_is_not_available(self):
        self.assertFalse(self._check('this_module_does_not_exist_xyz'))

    def test_import_name_override_for_pyqtwebengine(self):
        self.assertEqual(
            PackageManager._IMPORT_NAME_OVERRIDES['pyqtwebengine'],
            'PyQt5.QtWebEngineWidgets',
        )

    def test_hyphenated_package_name_is_normalized_for_import(self):
        # 'os-path' bestaat niet, maar de underscore-normalisatie mag geen
        # exception geven en moet netjes False teruggeven.
        self.assertFalse(self._check('does-not-exist-either'))


if __name__ == "__main__":
    unittest.main()
