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

import sys
import os
from pathlib import Path

# Configureer embedded Python als we in een PyInstaller executable zijn
if getattr(sys, 'frozen', False):
    # We zijn in een PyInstaller executable
    base_dir = os.path.dirname(sys.executable)

    # Zoek de embedded Python-map. In een onedir-build van PyInstaller 6.x+
    # staan gebundelde datas (zoals embedded_python) niet meer los naast de
    # exe, maar onder een '_internal'-submap (sys._MEIPASS) - vandaar dat
    # ook die locatie gecheckt wordt.
    _candidate_embedded_python_dirs = [os.path.join(base_dir, "embedded_python")]
    _meipass = getattr(sys, '_MEIPASS', None)
    if _meipass:
        _candidate_embedded_python_dirs.append(os.path.join(_meipass, "embedded_python"))

    embedded_python_dir = next(
        (p for p in _candidate_embedded_python_dirs if os.path.exists(p)),
        _candidate_embedded_python_dirs[0]
    )
    if os.path.exists(embedded_python_dir):
        # Voeg de embedded Python toe aan PATH
        os.environ['PATH'] = f"{embedded_python_dir};{os.environ.get('PATH', '')}"
        # Voeg embedded Python Scripts toe aan PATH
        scripts_dir = os.path.join(embedded_python_dir, "Scripts")
        if os.path.exists(scripts_dir):
            os.environ['PATH'] = f"{scripts_dir};{os.environ.get('PATH', '')}"

# Zorg ervoor dat alle Python modules beschikbaar zijn
if getattr(sys, 'frozen', False):
    # We runnen vanuit een PyInstaller executable
    base_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    # We runnen vanuit een Python script
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Voeg base_dir toe aan sys.path voor imports
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# QtWebEngine (ESP32 Web Dashboard widget) gebruikt GPU-compositing
# (Chromium/ANGLE) die kan botsen met de doorzichtige, randloze overlay
# waarin widgets zitten: bij interactie met de webweergave kon de Windows
# bureaubladcompositie (DWM) in de war raken, met een zwart scherm en een
# verdwenen taakbalk tot gevolg. Software-rendering forceren voor Chromium
# voorkomt dit conflict. Moet gezet worden vóórdat QtWebEngineWidgets voor
# het eerst wordt geladen, dus hier op module-niveau, ruim op tijd.
os.environ.setdefault(
    'QTWEBENGINE_CHROMIUM_FLAGS',
    '--disable-gpu --disable-gpu-compositing --disable-software-rasterizer'
)

# Zorgen dat QT plugins correct worden gevonden in frozen executable
if getattr(sys, 'frozen', False):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'platforms')

    # QtWebEngine (gebruikt door de ESP32 Web Dashboard widget) heeft veel
    # eigen DLL-afhankelijkheden (Chromium-gebaseerd) die niet altijd
    # betrouwbaar gevonden worden via PyQt5's eigen PATH-gebaseerde
    # zelfdetectie (find_qt() in PyQt5/__init__.py) wanneer Qt5/bin genest
    # onder '_internal' staat, zoals in een onedir-build van PyInstaller
    # 6.x+. os.add_dll_directory() registreert de map expliciet en
    # betrouwbaar bij de Windows DLL-loader, ongeacht PATH-timing.
    if hasattr(os, 'add_dll_directory'):
        _qt5_bin_candidates = [
            os.path.join(base_dir, "PyQt5", "Qt5", "bin"),
        ]
        if _meipass:
            _qt5_bin_candidates.append(os.path.join(_meipass, "PyQt5", "Qt5", "bin"))
        for _qt5_bin in _qt5_bin_candidates:
            if os.path.isdir(_qt5_bin):
                try:
                    os.add_dll_directory(_qt5_bin)
                except OSError:
                    pass

import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from src.core.overlay import Overlay
from src.config import APP_NAME
from src.core.tray_icon import SystemTrayIcon
from src.utils.settings import Settings
from src.utils.logger import setup_logger
from src.utils.widget_loader import WidgetManager

# Moet gezet worden VÓÓRDAT er ergens een QApplication-instantie wordt
# aangemaakt (dus hier, op module-niveau, vóór main() draait). Widgets
# worden pas ná het aanmaken van de QApplication dynamisch geladen, dus we
# kunnen niet wachten tot een widget PyQt5.QtWebEngineWidgets zelf
# importeert - dan is het al te laat en faalt die import met:
# "QtWebEngineWidgets must be imported or Qt.AA_ShareOpenGLContexts must be
# set before a QCoreApplication instance is created". Dit trof de ESP32
# Web Dashboard widget, die QtWebEngineWidgets pas laadt op het moment dat
# hij wordt geactiveerd.
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

_logger = None  # wordt gezet in main(), gebruikt door de excepthook

