# Copyright (C) 2026 Imolia Media
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
System Overview Widget for Imolia Desktop Customizer

Toont CPU, geheugen, GPU, GPU-geheugen, netwerk en schijf tegelijk, elk met
een live grafiek - zoals Windows Taakbeheer, maar alles in één overzicht.

Dependencies:
PyQt5==5.15.6
psutil==7.2.2

"""

import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import deque

import psutil
from PyQt5.QtCore import Qt, QObject, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import (QBrush, QColor, QFont, QFontMetrics, QLinearGradient,
                         QPainter, QPainterPath, QPen)
from PyQt5.QtWidgets import (QCheckBox, QColorDialog, QDoubleSpinBox, QGroupBox,
                             QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout)
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

logger = logging.getLogger('DesktopCustomizer.SystemOverviewWidget')

# Voorkomt dat er voor elke nvidia-smi / powershell aanroep een console-venster oplicht.
CREATE_NO_WINDOW = 0x08000000 if sys.platform == 'win32' else 0

# De echte systeemschijf (meestal C:), niet de schijf van de huidige werkmap.
SYSTEM_DRIVE_PATH = (os.environ.get('SystemDrive', 'C:') + os.sep
                     if sys.platform == 'win32' else os.path.abspath(os.sep))

# Virtuele adapters (Hyper-V, VMware, VPN, ...) horen niet bij "het netwerk van de pc".
VIRTUAL_NIC_RE = re.compile(
    r'loopback|pseudo|vethernet|virtual|vmware|vbox|hyper-v|bluetooth|'
    r'tailscale|zerotier|wsl|docker|tap-|\btun\b', re.IGNORECASE)

# (sleutel, titel, accentkleur)
PANELS = [
    ('cpu', 'CPU', '#4aa3ff'),
    ('ram', 'Geheugen', '#b36bff'),
    ('gpu', 'GPU', '#3ddc84'),
    ('vram', 'GPU-geheugen', '#2ec4b6'),
    ('net', 'Netwerk', '#ff9f43'),
    ('disk', 'Schijf', '#ffd84a'),
]
SECONDARY_COLOR = '#ff6b81'  # tweede lijn in grafieken met twee reeksen (upload / schrijven)

DEFAULT_CONFIG = {
    'color': '#ffffff',
    'update_interval': 1.0,      # seconden
    'history_points': 60,        # aantal meetpunten in de grafieken
    'columns': 3,
    'bg_opacity': 60,            # procent
    'size': (640, 340),
    'position': (100, 100),
    'show_cpu': True,
    'show_ram': True,
    'show_gpu': True,
    'show_vram': True,
    'show_net': True,
    'show_disk': True,
}

TEMP_WARN = 75
TEMP_HOT = 85


def config_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system_overview_widget_config.json')


# --------------------------------------------------------------------------
# Hulpfuncties
# --------------------------------------------------------------------------

def format_bits_per_second(bytes_per_second):
    bits = bytes_per_second * 8
    for unit, divisor in (('Gbps', 1e9), ('Mbps', 1e6), ('Kbps', 1e3)):
        if bits >= divisor:
            return f"{bits / divisor:.1f} {unit}"
    return f"{bits:.0f} bps"


def format_bytes_per_second(bytes_per_second):
    for unit, divisor in (('GB/s', 1024 ** 3), ('MB/s', 1024 ** 2), ('KB/s', 1024)):
        if bytes_per_second >= divisor:
            return f"{bytes_per_second / divisor:.1f} {unit}"
    return f"{bytes_per_second:.0f} B/s"


def _to_float(text):
    """nvidia-smi geeft '[N/A]' of 'N/A' voor waarden die de kaart niet kent."""
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def find_nvidia_smi():
    candidates = [
        shutil.which('nvidia-smi'),
        os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', 'nvidia-smi.exe'),
        os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'),
                     'NVIDIA Corporation', 'NVSMI', 'nvidia-smi.exe'),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def parse_nvidia_smi_line(line):
    """Zet één regel van `nvidia-smi --query-gpu=name,utilization.gpu,memory.used,
    memory.total,temperature.gpu,power.draw --format=csv,noheader,nounits` om in een dict."""
    parts = [p.strip() for p in line.split(',')]
    if len(parts) < 6:
        return None
    return {
        'name': parts[0],
        'util': _to_float(parts[1]),
        'mem_used': _to_float(parts[2]),    # MiB
        'mem_total': _to_float(parts[3]),   # MiB
        'temp': _to_float(parts[4]),
        'power': _to_float(parts[5]),
    }


def pick_cpu_temperature(sensors):
    """Kies de CPU-temperatuur uit de sensorlijst van LibreHardwareMonitor /
    OpenHardwareMonitor (lijst van dicts met 'Name', 'Value', 'Identifier')."""
    cpu_sensors = [s for s in sensors
                   if re.match(r'^/(intelcpu|amdcpu)/', str(s.get('Identifier', '')), re.IGNORECASE)
                   and _to_float(s.get('Value')) is not None]
    if not cpu_sensors:
        return None
    for s in cpu_sensors:
        if re.search(r'package|tctl|tdie', str(s.get('Name', '')), re.IGNORECASE):
            return _to_float(s['Value'])
    return max(_to_float(s['Value']) for s in cpu_sensors)


# Windows geeft CPU-temperatuur niet vrij aan gewone programma's. Alleen als
# één van deze monitoringprogramma's draait, kan de widget de waarde via hun
# WMI-interface overnemen.
TEMP_PROVIDERS = {
    'librehardwaremonitor.exe': 'root/LibreHardwareMonitor',
    'openhardwaremonitor.exe': 'root/OpenHardwareMonitor',
}


# --------------------------------------------------------------------------
# Metingen (draait in een eigen thread, zodat de desktop nooit haperen)
# --------------------------------------------------------------------------

class SampleBridge(QObject):
    sampled = pyqtSignal(dict)


class StatsSampler(threading.Thread):
    def __init__(self, interval, emit):
        super().__init__(name='SystemOverviewSampler', daemon=True)
        self.interval = max(0.25, float(interval))
        self._emit = emit
        self._stop_event = threading.Event()
        self._smi = find_nvidia_smi()
        self._cpu_temp = None
        self._next_temp_poll = 0.0
        self._prev_time = None
        self._prev_net = {}
        self._prev_disk = None

    def stop(self):
        self._stop_event.set()

    def run(self):
        psutil.cpu_percent(None)  # eerste aanroep geeft altijd 0 - alleen als referentie
        self._prev_time = time.monotonic()
        self._prev_net = self._net_counters()[0]
        self._prev_disk = psutil.disk_io_counters()
        while not self._stop_event.wait(self.interval):
            try:
                sample = self._collect()
            except Exception:
                logger.exception("Fout bij het meten van systeemgegevens")
                continue
            if not self._stop_event.is_set():
                self._emit(sample)

    # -- netwerk ----------------------------------------------------------

    def _net_counters(self):
        """Tellers van alle actieve, fysieke adapters + naam/snelheid voor weergave."""
        stats = psutil.net_if_stats()
        io = psutil.net_io_counters(pernic=True)
        names = [n for n, s in stats.items()
                 if s.isup and n in io and not VIRTUAL_NIC_RE.search(n)]
        counters = {n: (io[n].bytes_recv, io[n].bytes_sent) for n in names}
        label = ' + '.join(names[:2]) if names else 'Geen verbinding'
        speed = max((stats[n].speed for n in names), default=0)
        return counters, label, speed

    # -- GPU --------------------------------------------------------------

    def _read_gpu(self):
        if not self._smi:
            return None
        try:
            result = subprocess.run(
                [self._smi,
                 '--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=3, creationflags=CREATE_NO_WINDOW)
            lines = result.stdout.strip().splitlines()
            return parse_nvidia_smi_line(lines[0]) if lines else None
        except Exception as e:
            logger.debug(f"nvidia-smi mislukt: {e}")
            return None

    # -- CPU-temperatuur (optioneel) ---------------------------------------

    def _poll_cpu_temp(self, now):
        if now < self._next_temp_poll:
            return self._cpu_temp
        self._next_temp_poll = now + 5.0
        namespace = None
        try:
            for proc in psutil.process_iter(['name']):
                key = (proc.info.get('name') or '').lower()
                if key in TEMP_PROVIDERS:
                    namespace = TEMP_PROVIDERS[key]
                    break
        except Exception:
            pass
        if not namespace:
            self._cpu_temp = None
            return None
        try:
            command = (f"Get-CimInstance -Namespace {namespace} -ClassName Sensor "
                       f"-Filter \"SensorType='Temperature'\" | "
                       f"Select-Object Name,Value,Identifier | ConvertTo-Json -Compress")
            result = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', command],
                capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
            data = json.loads(result.stdout) if result.stdout.strip() else []
            if isinstance(data, dict):  # ConvertTo-Json maakt van één item een los object
                data = [data]
            self._cpu_temp = pick_cpu_temperature(data)
        except Exception as e:
            logger.debug(f"CPU-temperatuur uitlezen mislukt: {e}")
            self._cpu_temp = None
        return self._cpu_temp

    # -- alles samen ------------------------------------------------------

    def _collect(self):
        now = time.monotonic()
        dt = max(now - self._prev_time, 0.001)
        self._prev_time = now

        vm = psutil.virtual_memory()
        sample = {
            'cpu': psutil.cpu_percent(None),
            'ram_percent': vm.percent,
            'ram_used': vm.used,
            'ram_total': vm.total,
            'swap_percent': psutil.swap_memory().percent,
        }

        counters, label, speed = self._net_counters()
        down = up = 0.0
        for name, (recv, sent) in counters.items():
            if name in self._prev_net:  # adapter die net verschenen is, telt pas vanaf de volgende meting
                prev_recv, prev_sent = self._prev_net[name]
                down += max(0, recv - prev_recv)
                up += max(0, sent - prev_sent)
        self._prev_net = counters
        sample.update(net_down=down / dt, net_up=up / dt, net_label=label, net_speed=speed)

        disk = psutil.disk_io_counters()
        read = write = 0.0
        if disk and self._prev_disk:
            read = max(0, disk.read_bytes - self._prev_disk.read_bytes) / dt
            write = max(0, disk.write_bytes - self._prev_disk.write_bytes) / dt
        self._prev_disk = disk
        try:
            disk_used = psutil.disk_usage(SYSTEM_DRIVE_PATH).percent
        except Exception:
            disk_used = None
        sample.update(disk_read=read, disk_write=write, disk_used=disk_used)

        sample['gpu'] = self._read_gpu()
        sample['cpu_temp'] = self._poll_cpu_temp(now)
        return sample


# --------------------------------------------------------------------------
# De widget
# --------------------------------------------------------------------------

class SystemOverviewWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.latest = {}
        self.history = {}
        self._build_history()

        self.setMinimumSize(300, 170)
        self.resize(*self.config['size'])
        self.move(*self.config['position'])

        self.bridge = SampleBridge(self)
        self.bridge.sampled.connect(self.on_sample)
        self.sampler = None
        self._start_sampler()

    # -- configuratie -----------------------------------------------------

    def load_config(self):
        config = dict(DEFAULT_CONFIG)
        try:
            if os.path.exists(config_path()):
                with open(config_path(), 'r') as f:
                    config.update(json.load(f))
        except (OSError, ValueError) as e:
            logger.error(f"Kon configuratie van System Overview niet lezen: {e}")
        return config

    def save_config(self):
        try:
            with open(config_path(), 'w') as f:
                json.dump(self.config, f)
        except OSError as e:
            logger.error(f"Kon configuratie van System Overview niet opslaan: {e}")

    def updateConfig(self, new_config):
        interval_changed = new_config.get('update_interval') != self.config.get('update_interval')
        self.config.update(new_config)
        self._build_history()
        if interval_changed:
            self._start_sampler()
        self.update()
        self.save_config()

    def openSettings(self):
        dialog = SystemOverviewSettingsDialog(self)
        if dialog.exec_():
            self.updateConfig(dialog.get_config())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

    # -- metingen ontvangen -----------------------------------------------

    @property
    def history_len(self):
        return max(10, int(self.config.get('history_points', 60)))

    def _build_history(self):
        size = self.history_len
        old = self.history
        self.history = {
            key: deque(old.get(key, ()), maxlen=size)
            for key in ('cpu', 'ram', 'gpu', 'vram', 'net_down', 'net_up', 'disk_read', 'disk_write')
        }

    def _start_sampler(self):
        if self.sampler:
            self.sampler.stop()
        self.sampler = StatsSampler(self.config.get('update_interval', 1.0), self.bridge.sampled.emit)
        self.sampler.start()

    def closeEvent(self, event):
        if self.sampler:
            self.sampler.stop()
            self.sampler = None
        super().closeEvent(event)

    def on_sample(self, sample):
        self.latest = sample
        h = self.history
        h['cpu'].append(sample['cpu'])
        h['ram'].append(sample['ram_percent'])
        h['net_down'].append(sample['net_down'])
        h['net_up'].append(sample['net_up'])
        h['disk_read'].append(sample['disk_read'])
        h['disk_write'].append(sample['disk_write'])
        gpu = sample.get('gpu')
        if gpu:
            h['gpu'].append(gpu['util'] or 0)
            if gpu['mem_total']:
                h['vram'].append((gpu['mem_used'] or 0) / gpu['mem_total'] * 100)
        self.update()

    # -- inhoud per paneel ------------------------------------------------

    def _panel_content(self, key):
        s = self.latest
        dim = None  # None = standaard gedempte tekstkleur
        accent = QColor(next(p[2] for p in PANELS if p[0] == key))
        title = next(p[1] for p in PANELS if p[0] == key)
        content = {'title': title, 'accent': accent, 'value': '–', 'lines': [], 'series': [], 'vmax': 100.0}

        if key == 'cpu':
            content['series'] = [(self.history['cpu'], accent)]
            if s:
                content['value'] = f"{s['cpu']:.0f}%"
            physical = psutil.cpu_count(logical=False)
            logical = psutil.cpu_count(logical=True)
            content['lines'].append((f"{physical} kernen · {logical} threads", dim))
            if s.get('cpu_temp') is not None:
                content['lines'].append((f"{s['cpu_temp']:.0f} °C", self._temp_color(s['cpu_temp'])))

        elif key == 'ram':
            content['series'] = [(self.history['ram'], accent)]
            if s:
                content['value'] = f"{s['ram_percent']:.0f}%"
                gib = 1024 ** 3
                content['lines'].append((f"{s['ram_used'] / gib:.1f} / {s['ram_total'] / gib:.1f} GB", dim))
                content['lines'].append((f"Wisselbestand {s['swap_percent']:.0f}%", dim))

        elif key == 'gpu':
            content['series'] = [(self.history['gpu'], accent)]
            gpu = s.get('gpu') if s else None
            if gpu:
                content['value'] = f"{(gpu['util'] or 0):.0f}%"
                content['lines'].append((re.sub(r'^NVIDIA\s+', '', gpu['name']), dim))
                parts = []
                if gpu['temp'] is not None:
                    parts.append(f"{gpu['temp']:.0f} °C")
                if gpu['power'] is not None:
                    parts.append(f"{gpu['power']:.0f} W")
                if parts:
                    content['lines'].append((' · '.join(parts), self._temp_color(gpu['temp'])))
            elif s:
                content['value'] = 'n.v.t.'
                content['lines'].append(('Geen NVIDIA-GPU gevonden', dim))

        elif key == 'vram':
            content['series'] = [(self.history['vram'], accent)]
            gpu = s.get('gpu') if s else None
            if gpu and gpu['mem_total']:
                content['value'] = f"{gpu['mem_used'] / gpu['mem_total'] * 100:.0f}%"
                content['lines'].append((f"{gpu['mem_used'] / 1024:.1f} / {gpu['mem_total'] / 1024:.1f} GB", dim))
            elif s:
                content['value'] = 'n.v.t.'

        elif key == 'net':
            secondary = QColor(SECONDARY_COLOR)
            content['series'] = [(self.history['net_down'], accent), (self.history['net_up'], secondary)]
            content['vmax'] = None
            content['floor'] = 125_000  # 1 Mbps, zodat een stille lijn niet vol schaal lijkt
            if s:
                content['title'] = s['net_label']
                content['value'] = format_bits_per_second(s['net_down'] + s['net_up'])
                content['lines'].append((f"↓ {format_bits_per_second(s['net_down'])}", accent))
                content['lines'].append((f"↑ {format_bits_per_second(s['net_up'])}", secondary))
                if s['net_speed']:
                    content['lines'].append((f"Verbinding {s['net_speed']:.0f} Mbps", dim))

        elif key == 'disk':
            secondary = QColor(SECONDARY_COLOR)
            content['series'] = [(self.history['disk_read'], accent), (self.history['disk_write'], secondary)]
            content['vmax'] = None
            content['floor'] = 1024 * 1024  # 1 MB/s
            if s:
                content['value'] = format_bytes_per_second(s['disk_read'] + s['disk_write'])
                content['lines'].append((f"↓ lezen {format_bytes_per_second(s['disk_read'])}", accent))
                content['lines'].append((f"↑ schrijven {format_bytes_per_second(s['disk_write'])}", secondary))
                if s['disk_used'] is not None:
                    drive = os.path.splitdrive(SYSTEM_DRIVE_PATH)[0] or SYSTEM_DRIVE_PATH
                    content['lines'].append((f"{drive} {s['disk_used']:.0f}% vol", dim))

        return content

    @staticmethod
    def _temp_color(temp):
        if temp is None:
            return None
        if temp >= TEMP_HOT:
            return QColor('#ff5252')
        if temp >= TEMP_WARN:
            return QColor('#ffb142')
        return None

    # -- tekenen ----------------------------------------------------------

    def _enabled_panels(self):
        return [p[0] for p in PANELS if self.config.get(f'show_{p[0]}', True)]

    def _cell_rects(self, keys, area, gap=8.0):
        """Verdeel `area` in een raster; een onvolledige laatste rij wordt over de volle breedte uitgerekt."""
        if not keys:
            return []
        cols = max(1, min(int(self.config.get('columns', 3)), len(keys)))
        rows = math.ceil(len(keys) / cols)
        cell_h = (area.height() - gap * (rows - 1)) / rows
        rects = []
        index = 0
        for row in range(rows):
            in_row = min(cols, len(keys) - index)
            cell_w = (area.width() - gap * (in_row - 1)) / in_row
            for col in range(in_row):
                rects.append(QRectF(area.left() + col * (cell_w + gap),
                                    area.top() + row * (cell_h + gap), cell_w, cell_h))
            index += in_row
        return rects

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        alpha = int(max(10, min(100, self.config.get('bg_opacity', 60))) / 100 * 255)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(14, 16, 22, alpha))
        painter.drawRoundedRect(QRectF(self.rect()), 12, 12)

        keys = self._enabled_panels()
        area = QRectF(self.rect()).adjusted(10, 10, -10, -10)
        for key, rect in zip(keys, self._cell_rects(keys, area)):
            self._draw_panel(painter, rect, self._panel_content(key))
        painter.end()

        super().paintEvent(event)  # tekent het greepje rechtsonder om te schalen

    def _draw_panel(self, painter, rect, content):
        text_color = QColor(self.config.get('color', '#ffffff'))
        dim_color = QColor(text_color)
        dim_color.setAlpha(150)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 16))
        painter.drawRoundedRect(rect, 8, 8)

        inner = rect.adjusted(9, 7, -9, -8)
        base = max(9.0, min(15.0, rect.height() * 0.085))

        title_font = QFont('Segoe UI')
        title_font.setPixelSize(int(base))
        title_font.setBold(True)
        value_font = QFont('Segoe UI')
        value_font.setPixelSize(int(base * 1.5))
        value_font.setBold(True)
        line_font = QFont('Segoe UI')
        line_font.setPixelSize(max(8, int(base * 0.9)))

        value_fm = QFontMetrics(value_font)
        header_h = value_fm.height()
        value_w = value_fm.horizontalAdvance(content['value'])

        painter.setFont(value_font)
        painter.setPen(text_color)
        painter.drawText(QRectF(inner.left(), inner.top(), inner.width(), header_h),
                         Qt.AlignRight | Qt.AlignVCenter, content['value'])

        title_fm = QFontMetrics(title_font)
        title = title_fm.elidedText(content['title'], Qt.ElideRight, max(10, int(inner.width() - value_w - 8)))
        painter.setFont(title_font)
        painter.setPen(content['accent'])
        painter.drawText(QRectF(inner.left(), inner.top(), inner.width(), header_h),
                         Qt.AlignLeft | Qt.AlignVCenter, title)

        y = inner.top() + header_h + 1
        line_fm = QFontMetrics(line_font)
        min_graph_h = 30
        painter.setFont(line_font)
        for text, color in content['lines']:
            if y + line_fm.height() > inner.bottom() - min_graph_h:
                break  # past niet meer naast een bruikbare grafiek
            painter.setPen(color or dim_color)
            elided = line_fm.elidedText(text, Qt.ElideRight, int(inner.width()))
            painter.drawText(QRectF(inner.left(), y, inner.width(), line_fm.height()),
                             Qt.AlignLeft | Qt.AlignVCenter, elided)
            y += line_fm.height()

        graph = QRectF(inner.left(), y + 3, inner.width(), inner.bottom() - y - 3)
        if graph.height() >= 16:
            self._draw_graph(painter, graph, content)

    def _draw_graph(self, painter, rect, content):
        # achtergrond en rasterlijnen
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 70))
        painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(QPen(QColor(255, 255, 255, 22), 1))
        for fraction in (0.25, 0.5, 0.75):
            y = rect.top() + rect.height() * fraction
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

        vmax = content['vmax']
        if vmax is None:  # automatische schaal voor snelheden
            peak = max((max(series, default=0) for series, _ in content['series']), default=0)
            vmax = max(peak * 1.15, content.get('floor', 1))

        painter.save()
        painter.setClipRect(rect.adjusted(0, -2, 0, 2))
        for series, color in content['series']:
            self._draw_series(painter, rect, series, vmax, color)
        painter.restore()

    def _draw_series(self, painter, rect, values, vmax, color):
        if len(values) < 2:
            return
        total = self.history_len
        offset = total - len(values)
        points = []
        for i, value in enumerate(values):
            x = rect.left() + (offset + i) / (total - 1) * rect.width()
            y = rect.bottom() - min(max(value / vmax, 0.0), 1.0) * rect.height()
            points.append(QPointF(x, y))

        line = QPainterPath(points[0])
        for point in points[1:]:
            line.lineTo(point)

        fill = QPainterPath(line)
        fill.lineTo(points[-1].x(), rect.bottom())
        fill.lineTo(points[0].x(), rect.bottom())
        fill.closeSubpath()
        top = QColor(color)
        top.setAlpha(100)
        bottom = QColor(color)
        bottom.setAlpha(8)
        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        gradient.setColorAt(0, top)
        gradient.setColorAt(1, bottom)
        painter.fillPath(fill, QBrush(gradient))

        painter.setPen(QPen(color, 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(line)


class SystemOverviewSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def add_behavior_section(self, layout):
        # Eigen versie: de standaard sectie rekent in hele seconden, terwijl
        # een overzicht met grafieken juist baat heeft bij een halve seconde.
        group = QGroupBox("Gedrag")
        group_layout = QVBoxLayout()
        config = self.widget.config

        row = QHBoxLayout()
        row.addWidget(QLabel("Verversen elke:"))
        self.update_interval = QDoubleSpinBox()
        self.update_interval.setRange(0.5, 10.0)
        self.update_interval.setSingleStep(0.5)
        self.update_interval.setSuffix(" s")
        self.update_interval.setValue(float(config.get('update_interval', 1.0)))
        row.addWidget(self.update_interval)
        group_layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Geschiedenis in grafiek (meetpunten):"))
        self.history_points = QSpinBox()
        self.history_points.setRange(10, 600)
        self.history_points.setSingleStep(10)
        self.history_points.setValue(int(config.get('history_points', 60)))
        row.addWidget(self.history_points)
        group_layout.addLayout(row)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def add_custom_section(self, layout):
        config = self.widget.config

        panels_group = QGroupBox("Getoonde onderdelen")
        panels_layout = QVBoxLayout()
        self.panel_checks = {}
        for key, title, _ in PANELS:
            check = QCheckBox(title)
            check.setChecked(bool(config.get(f'show_{key}', True)))
            self.panel_checks[key] = check
            panels_layout.addWidget(check)
        panels_group.setLayout(panels_layout)
        layout.addWidget(panels_group)

        look_group = QGroupBox("Uiterlijk")
        look_layout = QVBoxLayout()

        row = QHBoxLayout()
        row.addWidget(QLabel("Kolommen:"))
        self.columns = QSpinBox()
        self.columns.setRange(1, 6)
        self.columns.setValue(int(config.get('columns', 3)))
        row.addWidget(self.columns)
        look_layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Achtergrond dekking (%):"))
        self.bg_opacity = QSpinBox()
        self.bg_opacity.setRange(10, 100)
        self.bg_opacity.setValue(int(config.get('bg_opacity', 60)))
        row.addWidget(self.bg_opacity)
        look_layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Tekstkleur:"))
        self.color_button = QPushButton()
        self.color_button.setStyleSheet(f"background-color: {config.get('color', '#ffffff')};")
        self.color_button.clicked.connect(self.choose_color)
        row.addWidget(self.color_button)
        look_layout.addLayout(row)

        look_group.setLayout(look_layout)
        layout.addWidget(look_group)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.widget.config.get('color', '#ffffff')))
        if color.isValid():
            self.color_button.setStyleSheet(f"background-color: {color.name()};")
            self.widget.config['color'] = color.name()

    def get_config(self):
        # Bewust zonder super().get_config(): die leest de kleur uit de
        # QPalette van de knop, wat na setStyleSheet() de verkeerde waarde geeft.
        config = {
            'update_interval': self.update_interval.value(),
            'history_points': self.history_points.value(),
            'columns': self.columns.value(),
            'bg_opacity': self.bg_opacity.value(),
            'color': self.widget.config.get('color', '#ffffff'),
        }
        for key, check in self.panel_checks.items():
            config[f'show_{key}'] = check.isChecked()
        return config


# Important: The class must be named 'Widget' for the loader to recognize it
Widget = SystemOverviewWidget

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())
