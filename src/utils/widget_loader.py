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

import os
import importlib.util

def load_widgets(widget_dir):
    widgets = {}
    for filename in os.listdir(widget_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]  # Remove .py extension
            module_path = os.path.join(widget_dir, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for the 'Widget' class in the module
            if hasattr(module, 'Widget'):
                widgets[module_name] = module.Widget
    return widgets

class WidgetManager:
    def __init__(self, widget_dir):
        self.widget_dir = widget_dir
        self.widgets = self.load_widgets()
        self.active_widgets = {}

    def load_widgets(self):
        return load_widgets(self.widget_dir)

    def get_available_widgets(self):
        return list(self.widgets.keys())

    def reload_widgets(self):
        self.widgets = self.load_widgets()
        # Reload active widgets
        for widget_name in list(self.active_widgets.keys()):
            if widget_name not in self.widgets:
                self.deactivate_widget(widget_name)
            else:
                self.refresh_widget(widget_name)

    def activate_widget(self, widget_name):
        if widget_name in self.widgets:
            self.active_widgets[widget_name] = self.widgets[widget_name]()
            return self.active_widgets[widget_name]
        return None

    def deactivate_widget(self, widget_name):
        if widget_name in self.active_widgets:
            del self.active_widgets[widget_name]

    def refresh_widget(self, widget_name):
        if widget_name in self.active_widgets:
            self.deactivate_widget(widget_name)
        return self.activate_widget(widget_name)

    def get_active_widgets(self):
        return self.active_widgets