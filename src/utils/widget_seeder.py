# Copyright (C) 2024 Imolia Media
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

import logging
import os
import re
import shutil
import sys

logger = logging.getLogger('DesktopCustomizer.WidgetSeeder')

_WIDGET_ENTRY_POINT_RE = re.compile(r'Widget\s*=\s*\w+')


def find_bundled_widgets_dir():
    """Zoek de map met de meegeleverde standaard-widgets.

    Werkt zowel vanuit source (de 'widgets'-map naast main.py) als vanuit
    een PyInstaller-executable, waar diezelfde map als data is meegebouwd
    (naast de exe in een onedir-build, of onder sys._MEIPASS in een
    onefile-build).

    Returns:
        str or None: pad naar de widgets-bronmap, of None als die nergens
        gevonden kon worden.
    """
    candidates = []

    if getattr(sys, 'frozen', False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), 'widgets'))
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidates.append(os.path.join(meipass, 'widgets'))
    else:
        # src/utils/widget_seeder.py -> projectroot/widgets
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidates.append(os.path.join(project_root, 'widgets'))

    for candidate in candidates:
        if os.path.isdir(candidate):
            return candidate

    return None


def _looks_like_widget_file(file_path):
    """Zelfde check als WidgetManager.is_valid_widget_file, hier los
    gehouden om geen afhankelijkheid richting widget_loader.py nodig te
    hebben (die op zijn beurt PyQt5 importeert)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return bool(_WIDGET_ENTRY_POINT_RE.search(f.read()))
    except OSError:
        return False


def seed_default_widgets(target_dir):
    """Kopieer de meegeleverde standaard-widgets naar de widgetmap van de gebruiker.

    Zonder dit blijft de widgetmap (standaard
    ~/Documents/Imolia Desktop Customizer Widgets) op een verse installatie
    volledig leeg, waardoor geen enkele standaard-widget ooit verschijnt -
    ook niet als hij in de instellingen als actief staat gemarkeerd.

    Bestaande bestanden in de doelmap worden nooit overschreven, zodat
    aanpassingen van de gebruiker aan een widget-bestand behouden blijven.

    Args:
        target_dir (str): De (al bestaande) widgetmap van de gebruiker.

    Returns:
        list: Bestandsnamen (zonder extensie) van widgets die zijn toegevoegd.
    """
    source_dir = find_bundled_widgets_dir()
    if not source_dir:
        logger.warning("Geen meegeleverde widgets-map gevonden om te seeden")
        return []

    seeded = []
    try:
        for entry in sorted(os.listdir(source_dir)):
            widget_source_dir = os.path.join(source_dir, entry)
            if not os.path.isdir(widget_source_dir):
                continue

            for filename in os.listdir(widget_source_dir):
                if not filename.endswith('.py'):
                    continue

                file_path = os.path.join(widget_source_dir, filename)
                target_path = os.path.join(target_dir, filename)

                if os.path.exists(target_path):
                    continue  # nooit een bestaand (mogelijk aangepast) bestand overschrijven

                if not _looks_like_widget_file(file_path):
                    continue

                try:
                    shutil.copyfile(file_path, target_path)
                    seeded.append(os.path.splitext(filename)[0])
                    logger.info(f"Standaard-widget geïnstalleerd: {filename}")
                except OSError as e:
                    logger.error(f"Kon widget {filename} niet kopiëren naar {target_path}: {e}")
    except OSError as e:
        logger.error(f"Fout bij het seeden van standaard-widgets vanuit {source_dir}: {e}")

    return seeded
