from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox, QPushButton
from PyQt5.QtCore import Qt
from src.utils.translation import _, update_language

class SettingsWindow(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(_("Settings"))
        self.setGeometry(300, 300, 300, 200)  # Set a default size and position
        layout = QVBoxLayout()

        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel(_("Language:")))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['English', 'Nederlands'])
        self.lang_combo.setCurrentText(self.settings.get('language', 'English'))
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Start with Windows option
        self.start_with_windows = QCheckBox(_("Start with Windows"))
        self.start_with_windows.setChecked(self.settings.get('start_with_windows', False))
        layout.addWidget(self.start_with_windows)

        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton(_("Save"))
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton(_("Cancel"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def save_settings(self):
        new_language = 'en' if self.lang_combo.currentText() == 'English' else 'nl'
        if new_language != self.settings.get('language'):
            self.settings.set('language', new_language)
            update_language(new_language)
        
        self.settings.set('start_with_windows', self.start_with_windows.isChecked())
        self.accept()

    def showEvent(self, event):
        print("Settings window is being shown")  # Debug print
        super().showEvent(event)

    def closeEvent(self, event):
        print("Settings window is being closed")  # Debug print
        super().closeEvent(event)