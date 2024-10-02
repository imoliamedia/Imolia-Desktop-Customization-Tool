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
import sys
import re
import logging
from src.utils.venv_manager import VenvManager

def parse_dependencies(file_path):
    dependencies = []
    with open(file_path, 'r') as file:
        content = file.read()
        match = re.search(r'"""[\s\S]*?Dependencies:([\s\S]*?)"""', content)
        if match:
            deps = match.group(1).strip().split('\n')
            dependencies = [dep.strip() for dep in deps if dep.strip()]
    return dependencies

def load_widgets(widget_dir):
    widgets = {}
    sys.path.append(widget_dir)  # Add widget directory to Python path
    for filename in os.listdir(widget_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]  # Remove .py extension
            module_path = os.path.join(widget_dir, filename)
            dependencies = parse_dependencies(module_path)
            
            logging.debug(f"Laden van widget: {module_name}")
            logging.debug(f"Afhankelijkheden voor {module_name}: {dependencies}")
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'Widget'):
                    widgets[module_name] = {
                        'class': module.Widget,
                        'dependencies': dependencies
                    }
                    logging.debug(f"Widget {module_name} succesvol geladen")
                else:
                    logging.warning(f"Waarschuwing: {filename} bevat geen 'Widget' klasse.")
            except Exception as e:
                logging.error(f"Fout bij het laden van widget {filename}: {str(e)}")
    
    sys.path.remove(widget_dir)  # Remove widget directory from Python path
    return widgets

class WidgetManager:
    def __init__(self, widget_dir):
        self.widget_dir = widget_dir
        self.venv_manager = VenvManager(os.path.dirname(widget_dir))
        self.widgets = self.load_widgets()
        self.active_widgets = {}

    def load_widgets(self):
        return load_widgets(self.widget_dir)

    def get_available_widgets(self):
        return list(self.widgets.keys())

    def reload_widgets(self):
        self.widgets = self.load_widgets()
        for widget_name in list(self.active_widgets.keys()):
            if widget_name not in self.widgets:
                self.deactivate_widget(widget_name)
            else:
                self.refresh_widget(widget_name)

    def activate_widget(self, widget_name):
        if widget_name in self.widgets:
            widget_info = self.widgets[widget_name]
            dependencies = widget_info['dependencies']
            
            logging.debug(f"Activeren van widget: {widget_name}")
            logging.debug(f"Afhankelijkheden voor {widget_name}: {dependencies}")
            
            try:
                self.venv_manager.install_dependencies(widget_name, dependencies)
                
                # Use the virtual environment's Python to import the widget
                python_exec = self.venv_manager.get_python_executable()
                original_executable = sys.executable
                sys.executable = python_exec
                
                # Reload the module to ensure we're using the correct environment
                module_path = os.path.join(self.widget_dir, f"{widget_name}.py")
                spec = importlib.util.spec_from_file_location(widget_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                self.active_widgets[widget_name] = module.Widget()
                
                # Restore the original Python executable
                sys.executable = original_executable
                
                logging.debug(f"Widget {widget_name} succesvol geactiveerd")
                return self.active_widgets[widget_name]
            except Exception as e:
                logging.error(f"Fout bij activeren van widget {widget_name}: {str(e)}")
                logging.exception("Stacktrace:")
                return None
        else:
            logging.warning(f"Widget {widget_name} niet gevonden.")
            return None

    def deactivate_widget(self, widget_name):
        if widget_name in self.active_widgets:
            widget = self.active_widgets[widget_name]
            if hasattr(widget, 'close') and callable(getattr(widget, 'close')):
                widget.close()
            del self.active_widgets[widget_name]
            logging.debug(f"Widget {widget_name} gedeactiveerd")
        else:
            logging.warning(f"Widget {widget_name} is niet actief.")

    def refresh_widget(self, widget_name):
        if widget_name in self.active_widgets:
            self.deactivate_widget(widget_name)
        return self.activate_widget(widget_name)

    def get_active_widgets(self):
        return self.active_widgets

    def get_widget_dependencies(self, widget_name):
        return self.widgets.get(widget_name, {}).get('dependencies', [])