# Onthoud welke fouten al een melding hebben getoond, zodat een fout die
# blijft terugkomen (bv. een widget-timer die elke seconde opnieuw faalt)
# niet elke keer opnieuw een pop-up geeft. Elke fout wordt wel altijd
# gelogd - alleen de zichtbare melding wordt per uniek probleem één keer
# getoond.
_notified_error_signatures = set()


def _show_fatal_error(message):
    """Toon een zichtbare foutmelding i.p.v. dat de app stil verdwijnt."""
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, f"{APP_NAME} - Fout", message)
    except Exception:
        # Als zelfs Qt niet meer werkt, val terug op een print zodat er in
        # ieder geval iets zichtbaar is als de app vanuit een console draait.
        print(message, file=sys.stderr)


def _handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Globale excepthook voor fouten die tijdens het draaien optreden
    (bv. in een Qt-signaal/timer-callback van een widget), buiten de
    expliciete try/except rond het opstarten in main().

    Belangrijk: dit soort fouten sluit de applicatie in de praktijk NIET
    af (Qt's event loop blijft gewoon draaien na een fout in een slot) -
    dus wordt dat hier ook niet meer beweerd. Om te voorkomen dat een
    widget die telkens opnieuw dezelfde fout geeft (bv. een kapotte
    update-timer) de gebruiker bestookt met een pop-up per seconde, wordt
    een identieke fout maar één keer zichtbaar gemeld; alle herhalingen
    worden wel gewoon gelogd.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    formatted = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    # Signature op basis van type + herkomst (laatste frame), niet de volledige
    # boodschap, zodat bv. dezelfde fout met een net iets andere waarde nog
    # steeds als "dezelfde" fout wordt herkend.
    last_frame = exc_traceback
    while last_frame and last_frame.tb_next:
        last_frame = last_frame.tb_next
    origin = (last_frame.tb_frame.f_code.co_filename, last_frame.tb_lineno) if last_frame else (None, None)
    signature = (exc_type.__name__, origin)
    already_notified = signature in _notified_error_signatures

    if _logger:
        level = _logger.error if already_notified else _logger.critical
        level(f"Onverwachte fout opgetreden:\n{formatted}")
    else:
        print(formatted, file=sys.stderr)

    if already_notified:
        return
    _notified_error_signatures.add(signature)

    _show_fatal_error(
        "Er is een onverwachte fout opgetreden.\n\n"
        f"{exc_value}\n\n"
        "De applicatie blijft actief; deze melding verschijnt niet opnieuw voor "
        "dezelfde fout. Details zijn te vinden in het logbestand "
        "(%APPDATA%\\Imolia Desktop Customizer\\logs\\app.log)."
    )


def main():
    global _logger

    sys.excepthook = _handle_uncaught_exception

    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    # Setup logger
    logger = setup_logger()
    _logger = logger
    logger.info("Applicatie wordt gestart")
    logger.info(f"Python versie: {sys.version}")
    logger.info(f"Systeem: {sys.platform}")

    if getattr(sys, 'frozen', False):
        logger.info(f"Applicatie draait als PyInstaller executable")
        logger.info(f"Executable pad: {sys.executable}")
        # Log embedded Python pad (zie ook de PATH-configuratie bovenaan dit
        # bestand voor waarom zowel de map naast de exe als _MEIPASS gecheckt worden)
        if os.path.exists(embedded_python_dir):
            logger.info(f"Embedded Python gevonden op: {embedded_python_dir}")
        else:
            logger.warning(f"Geen embedded Python gevonden in: {embedded_python_dir}")
    else:
        logger.info(f"Applicatie draait als Python script")

    try:
        # Load settings (for application-wide settings, not widget-specific)
        settings = Settings()

        # Create and show overlay
        overlay = Overlay(settings)
        overlay.initUI()
        overlay.show()  # Make the overlay visible by default

        # Create system tray icon. Zoek zowel naast base_dir als onder
        # sys._MEIPASS: in een onedir-build van PyInstaller 6.x+ staan
        # gebundelde datas (zoals 'resources') onder een '_internal'-submap,
        # niet los naast de exe.
        icon_candidates = [os.path.join(base_dir, "resources", "icons", "tray_icon.ico")]
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            icon_candidates.append(os.path.join(meipass, "resources", "icons", "tray_icon.ico"))
        icon_path = next((p for p in icon_candidates if os.path.exists(p)), icon_candidates[0])
        if not os.path.exists(icon_path):
            logger.warning(f"Tray icoon niet gevonden op: {icon_path}")
        tray_icon = SystemTrayIcon(QIcon(icon_path), overlay, settings)
        tray_icon.show()
    except Exception:
        logger.exception("Fout tijdens opstarten van de applicatie")
        _show_fatal_error(
            "De applicatie kon niet worden gestart.\n\n"
            "Details zijn te vinden in het logbestand "
            "(%APPDATA%\\Imolia Desktop Customizer\\logs\\app.log)."
        )
        sys.exit(1)

    # Start the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()