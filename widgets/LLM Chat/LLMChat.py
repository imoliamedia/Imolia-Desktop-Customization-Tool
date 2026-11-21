"""
LLM Chat Widget for Imolia Desktop Customization Tool

Dependencies:
PyQt5==5.15.6
openai==0.27.0
"""

import base64
import ctypes
import json
import os
import sys
import threading
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QColorDialog,
                             QLabel, QLineEdit, QComboBox, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QColor, QTextCursor
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog
import openai
import logging
import traceback

# Hier stond eerst logging.basicConfig(filename='llm_chat_widget.log', level=DEBUG). Dat zette het
# HELE programma op debug-logging naar een bestand in de werkmap, en de widget schreef daar zijn
# complete configuratie in - inclusief de OpenAI-sleutel in leesbare tekst. Nu loggen we via de
# gewone app-logger en komt de sleutel nergens meer in een log.
logger = logging.getLogger('DesktopCustomizer.LLMChatWidget')


# --- Sleutel versleuteld bewaren (Windows DPAPI: alleen jouw Windows-gebruiker kan het lezen) ---
# Bewust een eigen kopie, hetzelfde als in de Gmail Inbox widget: widgets staan los van elkaar en
# een gedeelde module zou in de gebouwde .exe extra moeten worden meegebouwd.
if sys.platform == 'win32':
    from ctypes import wintypes

    class _DataBlob(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]

    # Eigen WinDLL-exemplaren (niet het gedeelde ctypes.windll.crypt32): anders overschrijven
    # widgets die allebei DPAPI gebruiken elkaars argtypes.
    _crypt32 = ctypes.WinDLL('crypt32')
    _kernel32 = ctypes.WinDLL('kernel32')
    _crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob), wintypes.LPCWSTR, ctypes.POINTER(_DataBlob),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob)]
    _crypt32.CryptProtectData.restype = wintypes.BOOL
    _crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.POINTER(_DataBlob),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob)]
    _crypt32.CryptUnprotectData.restype = wintypes.BOOL
    _kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    _kernel32.LocalFree.restype = ctypes.c_void_p

    def _blob_in(data):
        buffer = ctypes.create_string_buffer(data, len(data))
        return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


def encrypt_secret(plain):
    data = plain.encode('utf-8')
    if sys.platform != 'win32':
        return 'b64:' + base64.b64encode(data).decode('ascii')  # geen echte beveiliging, alleen Windows heeft DPAPI
    blob_in, _keep_alive = _blob_in(data)
    blob_out = _DataBlob()
    if not _crypt32.CryptProtectData(ctypes.byref(blob_in), 'Imolia LLM Chat Widget', None, None, None, 0,
                                     ctypes.byref(blob_out)):
        raise ctypes.WinError()
    try:
        return 'dpapi:' + base64.b64encode(ctypes.string_at(blob_out.pbData, blob_out.cbData)).decode('ascii')
    finally:
        _kernel32.LocalFree(blob_out.pbData)


def decrypt_secret(token):
    kind, _, payload = (token or '').partition(':')
    raw = base64.b64decode(payload)
    if kind == 'b64':
        return raw.decode('utf-8')
    if kind != 'dpapi' or sys.platform != 'win32':
        raise ValueError('Onbekend formaat')
    blob_in, _keep_alive = _blob_in(raw)
    blob_out = _DataBlob()
    if not _crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData).decode('utf-8')
    finally:
        _kernel32.LocalFree(blob_out.pbData)


def ask_openai(api_key, model, user_input):
    """Stel één vraag en geef het antwoord terug.

    Werkt met zowel openai >= 1.0 als met openai 0.27, de versie die bij de app
    wordt meegeleverd. De widget gebruikte alleen de nieuwe API (openai.OpenAI),
    die in 0.27 niet bestaat: daardoor kon de widget nooit verbinden.
    """
    messages = [{"role": "user", "content": user_input}]
    if hasattr(openai, 'OpenAI'):
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content
    response = openai.ChatCompletion.create(model=model, messages=messages, api_key=api_key)
    return response['choices'][0]['message']['content']

