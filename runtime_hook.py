import os
import sys

def runtime_hook():
    if getattr(sys, 'frozen', False):
        # We zijn in een PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # We draaien in een normale Python-omgeving
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Stel het pad in naar de widgets map in de gebruikers' Documenten
    widgets_path = os.path.expanduser("~/Documents/Imolia Desktop Customizer Widgets")
    os.environ['IMOLIA_WIDGETS_PATH'] = widgets_path

    # Voeg het pad toe aan sys.path zodat Python de modules kan vinden
    if widgets_path not in sys.path:
        sys.path.append(widgets_path)