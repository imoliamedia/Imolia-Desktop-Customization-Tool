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
import sys
import re
import json
import logging
import importlib.util
import importlib.machinery
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from src.utils.package_manager import PackageManager

logger = logging.getLogger('DesktopCustomizer.WidgetLoader')

def parse_dependencies(file_path):
    """
    Parse dependencies from a widget file's docstring.
    
    Args:
        file_path (str): Path to the widget Python file
        
    Returns:
        list: List of dependency strings (e.g., ["PyQt5==5.15.6", "requests==2.28.1"])
    """
    dependencies = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            match = re.search(r'"""[\s\S]*?Dependencies:([\s\S]*?)(?:"""|$)', content)
            if match:
                deps_section = match.group(1).strip()
                deps = [line.strip() for line in deps_section.split('\n')]
                dependencies = [dep for dep in deps if dep and not dep.startswith('#')]
            else:
                # Check if there might be a requirements.txt or dependency.json file
                dir_path = os.path.dirname(file_path)
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Try requirements.txt
                req_path = os.path.join(dir_path, f"{base_name}_requirements.txt")
                if os.path.exists(req_path):
                    with open(req_path, 'r', encoding='utf-8') as req_file:
                        dependencies = [line.strip() for line in req_file.readlines() 
                                        if line.strip() and not line.strip().startswith('#')]
                
                # Try dependency.json
                dep_json_path = os.path.join(dir_path, f"{base_name}_dependencies.json")
                if os.path.exists(dep_json_path):
                    with open(dep_json_path, 'r', encoding='utf-8') as json_file:
                        dependency_data = json.load(json_file)
                        if isinstance(dependency_data, list):
                            dependencies = dependency_data
                        elif isinstance(dependency_data, dict) and 'dependencies' in dependency_data:
                            dependencies = dependency_data['dependencies']
    except Exception as e:
        logger.error(f"Error parsing dependencies from {file_path}: {str(e)}")
        
    # Ensure PyQt5 is always included
    if not any(dep.startswith('PyQt5') for dep in dependencies):
        dependencies.append('PyQt5==5.15.6')
        
    logger.info(f"Parsed dependencies for {os.path.basename(file_path)}: {dependencies}")
    return dependencies


