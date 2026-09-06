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

import json
import os
import sys
import shutil
import logging

logger = logging.getLogger('DesktopCustomizer.Settings')


def _legacy_settings_paths():
    """Mogelijke locaties van settings.json uit oudere versies (relatief pad)."""
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), 'settings.json'))
    candidates.append(os.path.join(os.getcwd(), 'settings.json'))
    return candidates


def _default_settings_path():
    """Bepaal een schrijfbaar, pc-onafhankelijk pad voor settings.json.

    Gebruikt %APPDATA%\\Imolia Desktop Customizer\\settings.json zodat de
    locatie niet afhangt van de working directory waarmee de app gestart
    wordt (snelkoppeling, opstartmap, Taakplanner, ...), en niet in een
    map staat waar de gebruiker mogelijk geen schrijfrechten heeft
    (bv. Program Files).
    """
    appdata_dir = os.getenv('APPDATA') or os.path.expanduser('~')
    settings_dir = os.path.join(appdata_dir, 'Imolia Desktop Customizer')
    os.makedirs(settings_dir, exist_ok=True)
    new_path = os.path.join(settings_dir, 'settings.json')

    # Eenmalige migratie: oudere versies schreven settings.json relatief
    # (naast de exe of in de working directory). Als die bestaat en er nog
    # geen settings op de nieuwe, vaste locatie staan, kopieer ze over zodat
    # bestaande gebruikers hun widgetconfiguratie niet kwijtraken.
    if not os.path.exists(new_path):
        for legacy_path in _legacy_settings_paths():
            if os.path.exists(legacy_path) and os.path.abspath(legacy_path) != os.path.abspath(new_path):
                try:
                    shutil.copyfile(legacy_path, new_path)
                    logger.info(f"Settings gemigreerd van {legacy_path} naar {new_path}")
                    break
                except OSError as e:
                    logger.warning(f"Kon oude settings niet migreren van {legacy_path}: {e}")

    return new_path


class Settings:
    def __init__(self, filename=None):
        self.filename = filename or _default_settings_path()
        self.settings = {}
        self.load()

    def load(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    self.settings = json.load(f)
                return
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Kon settings niet laden van {self.filename}: {e}")

        self.settings = {
            'overlay_geometry': (100, 100, 300, 200)
        }
        self.save()

    def save(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except OSError as e:
            logger.error(f"Kon settings niet opslaan naar {self.filename}: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()