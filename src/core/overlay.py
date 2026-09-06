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
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QRegion
from pathlib import Path
from src.config import APP_NAME, WIDGETS_FOLDER_NAME
from src.utils.widget_loader import WidgetManager
from src.utils.widget_seeder import seed_default_widgets

logger = logging.getLogger('DesktopCustomizer.Overlay')

class Overlay(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.widgets = {}

        user_documents = Path.home() / "Documents"
        default_widget_dir = user_documents / WIDGETS_FOLDER_NAME
        
        default_widget_dir.mkdir(parents=True, exist_ok=True)

        # Zorg dat de meegeleverde standaard-widgets (klok, calculator, ...)
        # daadwerkelijk in de widgetmap van de gebruiker staan. Zonder dit
        # blijft die map op een verse installatie leeg en verschijnt er
        # nooit een widget, ook niet als hij in de instellingen actief is.
        # Bestaande (mogelijk aangepaste) widget-bestanden worden nooit
        # overschreven.
        seeded = seed_default_widgets(str(default_widget_dir))
        if seeded:
            logger.info(f"Standaard-widgets toegevoegd aan widgetmap: {seeded}")

        widget_dir = str(default_widget_dir)
        self.widget_manager = WidgetManager(widget_dir)

    def initUI(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnBottomHint |
            Qt.Tool
        )

        # Combineer alle schermen tot één virtuele rechthoek i.p.v. enkel
        # het scherm waar de muis toevallig stond bij het opstarten.
        # desktop.geometry() geeft de omvattende rechthoek van het hele
        # virtuele bureaublad (alle monitoren samen), zoals Windows dat
        # zelf ook al hanteert. Widgets kunnen zo vrij naar elk scherm
        # gesleept worden.
        desktop = QDesktopWidget()
        desktop_rect = desktop.geometry()
        self.setGeometry(self._avoid_fullscreen_detection(desktop_rect))

        self.load_active_widgets()

        # De overlay beslaat het volledige scherm, maar mag alleen daar
        # écht klikbaar zijn waar een widget staat. Zonder dit vangt deze
        # doorzichtige, schermvullende overlay ALLE muisklikken op zodra er
        # geen ander venster (Chrome, Verkenner, ...) ervoor open staat -
        # inclusief klikken die voor het bureaublad of de taakbalk bedoeld
        # waren. setMask() beperkt zowel de zichtbare als de klikbare
        # regio tot de opgegeven vorm (zie Qt-documentatie bij
        # QWidget.setMask); buiten die vorm bestaat de overlay simpelweg
        # niet voor de muis, en vallen klikken automatisch door naar wat
        # eronder zit. Een timer houdt dit bij tijdens het slepen/resizen
        # van widgets, zonder dat elke widget zelf een signaal hoeft te
        # sturen.
        self.update_click_through_mask()
        self._mask_update_timer = QTimer(self)
        self._mask_update_timer.timeout.connect(self.update_click_through_mask)
        self._mask_update_timer.start(250)

    def update_click_through_mask(self):
        """Beperk het klikbare/zichtbare gebied van de overlay tot de
        plekken waar actieve widgets staan (zie toelichting in initUI)."""
        region = QRegion()
        for widget in self.widgets.values():
            if widget.isVisible():
                region += QRegion(widget.geometry())
        self.setMask(region)

    def _avoid_fullscreen_detection(self, rect):
        """Krimp de vensterrect met 1 pixel t.o.v. het volledige scherm.

        Windows behandelt een randloos venster dat exact de resolutie van
        een scherm dekt soms als een fullscreen-game (Fullscreen
        Optimizations/Game Bar-heuristiek). Zodra dat venster geactiveerd
        wordt - bv. door ergens op dat scherm te klikken - kan dat de
        bureaubladcompositie (DWM) verstoren: het scherm wordt zwart en de
        taakbalk verdwijnt. Eén pixel kleiner dan het scherm maken is
        genoeg om niet meer als "exact fullscreen" herkend te worden,
        zonder dat dit visueel merkbaar is.
        """
        return rect.adjusted(0, 0, -1, -1)

    def load_active_widgets(self):
        """Laad actieve widgets."""
        active_widgets = self.settings.get('active_widgets', [])
        available_widgets = self.widget_manager.get_available_widgets()
        
        logger.info(f"Actieve widgets laden: {active_widgets}")
        logger.info(f"Beschikbare widgets: {available_widgets}")

        missing_widgets = [w for w in active_widgets if w not in available_widgets]
        if missing_widgets:
            logger.warning(
                f"Deze actieve widgets staan niet in de widgetmap en worden overgeslagen: "
                f"{missing_widgets}"
            )

        # Verwijder inactieve widgets
        for widget_name in list(self.widgets.keys()):
            if widget_name not in active_widgets:
                logger.info(f"Widget {widget_name} deactiveren")
                self.widget_manager.deactivate_widget(widget_name)
                del self.widgets[widget_name]
        
        # Laad actieve widgets
        for widget_name in active_widgets:
            if widget_name in available_widgets and widget_name not in self.widgets:
                logger.info(f"Widget {widget_name} activeren")
                try:
                    widget = self.widget_manager.activate_widget(widget_name)
                    if widget:
                        self.widgets[widget_name] = widget
                        widget.setParent(self)

                        # Grootte uit configuratie laden, geclampt aan dit scherm.
                        # Instellingen kunnen afkomstig zijn van een andere pc
                        # (ander schermformaat/resolutie), dus zonder clamping
                        # kan een widget schermvullend of buiten beeld belanden.
                        if hasattr(widget, 'config') and 'size' in widget.config:
                            saved_size = self._clamp_size(widget.config['size'])
                            widget.resize(*saved_size)

                        # Positie uit configuratie laden of standaard zetten
                        if hasattr(widget, 'config') and 'position' in widget.config:
                            saved_position = widget.config['position']
                            safe_position = self._clamp_position(saved_position, widget.size())
                            widget.move(*safe_position)
                        else:
                            # Standaard positie
                            widget.move(50 * len(self.widgets), 50 * len(self.widgets))

                        widget.show()
                    else:
                        logger.error(f"Widget {widget_name} kon niet worden geactiveerd")
                        self.show_widget_error(widget_name)
                except Exception as e:
                    logger.exception(f"Fout bij activeren van widget {widget_name}")
                    self.show_widget_error(widget_name, str(e))

        # Direct bijwerken i.p.v. te wachten op de volgende timer-tick, zodat
        # widgets die net via Instellingen (de)geactiveerd zijn onmiddellijk
        # het juiste klikbare gebied krijgen. Bij de allereerste aanroep
        # vanuit initUI() bestaat de mask-timer nog niet - dan is dit een
        # no-op tot initUI() zelf update_click_through_mask() aanroept.
        if hasattr(self, '_mask_update_timer'):
            self.update_click_through_mask()

    def _clamp_size(self, size):
        """Beperk een opgeslagen widgetgrootte tot het huidige scherm.

        Voorkomt dat een grootte die op een ander (bv. groter multi-monitor)
        scherm is opgeslagen, de widget op dit scherm schermvullend maakt.
        """
        screen_rect = self.geometry()
        width, height = size
        max_width = max(screen_rect.width(), 1)
        max_height = max(screen_rect.height(), 1)
        clamped_width = min(max(int(width), 1), max_width)
        clamped_height = min(max(int(height), 1), max_height)
        if (clamped_width, clamped_height) != (width, height):
            logger.warning(
                f"Widgetgrootte {size} paste niet op dit scherm "
                f"({screen_rect.width()}x{screen_rect.height()}), aangepast naar "
                f"({clamped_width}, {clamped_height})"
            )
        return clamped_width, clamped_height

    def _clamp_position(self, position, widget_size):
        """Beperk een opgeslagen widgetpositie zodat de widget zichtbaar blijft.

        Voorkomt dat een positie die op een ander scherm is opgeslagen
        (bv. een tweede monitor die hier niet bestaat, of negatieve
        coördinaten) de widget volledig buiten beeld plaatst.
        """
        screen_rect = self.geometry()
        x, y = position
        width = widget_size.width()
        height = widget_size.height()

        max_x = max(screen_rect.width() - width, 0)
        max_y = max(screen_rect.height() - height, 0)
        clamped_x = min(max(int(x), 0), max_x)
        clamped_y = min(max(int(y), 0), max_y)

        if (clamped_x, clamped_y) != (x, y):
            logger.warning(
                f"Widgetpositie {position} viel buiten dit scherm "
                f"({screen_rect.width()}x{screen_rect.height()}), aangepast naar "
                f"({clamped_x}, {clamped_y})"
            )
        return clamped_x, clamped_y

    def show_widget_error(self, widget_name, error_message=None):
        """Toon een foutmelding bij het laden van een widget."""
        error_text = f"De widget '{widget_name}' kon niet worden geladen."
        if error_message:
            error_text += f"\n\nFoutmelding: {error_message}"
        
        logger.error(error_text)
        
        QMessageBox.warning(
            self, 
            f"{APP_NAME} - Widget Fout",
            error_text
        )

    def resizeEvent(self, event):
        desktop = QDesktopWidget()
        self.setGeometry(self._avoid_fullscreen_detection(desktop.geometry()))
        super().resizeEvent(event)

    def showEvent(self, event):
        self.lower()
        super().showEvent(event)

    def closeEvent(self, event):
        for widget in self.widgets.values():
            widget.close()
        QWidget.closeEvent(self, event)