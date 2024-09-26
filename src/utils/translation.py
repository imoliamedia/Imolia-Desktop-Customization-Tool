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