class LLMChatWidget(DraggableWidget):
    chat_update = pyqtSignal(str)
    request_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()
        if self._config_needs_migration:
            self.save_config()  # een oude, leesbare sleutel meteen versleuteld opslaan

    _config_needs_migration = False

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'llm_chat_widget_config.json')
        default_config = {
            'api_key': '',
            'model': 'gpt-3.5-turbo',
            'bg_color': '#FFFFFF',
            'text_color': '#000000',
            'button_color': '#4CAF50',
            'size': (400, 600),
            'position': (100, 100)
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                encrypted_key = loaded_config.pop('api_key_enc', '')
                default_config.update(loaded_config)
                if encrypted_key:
                    try:
                        default_config['api_key'] = decrypt_secret(encrypted_key)
                    except Exception:
                        logger.error("De opgeslagen OpenAI-sleutel kan niet worden gelezen; voer hem opnieuw in")
                        default_config['api_key'] = ''
                elif loaded_config.get('api_key'):
                    self._config_needs_migration = True  # leesbare sleutel uit een oudere versie
                logger.debug("Config loaded")
            except Exception as e:
                logger.error(f"Error loading config: {type(e).__name__}")
        return default_config

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'llm_chat_widget_config.json')
        try:
            to_save = dict(self.config)
            api_key = to_save.pop('api_key', '')
            to_save['api_key_enc'] = encrypt_secret(api_key) if api_key else ''
            with open(config_path, 'w') as f:
                json.dump(to_save, f)
            logger.debug("Config saved")
        except Exception as e:
            logger.error(f"Error saving config: {type(e).__name__}")

    def initUI(self):
        try:
            layout = QVBoxLayout(self)

            self.chat_display = QTextEdit()
            self.chat_display.setReadOnly(True)
            layout.addWidget(self.chat_display)

            input_layout = QHBoxLayout()
            self.input_field = QTextEdit()
            self.input_field.setFixedHeight(60)
            self.input_field.installEventFilter(self)
            input_layout.addWidget(self.input_field)

            self.send_button = QPushButton("Send")
            self.send_button.clicked.connect(self.send_message)
            input_layout.addWidget(self.send_button)

            layout.addLayout(input_layout)

            self.new_chat_button = QPushButton("New Chat")
            self.new_chat_button.clicked.connect(self.new_chat)
            layout.addWidget(self.new_chat_button)

            self.setLayout(layout)

            size = self.config.get('size', (400, 600))
            self.resize(*size)

            position = self.config.get('position', (100, 100))
            self.move(*position)

            self.updateStyle()

            self.chat_update.connect(self.update_chat_display)
            self.request_finished.connect(lambda: self.send_button.setEnabled(True))
            logger.debug("UI initialized successfully")
        except Exception as e:
            logger.error(f"Error in initUI: {e}")
            logger.error(traceback.format_exc())

    def new_chat(self):
        try:
            self.chat_display.clear()
            self.chat_display.append("New chat started. How can I assist you?")
            logger.debug("New chat initiated")
        except Exception as e:
            logger.error(f"Error in new_chat: {e}")       

    def eventFilter(self, source, event):
        if (source == self.input_field and
            event.type() == QEvent.KeyPress and
            event.key() == Qt.Key_Return and
            event.modifiers() != Qt.ShiftModifier):
            self.send_message()
            return True
        return super().eventFilter(source, event)        

    def updateStyle(self):
        try:
            bg_color = self.config.get('bg_color', '#FFFFFF')
            text_color = self.config.get('text_color', '#000000')
            button_color = self.config.get('button_color', '#4CAF50')

            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QTextEdit {{
                    border: 1px solid {text_color};
                }}
                QPushButton {{
                    background-color: {button_color};
                    color: white;
                    border: none;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(button_color)};
                }}
            """)
            logger.debug(f"Updated style with colors: bg={bg_color}, text={text_color}, button={button_color}")
        except Exception as e:
            logger.error(f"Error in updateStyle: {e}")

    def lighten_color(self, color):
        try:
            c = QColor(color)
            h, s, l, _ = c.getHsl()
            return QColor.fromHsl(h, s, min(l + 20, 255), 255).name()
        except Exception as e:
            logger.error(f"Error in lighten_color: {e}")
            return color

    # (De aparte "client" is vervangen door ask_openai(), dat per vraag een verbinding maakt.)

    def send_message(self):
        user_input = self.input_field.toPlainText().strip()
        if not user_input:
            return

        self.chat_display.append(f"You: {user_input}")
        self.input_field.clear()

        api_key = self.config.get('api_key', '')
        if not api_key:
            self.chat_display.append("Error: no OpenAI API key set. Please add it in the widget settings.")
            return

        # De vraag gaat op de achtergrond weg: het wachten op OpenAI duurt seconden en
        # mocht eerder het hele bureaublad laten vastlopen.
        self.send_button.setEnabled(False)
        threading.Thread(target=self._ask_in_background, args=(api_key, self.config['model'], user_input),
                         name='LLMChatRequest', daemon=True).start()

    def _ask_in_background(self, api_key, model, user_input):
        try:
            answer = ask_openai(api_key, model, user_input)
            self._emit_safely(self.chat_update, f"AI: {answer}")
        except Exception as e:
            # Alleen het type loggen: OpenAI-foutmeldingen bevatten een deel van de sleutel.
            logger.error(f"OpenAI request failed: {type(e).__name__}")
            self._emit_safely(self.chat_update, f"Error: {e}")
        finally:
            self._emit_safely(self.request_finished)

    @staticmethod
    def _emit_safely(signal, *args):
        try:
            signal.emit(*args)
        except RuntimeError:
            pass  # widget is intussen afgesloten

    def update_chat_display(self, message):
        try:
            self.chat_display.append(message)
            self.chat_display.verticalScrollBar().setValue(
                self.chat_display.verticalScrollBar().maximum()
            )
        except Exception as e:
            logger.error(f"Error in update_chat_display: {e}")

    def updateConfig(self, new_config):
        try:
            self.config.update(new_config)
            self.updateStyle()
            self.save_config()
            logger.debug("Config updated")
        except Exception as e:
            logger.error(f"Error in updateConfig: {e}")

    def openSettings(self):
        try:
            dialog = LLMChatSettingsDialog(self)
            if dialog.exec_():
                new_config = dialog.get_config()
                self.updateConfig(new_config)
        except Exception as e:
            logger.error(f"Error in openSettings: {e}")

class LLMChatSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def add_custom_section(self, layout):
        
            api_layout = QHBoxLayout()
            api_layout.addWidget(QLabel("OpenAI API Key:"))
            self.api_key_input = QLineEdit()
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.api_key_input.setText(self.widget.config.get('api_key', ''))
            api_layout.addWidget(self.api_key_input)
            layout.addLayout(api_layout)

            model_layout = QHBoxLayout()
            model_layout.addWidget(QLabel("Model:"))
            self.model_combo = QComboBox()
            self.model_combo.addItems([
                'gpt-4o',
                'gpt-4',
                'gpt-4-0613',
                'gpt-4-32k',
                'gpt-4-32k-0613',
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k',
                'gpt-3.5-turbo-0613',
                'gpt-3.5-turbo-16k-0613'
            ])
            current_model = self.widget.config.get('model', 'gpt-3.5-turbo')
            index = self.model_combo.findText(current_model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
            model_layout.addWidget(self.model_combo)
            layout.addLayout(model_layout)

            self.add_color_setting(layout, "Background Color", self.widget.config['bg_color'], 'bg_color')
            self.add_color_setting(layout, "Text Color", self.widget.config['text_color'], 'text_color')
            self.add_color_setting(layout, "Button Color", self.widget.config['button_color'], 'button_color')

    def add_color_setting(self, layout, label, initial_color, config_key):
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel(label))
        color_button = QPushButton()
        color_button.setStyleSheet(f"background-color: {initial_color};")
        color_button.clicked.connect(lambda: self.choose_color(color_button, config_key))
        color_layout.addWidget(color_button)
        layout.addLayout(color_layout)

    def choose_color(self, button, config_key):
        color = QColorDialog.getColor(QColor(self.widget.config[config_key]))
        if color.isValid():
            self.widget.config[config_key] = color.name()
            button.setStyleSheet(f"background-color: {color.name()};")

    def get_config(self):
        return {
            'api_key': self.api_key_input.text(),
            'model': self.model_combo.currentText(),
            'bg_color': self.widget.config['bg_color'],
            'text_color': self.widget.config['text_color'],
            'button_color': self.widget.config['button_color']
        }
        
# Important: The class must be named 'Widget' for the loader to recognize it
Widget = LLMChatWidget