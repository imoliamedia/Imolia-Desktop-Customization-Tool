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
import subprocess
import sys
import venv
import logging

class VenvManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.venv_path = None

    def create_widget_venv(self, widget_name):
        self.venv_path = os.path.join(self.base_dir, f'{widget_name}_venv')
        if not os.path.exists(self.venv_path):
            venv.create(self.venv_path, with_pip=True)
        return self.venv_path

    def install_dependencies(self, widget_name, dependencies):
        venv_path = self.create_widget_venv(widget_name)
        pip_path = os.path.join(venv_path, 'Scripts', 'pip.exe')
        for dep in dependencies:
            subprocess.run([pip_path, 'install', dep], check=True)

    def get_python_executable(self):
        if self.venv_path is None:
            raise ValueError("Virtual environment path is not set. Call create_widget_venv first.")
        return os.path.join(self.venv_path, 'Scripts' if sys.platform == 'win32' else 'bin', 'python')

    def run_in_venv(self, command):
        python_executable = self.get_python_executable()
        logging.info(f"Running command in virtual environment: {command}")
        try:
            result = subprocess.run([python_executable, '-c', command], capture_output=True, text=True, check=True)
            logging.info("Command executed successfully")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logging.error(f"Error executing command: {e.stderr}")
            raise