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
import json
import logging
import subprocess
import shutil
import re
import importlib
import importlib.metadata
from pathlib import Path
from datetime import datetime, timedelta
from distutils.version import LooseVersion

logger = logging.getLogger('DesktopCustomizer.PackageManager')

class PackageManager:
    """
    Beheer van widget packages zonder virtuele omgevingen.

    Deze class maakt gebruik van een embedded Python om packages te installeren
    voor widgets, zonder virtuele omgevingen te gebruiken.
    """

    # Package-namen die niet overeenkomen met de module die je importeert.
    # Sleutels in lowercase, zoals ze in een dependency-specificatie staan.
    _IMPORT_NAME_OVERRIDES = {
        'pyqtwebengine': 'PyQt5.QtWebEngineWidgets',
    }

    def __init__(self, base_dir=None):
        """
        Initialiseer de PackageManager.
        
        Args:
            base_dir (str, optional): Basis directory voor het opslaan van packages.
                                     Standaard: AppData/Roaming/Imolia Desktop Customizer/packages
        """
        # Basismap voor packages
        if base_dir is None:
            appdata_dir = os.path.join(os.getenv('APPDATA'), 'Imolia Desktop Customizer')
            self.base_dir = os.path.join(appdata_dir, 'packages')
        else:
            self.base_dir = os.path.abspath(base_dir)
            
        # Maak de basismap als deze niet bestaat
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Cache directory voor pip download cache
        self.pip_cache_dir = os.path.join(os.path.dirname(self.base_dir), 'pip_cache')
        os.makedirs(self.pip_cache_dir, exist_ok=True)
        
        # Status bestand voor het bijhouden van geïnstalleerde packages
        self.status_file = os.path.join(os.path.dirname(self.base_dir), 'packages_status.json')
        self.status_data = self._load_status()
        
        # Detecteer embedded Python
        self.python_path = self._find_embedded_python()
        self.pip_path = self._get_pip_path()

        # Pip pas (lui) installeren op het moment dat er echt een package
        # via pip geïnstalleerd moet worden - zie _ensure_pip_installed().
        # Dit gebeurde hier voorheen bij elke app-start onvoorwaardelijk,
        # wat een paar seconden tot ruim 10 seconden kostte (get-pip.py
        # downloaden) én internet vereiste, zelfs wanneer geen enkele
        # widget-dependency ontbreekt (dankzij de in-process-import-check
        # hierboven is dat voor de meegeleverde widgets altijd het geval).
        self._pip_ensured = False
        
    def _load_status(self):
        """
        Laad statusinformatie uit het statusbestand.
        
        Returns:
            dict: Status data
        """
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Fout bij laden van package status bestand: {str(e)}")
        
        return {
            'packages': {},
            'widgets': {}
        }
    
    def _save_status(self):
        """Bewaar status data naar statusbestand."""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status_data, f, indent=2)
        except Exception as e:
            logger.error(f"Fout bij opslaan van package status bestand: {str(e)}")

    def _find_embedded_python(self):
        """
        Zoek de embedded Python installatie.
        
        Eerst controleren we of we in een PyInstaller executable zijn, en zo ja,
        proberen we de embedded Python te vinden. Anders gebruiken we de 
        huidige Python interpreter.
        
        Returns:
            str: Pad naar Python executable
        """
        logger.info("Zoeken naar embedded Python...")
        
        # Check of we in een PyInstaller executable zijn
        if getattr(sys, 'frozen', False):
            # PyInstaller executable
            base_dir = os.path.dirname(sys.executable)
            logger.info(f"Running in PyInstaller executable: {base_dir}")
            
            # Zoek embedded Python in verschillende mogelijke locaties.
            # Sinds PyInstaller 6.x staan gebundelde datas (zoals
            # embedded_python) in een onedir-build niet meer direct naast
            # de exe, maar onder een '_internal'-submap (sys._MEIPASS).
            # Zonder deze locaties mee te checken werd de embedded Python
            # nooit gevonden in een moderne build, en viel alles terug op
            # een toevallig aanwezige systeem-Python (of helemaal niets op
            # een pc zonder Python).
            meipass = getattr(sys, '_MEIPASS', None)
            possible_paths = [
                os.path.join(base_dir, "python", "python.exe"),
                os.path.join(base_dir, "embedded_python", "python.exe"),
                os.path.join(base_dir, "python3", "python.exe"),
                os.path.join(base_dir, "embedded_python", "python3.exe"),
                os.path.join(base_dir, "python", "python3.exe"),
            ]
            if meipass:
                possible_paths.extend([
                    os.path.join(meipass, "embedded_python", "python.exe"),
                    os.path.join(meipass, "embedded_python", "python3.exe"),
                ])

            for path in possible_paths:
                logger.info(f"Checking for Python at: {path}")
                if os.path.exists(path):
                    logger.info(f"Embedded Python gevonden op: {path}")
                    return path
                    
            # Als we hier komen, hebben we geen embedded Python gevonden
            logger.warning("Geen embedded Python gevonden in executable directory, zoeken naar systeeminstallatie...")
            
            # Zoek in standaard Python locaties
            for python_dir in [r"C:\Python39", r"C:\Python310", r"C:\Python311", r"C:\Python312"]:
                python_exe = os.path.join(python_dir, "python.exe")
                logger.info(f"Checking for Python at: {python_exe}")
                if os.path.exists(python_exe):
                    logger.info(f"Systeeminstallatie van Python gevonden op: {python_exe}")
                    return python_exe
            
            # Zoek in PATH naar python
            try:
                if sys.platform == "win32":
                    # Windows: gebruik where.exe
                    result = subprocess.run(
                        ["where", "python"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
                    if result.returncode == 0:
                        python_path = result.stdout.splitlines()[0].strip()
                        logger.info(f"Python gevonden in PATH: {python_path}")
                        return python_path
                else:
                    # Linux/Mac: gebruik which
                    result = subprocess.run(
                        ["which", "python3"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
                    if result.returncode == 0:
                        python_path = result.stdout.strip()
                        logger.info(f"Python gevonden in PATH: {python_path}")
                        return python_path
            except Exception as e:
                logger.error(f"Fout bij zoeken naar Python in PATH: {e}")
                
            # Als laatste optie, ga ervan uit dat Python direct beschikbaar is
            logger.warning("Geen specifieke Python installatie gevonden. Gebruik 'python' of 'python3' commando als fallback.")
            return "python" if sys.platform == "win32" else "python3"
        else:
            # We draaien vanuit Python script, gebruik de huidige interpreter
            logger.info(f"Running from Python script, using current interpreter: {sys.executable}")
            return sys.executable
    
    def _get_pip_path(self):
        """
        Bepaal het pad naar pip.
        
        Returns:
            list: Commando om pip uit te voeren (python -m pip of pip.exe)
        """
        if not self.python_path:
            logger.error("Geen Python pad beschikbaar, kan pip pad niet bepalen")
            return None
            
        # Controleer of pip als module beschikbaar is
        if self.python_path in ["python", "python3"]:
            # Fallback naar command, gebruik -m pip
            return [self.python_path, "-m", "pip"]
        else:
            # In PyInstaller executable of normale Python, gebruik -m pip
            logger.info(f"Using {self.python_path} -m pip")
            return [self.python_path, "-m", "pip"]
    
    def _ensure_pip_installed(self):
        """Zorg ervoor dat pip geïnstalleerd is in de embedded Python."""
        if not self.python_path:
            logger.error("Geen Python-installatie gevonden, kan pip niet installeren.")
            return False
            
        try:
            # Controleer of pip al beschikbaar is
            logger.info(f"Controleren of pip beschikbaar is: {' '.join(self.pip_path + ['--version'])}")
            result = subprocess.run(
                self.pip_path + ["--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=self._get_startupinfo()
            )
            
            if result.returncode == 0:
                logger.info(f"Pip is al geïnstalleerd: {result.stdout.strip()}")
                return True
                
            # Installeer pip
            logger.info("Pip installeren...")
            result = subprocess.run(
                [self.python_path, "-m", "ensurepip", "--upgrade"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=self._get_startupinfo()
            )
            
            if result.returncode == 0:
                logger.info("Pip succesvol geïnstalleerd.")
                return True
            else:
                logger.error(f"Fout bij installeren van pip: {result.stderr}")
                
                # Probeer pip te downloaden en installeren via get-pip.py
                logger.info("Proberen pip te installeren via get-pip.py...")
                try:
                    import urllib.request
                    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
                    get_pip_path = os.path.join(self.base_dir, "get-pip.py")
                    
                    # Download get-pip.py
                    urllib.request.urlretrieve(get_pip_url, get_pip_path)
                    
                    # Voer get-pip.py uit
                    result = subprocess.run(
                        [self.python_path, get_pip_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=self._get_startupinfo()
                    )
                    
                    if result.returncode == 0:
                        logger.info("Pip succesvol geïnstalleerd via get-pip.py.")
                        return True
                    else:
                        logger.error(f"Fout bij installeren van pip via get-pip.py: {result.stderr}")
                except Exception as e:
                    logger.error(f"Fout bij downloaden/uitvoeren van get-pip.py: {e}")
                
                return False
                
        except Exception as e:
            logger.exception("Onverwachte fout bij controleren/installeren van pip")
            return False
    
    def _get_startupinfo(self):
        """
        Maak een subprocess.STARTUPINFO object om console vensters te verbergen.
        
        Returns:
            subprocess.STARTUPINFO of None
        """
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
        return startupinfo
    
    def _run_pip_silently(self, args):
        """
        Voer pip commando uit zonder console venster.
        
        Args:
            args (list): Command arguments
            
        Returns:
            tuple: (return_code, stdout, stderr)
        """
        if not self.pip_path:
            return -1, "", "Geen pip executable gevonden."

        # Pas hier (lui, één keer per proces) zorgen dat pip aanwezig is in
        # de embedded Python - niet al bij het aanmaken van de
        # PackageManager, want dan zou dit bij elke app-start gebeuren, ook
        # wanneer er uiteindelijk niets geïnstalleerd hoeft te worden.
        if not self._pip_ensured:
            self._pip_ensured = True
            self._ensure_pip_installed()

        # Voeg algemene argumenten toe
        full_args = self.pip_path + args + [
            '--cache-dir', self.pip_cache_dir,
            '--disable-pip-version-check'
        ]
        
        logger.info(f"Uitvoeren pip commando: {' '.join(full_args)}")
        try:
            # Voer het commando uit
            process = subprocess.run(
                full_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=self._get_startupinfo()
            )
            
            if process.returncode != 0:
                logger.error(f"Pip command failed with code {process.returncode}")
                logger.error(f"Stderr: {process.stderr}")
            else:
                logger.info("Pip command succeeded")
                
            return process.returncode, process.stdout, process.stderr
        except Exception as e:
            logger.exception(f"Fout bij uitvoeren pip commando: {' '.join(map(str, full_args))}")
            return -1, "", str(e)
    
    def _parse_package_spec(self, package_spec):
        """
        Parse een package specificatie in naam en versie constraint.
        
        Args:
            package_spec (str): Package specificatie (bijv. 'requests==2.28.1')
            
        Returns:
            tuple: (package_name, operator, version)
        """
        # Veelgebruikte versie operatoren
        operators = ['==', '>=', '<=', '>', '<', '~=', '!=']
        
        for op in operators:
            if op in package_spec:
                name, version = package_spec.split(op, 1)
                return name.strip(), op, version.strip()
        
        # Geen operator, alleen een package naam
        return package_spec.strip(), None, None
    
    def _importable_in_current_process(self, package_name, operator, version):
        """
        Controleer of een package al importeerbaar is in het huidige proces.

        Dit is bewust de eerste check, vóór er een apart (embedded) Python-
        subprocess wordt aangesproken. De widgets die met de app worden
        meegeleverd hebben hun dependencies al in de PyInstaller-executable
        ingebakken (hiddenimports) - die zijn dus al beschikbaar in dit
        proces zelf, ook al heeft de losse embedded Python er niets van
        geïnstalleerd. Zonder deze check zou de app bij elke eerste start
        denken dat alle standaard-widget-dependencies ontbreken en voor
        elke widget een pip-install via de embedded Python proberen te
        starten - iets dat internet, schrijfrechten en een aanwezige
        embedded_python-map vereist en op veel pc's faalt of door een
        antivirus wordt tegengehouden.

        Args:
            package_name (str): Naam van het package (zonder versie constraint)
            operator (str or None): Vergelijkingsoperator, bv. '=='
            version (str or None): Vereiste versie, indien van toepassing

        Returns:
            bool: True als het package hier al bruikbaar is
        """
        module_name = self._IMPORT_NAME_OVERRIDES.get(
            package_name.lower(), package_name.replace('-', '_')
        )

        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return False
        except Exception as e:
            logger.warning(f"Onverwachte fout bij importeren van {module_name}: {e}")
            return False

        if not operator:
            return True

        # Probeer de geïnstalleerde versie te bepalen. Lukt dat niet, dan
        # gaan we ervan uit dat de meegebundelde versie klopt (die ligt
        # immers vast bij het bouwen van de executable) in plaats van
        # onnodig een herinstallatie te forceren.
        installed_version = getattr(module, '__version__', None)
        if installed_version is None:
            try:
                installed_version = importlib.metadata.version(package_name)
            except Exception:
                return True

        try:
            if operator == '==':
                return installed_version == version
            elif operator == '>=':
                return LooseVersion(installed_version) >= LooseVersion(version)
            elif operator == '<=':
                return LooseVersion(installed_version) <= LooseVersion(version)
            elif operator == '>':
                return LooseVersion(installed_version) > LooseVersion(version)
            elif operator == '<':
                return LooseVersion(installed_version) < LooseVersion(version)
            elif operator == '~=':
                return LooseVersion(installed_version) >= LooseVersion(version) and \
                       installed_version.split('.')[0] == version.split('.')[0]
            elif operator == '!=':
                return installed_version != version
        except Exception:
            # Bij twijfel niet onnodig een werkende, meegebundelde dependency
            # als "ontbrekend" bestempelen.
            return True

        return True

    def _package_installed(self, package_spec):
        """
        Controleer of een package is geïnstalleerd.

        Args:
            package_spec (str): Package specificatie (bijv. 'requests==2.28.1')

        Returns:
            bool: True als de package is geïnstalleerd en voldoet aan de versie constraint
        """
        # Parse package spec
        package_name, operator, version = self._parse_package_spec(package_spec)

        # Snelle, offline check: is dit hier al gewoon te importeren?
        if self._importable_in_current_process(package_name, operator, version):
            logger.info(f"Package {package_name} is al beschikbaar in het huidige proces (geen install nodig)")
            self.status_data['packages'][package_name] = {
                'installed': datetime.now().isoformat(),
                'version': version if operator else None,
                'source': 'bundled',
            }
            self._save_status()
            return True

        if not self.python_path:
            logger.error("Geen Python executable gevonden bij controleren van package")
            return False

        # Controleer eerst in de status data
        if package_name in self.status_data['packages']:
            # Als er geen versie constraint is, is het package geïnstalleerd
            if not operator:
                return True
                
            # Controleer versie constraint
            installed_version = self.status_data['packages'][package_name].get('version')
            if installed_version:
                if operator == '==':
                    return installed_version == version
                elif operator == '>=':
                    return LooseVersion(installed_version) >= LooseVersion(version)
                elif operator == '<=':
                    return LooseVersion(installed_version) <= LooseVersion(version)
                elif operator == '>':
                    return LooseVersion(installed_version) > LooseVersion(version)
                elif operator == '<':
                    return LooseVersion(installed_version) < LooseVersion(version)
                elif operator == '~=':
                    # Compatible release operator (PEP 440)
                    return LooseVersion(installed_version) >= LooseVersion(version) and \
                           installed_version.split('.')[0] == version.split('.')[0]
                elif operator == '!=':
                    return installed_version != version
        
        # Als we hier komen, is het package niet gevonden in de status data, 
        # of de versie constraint is niet voldaan. Laten we direct controleren.
        try:
            # Voer Python commando uit om te controleren of het package is geïnstalleerd
            if not operator:
                # Controleer alleen of het package is geïnstalleerd
                logger.info(f"Controleren of package {package_name} is geïnstalleerd")
                cmd = f"""
import sys
try:
    import {package_name}
    print('1')
except ImportError:
    print('0')
"""
            else:
                # Controleer versie constraint
                logger.info(f"Controleren of package {package_name} voldoet aan versie constraint {operator}{version}")
                cmd = f"""
import sys
try:
    import {package_name}
    import pkg_resources
    try:
        pkg_dist = pkg_resources.get_distribution('{package_name}')
        print(f'1:{{pkg_dist.version}}')
    except pkg_resources.DistributionNotFound:
        print('0:not-found')
except ImportError:
    print('0:import-error')
"""
            
            # Voeg package directory toe aan PYTHONPATH
            env = os.environ.copy()
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{self.base_dir};{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = self.base_dir
            
            # Voer het commando uit
            result = subprocess.run(
                [self.python_path, "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                startupinfo=self._get_startupinfo()
            )
            
            if result.returncode != 0:
                logger.error(f"Fout bij controleren van package {package_name}: {result.stderr}")
                return False
                
            output = result.stdout.strip()
            logger.info(f"Package check resultaat voor {package_name}: '{output}'")
            
            # Verwerk output
            if not operator:
                # Bewaar in status data
                if output == '1':
                    self.status_data['packages'][package_name] = {
                        'installed': datetime.now().isoformat(),
                        'version': None
                    }
                    self._save_status()
                return output == '1'
                
            # Verwerk versie constraint
            if output.startswith('1:'):
                installed_version = output.split(':')[1]
                
                # Bewaar in status data
                self.status_data['packages'][package_name] = {
                    'installed': datetime.now().isoformat(),
                    'version': installed_version
                }
                self._save_status()
                
                # Vergelijk versies op basis van operator
                if operator == '==':
                    return installed_version == version
                elif operator == '>=':
                    return LooseVersion(installed_version) >= LooseVersion(version)
                elif operator == '<=':
                    return LooseVersion(installed_version) <= LooseVersion(version)
                elif operator == '>':
                    return LooseVersion(installed_version) > LooseVersion(version)
                elif operator == '<':
                    return LooseVersion(installed_version) < LooseVersion(version)
                elif operator == '~=':
                    # Compatible release operator (PEP 440)
                    return LooseVersion(installed_version) >= LooseVersion(version) and \
                           installed_version.split('.')[0] == version.split('.')[0]
                elif operator == '!=':
                    return installed_version != version
                    
            return False
        except Exception as e:
            logger.exception(f"Fout bij controleren of package {package_spec} is geïnstalleerd")
            return False
    
    def install_package(self, package_spec):
        """
        Installeer een package zonder virtuele omgeving.
        
        Args:
            package_spec (str): Package specificatie (bijv. 'requests==2.28.1')
            
        Returns:
            tuple: (success, message)
        """
        if not self.python_path:
            logger.error("Geen Python executable gevonden, kan package niet installeren")
            return False, "Geen Python executable gevonden."
            
        # Controleer of package al is geïnstalleerd
        if self._package_installed(package_spec):
            logger.info(f"Package {package_spec} is al geïnstalleerd.")
            return True, "Package is al geïnstalleerd."
            
        # Installeer het package
        logger.info(f"Package {package_spec} installeren...")
        
        returncode, stdout, stderr = self._run_pip_silently([
            'install',
            package_spec,
            '--target', self.base_dir,
            '--upgrade'
        ])
        
        if returncode != 0:
            logger.error(f"Fout bij installeren van {package_spec}: {stderr}")
            return False, stderr
            
        # Update status data
        package_name, operator, version = self._parse_package_spec(package_spec)
        self.status_data['packages'][package_name] = {
            'installed': datetime.now().isoformat(),
            'spec': package_spec
        }
        
        # Probeer versie-informatie op te halen
        if operator:
            self.status_data['packages'][package_name]['version'] = version
            
        self._save_status()
        
        return True, "Package succesvol geïnstalleerd."
    
    def install_dependencies(self, widget_name, dependencies):
        """
        Installeer alle dependencies voor een widget.
        
        Args:
            widget_name (str): Naam van de widget
            dependencies (list): Lijst van package specificaties
            
        Returns:
            tuple: (all_installed, message)
        """
        if not self.python_path:
            logger.error("Geen Python executable gevonden, kan dependencies niet installeren")
            return False, "Geen Python executable gevonden."
            
        # Controleer elke dependency
        failed_deps = []
        for dep in dependencies:
            success, message = self.install_package(dep)
            if not success:
                failed_deps.append(f"{dep} ({message})")
                
        if failed_deps:
            return False, f"Kon niet alle dependencies installeren: {', '.join(failed_deps)}"
            
        # Update widget status
        self.status_data['widgets'][widget_name] = {
            'installed': datetime.now().isoformat(),
            'dependencies': dependencies
        }
        self._save_status()
        
        return True, "Alle dependencies zijn geïnstalleerd."
    
    def check_dependencies(self, widget_name, dependencies):
        """
        Controleer of alle dependencies voor een widget zijn geïnstalleerd.
        
        Args:
            widget_name (str): Naam van de widget
            dependencies (list): Lijst van package specificaties
            
        Returns:
            tuple: (all_installed, message)
        """
        if not self.python_path:
            logger.error("Geen Python executable gevonden, kan dependencies niet controleren")
            return False, "Geen Python executable gevonden."
            
        # Controleer elke dependency
        missing_deps = []
        for dep in dependencies:
            if not self._package_installed(dep):
                missing_deps.append(dep)
                
        if missing_deps:
            return False, f"Ontbrekende dependencies: {', '.join(missing_deps)}"
            
        return True, "Alle dependencies zijn geïnstalleerd."
    
    def get_package_paths(self):
        """
        Krijg paden naar geïnstalleerde packages.
        
        Deze paden kunnen worden toegevoegd aan sys.path.
        
        Returns:
            list: Lijst van paden naar geïnstalleerde packages
        """
        return [self.base_dir]
    
    def cleanup(self):
        """Ruim ongebruikte packages op."""
        now = datetime.now()
        
        # Zoek packages die langer dan 90 dagen niet zijn gebruikt
        for package_name, package_info in list(self.status_data['packages'].items()):
            # Sla over als geen installatiedatum (zou niet moeten gebeuren, maar voor de zekerheid)
            if 'installed' not in package_info:
                continue
                
            # Parse installatiedatum
            try:
                installed = datetime.fromisoformat(package_info['installed'])
            except ValueError:
                installed = datetime.now() - timedelta(days=365)  # Oude standaard
                
            # Controleer of package ouder is dan 90 dagen en niet is gebruikt
            used = False
            for widget_info in self.status_data['widgets'].values():
                if package_name in [self._parse_package_spec(dep)[0] for dep in widget_info.get('dependencies', [])]:
                    used = True
                    break
                    
            if not used and now - installed > timedelta(days=90):
                logger.info(f"Ongebruikt package opruimen: {package_name}")
                del self.status_data['packages'][package_name]
                
        # Opslaan bijgewerkte status data
        self._save_status()