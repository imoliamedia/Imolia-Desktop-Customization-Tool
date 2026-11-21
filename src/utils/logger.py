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
from logging.handlers import RotatingFileHandler

# Een logbestand mag niet onbeperkt groeien: een fout die elke seconde terugkomt
# (zoals de oude recursiefout in het widgetbeheer) maakte van app.log 93 MB.
# Nu blijft het bij maximaal 2 MB + 3 oudere bestanden van elk 2 MB.
LOG_MAX_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 3


def setup_logger():
    logger = logging.getLogger('DesktopCustomizer')
    if logger.handlers:
        return logger  # al ingesteld; opnieuw aanroepen mag geen dubbele regels geven
    logger.setLevel(logging.DEBUG)

    # Creëer logs directory in AppData
    log_dir = os.path.join(os.getenv('APPDATA'), 'Imolia Desktop Customizer', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')

    try:
        # File handler
        file_handler = RotatingFileHandler(log_file, maxBytes=LOG_MAX_BYTES,
                                           backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    except PermissionError:
        print("Kon het logbestand niet aanmaken. Gebruik alleen console logging.")
        logger.addHandler(logging.StreamHandler())

    return logger