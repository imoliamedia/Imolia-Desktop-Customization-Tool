"""
LLM Chat Widget for Imolia Desktop Customization Tool

Dependencies:
PyQt5==5.15.6
openai==0.27.0
"""

import json
import os
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QColorDialog,
                             QLabel, QLineEdit, QComboBox, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QColor, QTextCursor
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog
import openai
import logging
import traceback

logging.basicConfig(level=logging.DEBUG, filename='llm_chat_widget.log', filemode='w')
logger = logging.getLogger(__name__)

class LLMChatWidget(DraggableWidget):
    chat_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()
        self.openai_client = None
        self.initialize_openai_client()

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
                    default_config.update(loaded_config)
                logger.debug(f"Loaded config: {default_config}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        return default_config

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'llm_chat_widget_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f)
            logger.debug(f"Saved config: {self.config}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

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

    def initialize_openai_client(self):
        api_key = self.config.get('api_key', '')
        if api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.debug("OpenAI client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.chat_display.append(f"Error: Failed to connect to OpenAI. Please check your API key. Details: {e}")
        else:
            logger.warning("No API key provided. OpenAI client not initialized.")

    def send_message(self):
        user_input = self.input_field.toPlainText().strip()
        if not user_input:
            return

        self.chat_display.append(f"You: {user_input}")
        self.input_field.clear()

        if not self.openai_client:
            self.initialize_openai_client()
            if not self.openai_client:
                self.chat_display.append("Error: OpenAI client not initialized. Please check your API key in settings.")
                return

        try:
            response = self.openai_client.chat.completions.create(
                model=self.config['model'],
                messages=[{"role": "user", "content": user_input}]
            )
            ai_response = response.choices[0].message.content
            self.chat_update.emit(f"AI: {ai_response}")
        except openai.APIError as e:
            logger.error(f"OpenAI API Error: {e}")
            self.chat_update.emit(f"Error: OpenAI API Error - {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in API call: {e}")
            logger.error(traceback.format_exc())
            self.chat_update.emit(f"Error: An unexpected error occurred. Details: {str(e)}")

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
            self.initialize_openai_client()
            logger.debug(f"Config updated: {self.config}")
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
                'gpt-3.5-turbo-16k-0613',
                'text-davinci-003',
                'text-davinci-002',
                'code-davinci-002'
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