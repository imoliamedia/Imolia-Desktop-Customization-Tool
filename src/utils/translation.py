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

import gettext
import os

def setup_translations(language):
    localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'resources', 'translations')
    translate = gettext.translation('desktop_customizer', localedir, languages=[language], fallback=True)
    return translate.gettext

# Global translation function
_ = setup_translations('en')  # Default to English

def update_language(language):
    global _
    _ = setup_translations(language)