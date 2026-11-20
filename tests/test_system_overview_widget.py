import importlib.util
import os
import unittest

_WIDGET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'widgets', 'system_overview_widget', 'system_overview_widget.py')

_spec = importlib.util.spec_from_file_location('system_overview_widget_under_test', _WIDGET_FILE)
overview = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(overview)


class TestParseNvidiaSmiLine(unittest.TestCase):
    def test_parses_all_fields(self):
        gpu = overview.parse_nvidia_smi_line('NVIDIA GeForce RTX 2070 SUPER, 8, 3871, 8192, 34, 26.49')
        self.assertEqual(gpu['name'], 'NVIDIA GeForce RTX 2070 SUPER')
        self.assertEqual(gpu['util'], 8.0)
        self.assertEqual(gpu['mem_total'], 8192.0)
        self.assertEqual(gpu['temp'], 34.0)
        self.assertEqual(gpu['power'], 26.49)

    def test_not_available_values_become_none(self):
        gpu = overview.parse_nvidia_smi_line('Some GPU, [N/A], 1, 2, [N/A], [N/A]')
        self.assertIsNone(gpu['util'])
        self.assertIsNone(gpu['temp'])
        self.assertIsNone(gpu['power'])

    def test_too_few_columns_returns_none(self):
        self.assertIsNone(overview.parse_nvidia_smi_line('garbage'))


class TestPickCpuTemperature(unittest.TestCase):
    SENSORS = [
        {'Name': 'CPU Core #1', 'Value': 50, 'Identifier': '/intelcpu/0/temperature/1'},
        {'Name': 'CPU Package', 'Value': 61.5, 'Identifier': '/intelcpu/0/temperature/4'},
        {'Name': 'GPU Core', 'Value': 80, 'Identifier': '/gpu-nvidia/0/temperature/0'},
    ]

    def test_prefers_package_sensor(self):
        self.assertEqual(overview.pick_cpu_temperature(self.SENSORS), 61.5)

    def test_falls_back_to_hottest_cpu_sensor(self):
        self.assertEqual(overview.pick_cpu_temperature(self.SENSORS[:1]), 50)

    def test_ignores_non_cpu_sensors(self):
        self.assertIsNone(overview.pick_cpu_temperature(self.SENSORS[2:]))


class TestFormatting(unittest.TestCase):
    def test_bits_per_second(self):
        self.assertEqual(overview.format_bits_per_second(125000), '1.0 Mbps')
        self.assertEqual(overview.format_bits_per_second(0), '0 bps')

    def test_bytes_per_second(self):
        self.assertEqual(overview.format_bytes_per_second(1024 * 1024), '1.0 MB/s')
        self.assertEqual(overview.format_bytes_per_second(10), '10 B/s')


class TestVirtualAdapterFilter(unittest.TestCase):
    def test_filters_virtual_adapters_only(self):
        for virtual in ('vEthernet (Default Switch)', 'Loopback Pseudo-Interface 1', 'VMware Network Adapter VMnet8'):
            self.assertTrue(overview.VIRTUAL_NIC_RE.search(virtual), virtual)
        for physical in ('Ethernet', 'Wi-Fi', 'Ethernet 2'):
            self.assertFalse(overview.VIRTUAL_NIC_RE.search(physical), physical)


if __name__ == '__main__':
    unittest.main()