def is_valid_widget_file(file_path):
    """
    Check if a file is a valid widget file by looking for the 'Widget =' assignment.
    
    Args:
        file_path (str): Path to the file to check
        
    Returns:
        bool: True if it's a valid widget file, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Look for Widget = ClassName pattern
            return bool(re.search(r'Widget\s*=\s*\w+', content))
    except Exception as e:
        logger.error(f"Error checking if {file_path} is a valid widget file: {str(e)}")
        return False


class DependencyWorker(QThread):
    """Worker thread for asynchronous dependency installation."""
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(bool, str)  # success, error_message
    
    def __init__(self, package_manager, widget_name, dependencies):
        super().__init__()
        self.package_manager = package_manager
        self.widget_name = widget_name
        self.dependencies = dependencies
        
    def run(self):
        try:
            total_deps = len(self.dependencies)
            for i, dep in enumerate(self.dependencies, 1):
                self.status_update.emit(f"Installeren van {dep}...")
                self.progress_update.emit(i, total_deps)
                success, message = self.package_manager.install_package(dep)
                if not success:
                    self.finished.emit(False, f"Fout bij installeren van {dep}: {message}")
                    return
                    
            # Update widget dependencies
            self.package_manager.install_dependencies(self.widget_name, self.dependencies)
            
            self.status_update.emit("Installatie voltooid.")
            self.progress_update.emit(total_deps, total_deps)
            self.finished.emit(True, "")
        except Exception as e:
            logger.exception(f"Error installing dependencies for {self.widget_name}")
            self.finished.emit(False, str(e))


class WidgetInfo:
    """Store information about a widget."""
    def __init__(self, name, path, dependencies=None, display_name=None):
        self.name = name
        self.path = path
        self.dependencies = dependencies or []
        self.display_name = display_name or self.generate_display_name()
        self.installed = False
        self.error_message = ""
        
    def generate_display_name(self):
        """Generate a display name from the widget file name."""
        return ' '.join(word.capitalize() for word in self.name.replace('_', ' ').split())


class WidgetManager(QObject):
    """Manage widget discovery, loading, and activation."""
    widget_added = pyqtSignal(str)
    widget_removed = pyqtSignal(str)
    widget_updated = pyqtSignal(str)
    install_status = pyqtSignal(str, str)  # widget_name, status_message
    install_progress = pyqtSignal(str, int, int)  # widget_name, current, total
    install_complete = pyqtSignal(str, bool, str)  # widget_name, success, error_message
    
    def __init__(self, widget_dir):
        super().__init__()
        self.widget_dir = os.path.abspath(widget_dir)
        
        # Create widgets directory if it doesn't exist
        os.makedirs(self.widget_dir, exist_ok=True)
        
        logger.info(f"Initializing WidgetManager with widget directory: {self.widget_dir}")
        
        # Initialize package manager
        self.package_manager = PackageManager()
        
        # Information about available widgets (name -> WidgetInfo object)
        self.available_widgets = {}
        
        # Dictionary of active widget instances
        self.active_widgets = {}
        
        # Dictionary of dependency installation workers
        self.installation_workers = {}
        
        # Add packages directory to sys.path to ensure widgets can find dependencies
        package_paths = self.package_manager.get_package_paths()
        for path in package_paths:
            if path not in sys.path:
                logger.info(f"Adding package path to sys.path: {path}")
                sys.path.insert(0, path)
        
        # Add widget directory to sys.path temporarily for importing
        if self.widget_dir not in sys.path:
            logger.info(f"Adding widget directory to sys.path: {self.widget_dir}")
            sys.path.insert(0, self.widget_dir)
        
        # Scan for widgets
        self.scan_widgets()
    
    def scan_widgets(self):
        """Scan the widgets directory for new or updated widgets."""
        logger.info(f"Scanning for widgets in {self.widget_dir}")
        
        # Remember previous available widgets for comparison
        previous_widgets = set(self.available_widgets.keys())
        current_widgets = set()
        
        try:
            # Check Python files in the directory
            for filename in os.listdir(self.widget_dir):
                if filename.endswith('.py') and filename != '__init__.py':
                    widget_name = os.path.splitext(filename)[0]
                    file_path = os.path.join(self.widget_dir, filename)
                    
                    # Check if this is a valid widget file
                    if is_valid_widget_file(file_path):
                        logger.info(f"Found widget: {widget_name}")
                        # Add to available widgets or update
                        if widget_name not in self.available_widgets:
                            # New widget
                            dependencies = parse_dependencies(file_path)
                            widget_info = WidgetInfo(widget_name, file_path, dependencies)
                            self.available_widgets[widget_name] = widget_info
                            self.widget_added.emit(widget_name)
                        else:
                            # Update if the file has been modified
                            widget_info = self.available_widgets[widget_name]
                            
                            # Check if dependencies need to be updated
                            if os.path.getmtime(file_path) > 0:  # Always update for now
                                dependencies = parse_dependencies(file_path)
                                widget_info.dependencies = dependencies
                                widget_info.installed = False
                                self.widget_updated.emit(widget_name)
                        
                        # Check if dependencies are installed
                        is_installed, _ = self.package_manager.check_dependencies(widget_name, widget_info.dependencies)
                        widget_info.installed = is_installed
                        logger.info(f"Widget {widget_name} dependencies installed: {is_installed}")
                        
                        # Add to current widgets
                        current_widgets.add(widget_name)
            
            # Detect removed widgets
            for widget_name in previous_widgets - current_widgets:
                if widget_name in self.available_widgets:
                    logger.info(f"Widget removed: {widget_name}")
                    del self.available_widgets[widget_name]
                    self.widget_removed.emit(widget_name)
            
            return list(self.available_widgets.keys())
        except Exception as e:
            logger.error(f"Error scanning widgets: {str(e)}")
            return []
    
    def get_available_widgets(self):
        """Get a list of available widget names."""
        return list(self.available_widgets.keys())
    
    def get_widget_info(self, widget_name):
        """Get information about a widget."""
        return self.available_widgets.get(widget_name)
    
    def check_dependencies(self, widget_name):
        """Check if all dependencies are installed for a widget."""
        widget_info = self.get_widget_info(widget_name)
        if not widget_info:
            logger.warning(f"Cannot check dependencies for unknown widget: {widget_name}")
            return False, "Widget not found"
        
        # If already marked as installed, return True
        if widget_info.installed:
            logger.info(f"Widget {widget_name} dependencies are already installed")
            return True, ""
            
        # Check dependencies with package manager
        logger.info(f"Checking dependencies for widget {widget_name}")
        return self.package_manager.check_dependencies(widget_name, widget_info.dependencies)
    
    def install_dependencies(self, widget_name):
        """Install all dependencies for a widget asynchronously."""
        widget_info = self.get_widget_info(widget_name)
        if not widget_info:
            logger.warning(f"Cannot install dependencies for unknown widget: {widget_name}")
            return False, "Widget not found"
            
        # Return true if already installed
        if widget_info.installed:
            logger.info(f"Dependencies for widget {widget_name} are already installed")
            return True, "Already installed"
            
        # Start a worker thread to install dependencies
        logger.info(f"Starting installation of dependencies for widget {widget_name}")
        self.install_status.emit(widget_name, "Voorbereiden installatie...")
        
        worker = DependencyWorker(self.package_manager, widget_name, widget_info.dependencies)
        worker.status_update.connect(lambda msg: self.install_status.emit(widget_name, msg))
        worker.progress_update.connect(lambda curr, total: self.install_progress.emit(widget_name, curr, total))
        worker.finished.connect(lambda success, error: self._on_install_finished(widget_name, success, error))
        
        # Store worker in dictionary to prevent garbage collection
        self.installation_workers[widget_name] = worker
        
        # Start the worker thread
        worker.start()
        
        return True, "Installation started"
    
    def _on_install_finished(self, widget_name, success, error_message):
        """Called when dependency installation finishes."""
        if success:
            # Mark widget as installed
            widget_info = self.get_widget_info(widget_name)
            if widget_info:
                widget_info.installed = True
                widget_info.error_message = ""
            logger.info(f"Dependencies installed successfully for {widget_name}")
        else:
            # Mark widget as not installed with error message
            widget_info = self.get_widget_info(widget_name)
            if widget_info:
                widget_info.installed = False
                widget_info.error_message = error_message
            logger.error(f"Failed to install dependencies for {widget_name}: {error_message}")
        
        # Clean up worker
        if widget_name in self.installation_workers:
            del self.installation_workers[widget_name]
            
        # Emit signal for UI update
        self.install_complete.emit(widget_name, success, error_message)
    
    def load_widget_module(self, widget_name):
        """Load a widget module using importlib."""
        try:
            widget_info = self.get_widget_info(widget_name)
            if not widget_info:
                logger.error(f"Widget {widget_name} not found")
                return None
            
            file_path = widget_info.path
            logger.info(f"Loading widget module {widget_name} from {file_path}")
                
            # Add widget dir to sys.path temporarily if not already there
            widget_dir_added = False
            if self.widget_dir not in sys.path:
                sys.path.insert(0, self.widget_dir)
                widget_dir_added = True
                
            # Add packages directory to sys.path if not already there
            package_paths = self.package_manager.get_package_paths()
            path_added = []
            for path in package_paths:
                if path not in sys.path:
                    sys.path.insert(0, path)
                    path_added.append(path)
            
            # Import the module
            try:
                # Try direct import first
                module = importlib.import_module(widget_name)
                logger.info(f"Imported {widget_name} as module")
            except ImportError:
                # Fall back to spec_from_file_location
                logger.info(f"Direct import failed, trying spec_from_file_location")
                spec = importlib.util.spec_from_file_location(widget_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.info(f"Loaded {widget_name} from file location")
                
            # Clean up sys.path
            if widget_dir_added and self.widget_dir in sys.path:
                sys.path.remove(self.widget_dir)
                
            for path in path_added:
                if path in sys.path:
                    sys.path.remove(path)
                    
            return module
        except Exception as e:
            logger.exception(f"Error loading widget module {widget_name}")
            return None
    
    def activate_widget(self, widget_name):
        """Activate a widget (create an instance)."""
        logger.info(f"Activating widget: {widget_name}")
        
        # Check if widget is already active
        if widget_name in self.active_widgets:
            logger.info(f"Widget {widget_name} is already active")
            return self.active_widgets[widget_name]
            
        # Check if dependencies are installed
        is_ready, message = self.check_dependencies(widget_name)
        if not is_ready:
            logger.warning(f"Dependencies not installed for {widget_name}: {message}")
            self.install_dependencies(widget_name)
            return None
            
        try:
            # Make sure package path is in sys.path
            package_paths = self.package_manager.get_package_paths()
            for path in package_paths:
                if path not in sys.path:
                    logger.info(f"Adding package path to sys.path: {path}")
                    sys.path.insert(0, path)
            
            # Load module
            module = self.load_widget_module(widget_name)
            if not module:
                logger.error(f"Failed to load module for {widget_name}")
                return None
                
            # Create widget instance
            if hasattr(module, 'Widget'):
                self.active_widgets[widget_name] = module.Widget()
                logger.info(f"Widget {widget_name} successfully activated")
                return self.active_widgets[widget_name]
            else:
                logger.error(f"Widget {widget_name} has no Widget class")
                return None
        except Exception as e:
            logger.exception(f"Error activating widget {widget_name}")
            return None
    
    def deactivate_widget(self, widget_name):
        """Deactivate a widget (destroy instance)."""
        if widget_name in self.active_widgets:
            try:
                widget = self.active_widgets[widget_name]
                if hasattr(widget, 'close') and callable(getattr(widget, 'close')):
                    widget.close()
                del self.active_widgets[widget_name]
                logger.info(f"Widget {widget_name} deactivated")
            except Exception as e:
                logger.exception(f"Error deactivating widget {widget_name}")
    
    def refresh_widget(self, widget_name):
        """Refresh a widget by deactivating and activating it again."""
        self.deactivate_widget(widget_name)
        return self.activate_widget(widget_name)