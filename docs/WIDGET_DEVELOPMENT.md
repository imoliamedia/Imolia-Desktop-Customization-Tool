# Comprehensive Widget Development Guide for Imolia Desktop Customizer

## Table of Contents
1. [Introduction](#introduction)
2. [Setting Up Your Development Environment](#setting-up-your-development-environment)
3. [Widget Basics](#widget-basics)
4. [Creating Your First Widget](#creating-your-first-widget)
5. [Widget Configuration and Customization](#widget-configuration-and-customization)
6. [Styling Your Widget](#styling-your-widget)
7. [Making Your Widget Resizable and Draggable](#making-your-widget-resizable-and-draggable)
8. [Implementing Regular Updates](#implementing-regular-updates)
9. [Saving Configuration Without Flooding the Disk](#saving-configuration-without-flooding-the-disk)
10. [Doing Slow Work Without Freezing the Desktop](#doing-slow-work-without-freezing-the-desktop)
11. [Storing Secrets](#storing-secrets)
12. [Creating a Widget Settings Dialog](#creating-a-widget-settings-dialog)
13. [Advanced Widget Features](#advanced-widget-features)
14. [Best Practices](#best-practices)
15. [Testing Your Widget](#testing-your-widget)
16. [Adding Your Widget to the Application](#adding-your-widget-to-the-application)
17. [Handling Dependencies](#handling-dependencies)
18. [Error Handling and Logging](#error-handling-and-logging)
19. [Troubleshooting Common Issues](#troubleshooting-common-issues)
20. [Example Widgets](#example-widgets)

## Introduction
This guide provides comprehensive instructions for developing widgets for the Imolia Desktop Customizer. By following this guide, you'll be able to create custom widgets that seamlessly integrate with the application.

## Setting Up Your Development Environment
1. Ensure you have Python 3.9 or higher installed.
2. Clone the Imolia Desktop Customizer repository:
   ```
   git clone https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool.git
   ```
3. Create and activate a virtual environment (the program is for Windows):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the program with `python main.py`. Your widgets are loaded from `Documents\Imolia Desktop Customizer Widgets`, see [Adding Your Widget to the Application](#adding-your-widget-to-the-application).

For how the program is put together, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Widget Basics
All widgets in the Imolia Desktop Customizer should inherit from the `DraggableWidget` class, which provides essential functionality:
- Dragging and resizing capabilities
- Basic configuration management
- Integration with the main application

Key concepts:
- Widgets are self-contained modules
- Each widget manages its own configuration
- Widgets can be resized and moved by the user
- Widgets should have their own settings dialog
- Calls to your `save_config()` are bundled, see [Saving Configuration Without Flooding the Disk](#saving-configuration-without-flooding-the-disk)

## Creating Your First Widget
Here's a template for creating a basic widget, following the same
`DraggableWidget` + `WidgetSettingsDialog` pattern used by every bundled
widget (clock, calculator, system monitor, ...) - not the standalone
`BaseWidgetSettingsDialog` utility class, which exists in the codebase but
isn't actually used by any real widget:

```python
"""
MyCustomWidget

Dependencies:
PyQt5==5.15.6
"""

import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from src.utils.draggable_widget import DraggableWidget, WidgetSettingsDialog

class MyCustomWidget(DraggableWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.initUI()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'my_custom_widget_config.json')
        default_config = {
            'color': 'white',
            'size': (200, 100),
            'position': (100, 100),
        }
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        return default_config

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'my_custom_widget_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        layout = QVBoxLayout()
        self.label = QLabel("Hello, I'm a custom widget!")
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setMinimumSize(100, 50)
        size = self.config.get('size', (200, 100))
        self.resize(*size)

        position = self.config.get('position', (100, 100))
        self.move(*position)

        self.updateStyle()

    def updateStyle(self):
        color = self.config.get('color', 'white')
        self.setStyleSheet(f"""
            QWidget {{
                color: {color};
                background-color: rgba(0, 0, 0, 100);
                border-radius: 10px;
            }}
        """)
        self.adjustFontSize()

    def adjustFontSize(self):
        font = QFont()
        font.setPixelSize(int(self.height() * 0.2))
        self.label.setFont(font)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustFontSize()
        self.config['size'] = (self.width(), self.height())
        self.save_config()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config['position'] = (self.x(), self.y())
        self.save_config()

    def updateConfig(self, new_config):
        self.config.update(new_config)
        self.updateStyle()
        self.save_config()

    def openSettings(self):
        dialog = MyCustomWidgetSettingsDialog(self)
        if dialog.exec_():
            new_config = dialog.get_config()
            self.updateConfig(new_config)

class MyCustomWidgetSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def add_custom_section(self, layout):
        # Add your widget-specific settings here. If you want a color
        # picker, see "Creating a Widget Settings Dialog" below - the
        # base class's own get_config() expects a self.color_button to
        # exist, so skipping it will crash the dialog on Save.
        pass

    def get_config(self):
        config = super().get_config()
        # Add your widget-specific fields to the returned dict here.
        return config

# Important: The class must be named 'Widget' for the loader to recognize it
Widget = MyCustomWidget
```

## Widget Configuration and Customization
- Use a `config` dictionary to store customizable properties.
- Implement `load_config()` and `save_config()` methods for persistent storage.
- Use `updateConfig()` for dynamic updates to the widget's appearance and behavior.

## Styling Your Widget
- Implement the `updateStyle` method to apply styles based on the configuration.
- Use Qt stylesheets for complex styling.
- Consider using transparent backgrounds for better desktop integration.

## Making Your Widget Resizable and Draggable
The `DraggableWidget` base class provides basic functionality for resizing and moving. 
- Override `resizeEvent` and `moveEvent` to handle size and position changes.
- Save the new size and position in these events to persist them.

## Implementing Regular Updates
If your widget needs to update regularly (e.g., a clock or system monitor):
1. Set up a QTimer in your `initUI` method:
   ```python
   self.timer = QTimer(self)
   self.timer.timeout.connect(self.update_widget)
   self.timer.start(1000)  # Update every 1000 ms
   ```
2. Implement the `update_widget` method:
   ```python
   def update_widget(self):
       # Update your widget's content here
       pass
   ```

Keep this method fast. Anything that can take a moment (a network request, starting another program, reading many files) must not run here - see [Doing Slow Work Without Freezing the Desktop](#doing-slow-work-without-freezing-the-desktop). Wrap the body in `try/except` and log the error: an exception in a timer callback is raised again at every tick.

## Saving Configuration Without Flooding the Disk
`DraggableWidget` wraps the `save_config()` of every widget that inherits from it so that writes are **bundled**. Calling `self.save_config()` returns immediately; your own `save_config()` runs once, about 0.4 seconds after the *last* call, and writes whatever `self.config` contains at that moment. Pending changes are always written when the widget is closed and when the program quits.

What this means for you:
- You can call `save_config()` freely, for example in `moveEvent`, `resizeEvent` or on every keystroke. Dragging a widget used to rewrite the file for every mouse movement.
- If you need the file on disk right now, call `self.flush_config()`.
- Keep `save_config()` itself simple: it should only write `self.config` (or other state) to disk. Calls made from a thread other than the main thread are executed immediately, not bundled.
- If you override `closeEvent`, call `super().closeEvent(event)` so pending changes are written.

## Doing Slow Work Without Freezing the Desktop
Qt draws and handles the mouse on one thread. If your widget waits for a network answer or a slow program on that thread, **the whole desktop freezes** (the overlay and every other widget share it). Do slow work in a background thread and hand the result back with a **signal**, which Qt delivers on the main thread:

```python
import threading
from PyQt5.QtCore import pyqtSignal

class MyWidget(DraggableWidget):
    result_ready = pyqtSignal(object)          # emitted from the thread, received on the UI thread

    def __init__(self):
        super().__init__()
        self._busy = False
        self.result_ready.connect(self.on_result)

    def refresh(self):
        if self._busy:                         # never start two jobs at once
            return
        self._busy = True
        threading.Thread(target=self._work, daemon=True).start()

    def _work(self):                           # runs in the background: do NOT touch any widget here
        try:
            data = download_something()        # slow
        except Exception as e:
            data = e
        try:
            self.result_ready.emit(data)
        except RuntimeError:                   # the widget was closed in the meantime
            pass

    def on_result(self, data):                 # back on the UI thread: update the interface here
        self._busy = False
        ...
```

Show the last known data while a refresh runs or fails, instead of a blank widget. Examples in this project: the Gmail Inbox, Google Calendar and System Overview widgets.

## Storing Secrets
Never keep passwords or API keys as plain text in your widget's `_config.json`. The Gmail Inbox and LLM Chat widgets encrypt them with **Windows DPAPI** through `ctypes` (`CryptProtectData` / `CryptUnprotectData`), which ties the secret to the current Windows user on this PC. Look at `encrypt_password()` / `encrypt_secret()` in those widgets. Two things to copy exactly:
- Create your own library object, `ctypes.WinDLL('crypt32')`, instead of using the shared `ctypes.windll.crypt32`. Widgets set `argtypes` on the functions, and the shared object makes two widgets overwrite each other's settings, which breaks the encryption of whichever loaded first.
- Never write a secret, or the content of what the user typed, to the log; log the *type* of an error instead.

Say in your README which data your widget sends where.

## Creating a Widget Settings Dialog
Use `WidgetSettingsDialog` (from `src.utils.draggable_widget`) to create a
consistent settings experience - this is the base class every bundled
widget's settings dialog actually inherits from. It already builds the
dialog's "Save"/"Cancel" buttons and a "Behavior" section with an
update-interval spinner; you only need to override `add_custom_section()`
(to add your own fields to the UI) and `get_config()` (to include their
values in the dict that gets saved):

```python
from PyQt5.QtWidgets import QLineEdit, QLabel, QHBoxLayout
from src.utils.draggable_widget import WidgetSettingsDialog

class MyWidgetSettingsDialog(WidgetSettingsDialog):
    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

    def add_custom_section(self, layout):
        setting_layout = QHBoxLayout()
        setting_layout.addWidget(QLabel("My Setting:"))
        self.my_setting_input = QLineEdit(self.widget.config.get('my_setting', ''))
        setting_layout.addWidget(self.my_setting_input)
        layout.addLayout(setting_layout)

    def get_config(self):
        config = super().get_config()
        config.update({
            'my_setting': self.my_setting_input.text(),
        })
        return config
```

Saving is already wired up for you: the dialog's "Save" button calls
`get_config()` and passes the result to `widget.updateConfig()`, which
merges it into `widget.config` and calls `save_config()`. You don't need
to (and shouldn't) write your own save button or call `save_config()`
directly from the dialog.

**A gotcha worth knowing:** `WidgetSettingsDialog`'s own `get_config()`
tries to read a color from `self.color_button` (via its Qt palette). If
your `add_custom_section()` doesn't create a `self.color_button`, calling
`super().get_config()` will raise an `AttributeError` the moment the user
clicks "Save" - a real bug that shipped in the System Monitor widget for a
while. If you want a color picker, follow `clock_widget.py`'s pattern:

```python
from PyQt5.QtWidgets import QPushButton, QColorDialog
from PyQt5.QtGui import QColor

def add_custom_section(self, layout):
    self.color_button = QPushButton()
    self.color_button.setStyleSheet(f"background-color: {self.widget.config.get('color', 'white')};")
    self.color_button.clicked.connect(self.choose_color)
    layout.addWidget(self.color_button)

def choose_color(self):
    # Override this too: setStyleSheet() doesn't update the button's
    # QPalette, so the base class's palette-based color read would
    # otherwise always return the wrong (default) color.
    color = QColorDialog.getColor(QColor(self.widget.config.get('color', 'white')))
    if color.isValid():
        self.color_button.setStyleSheet(f"background-color: {color.name()};")
        self.widget.config['color'] = color.name()

def get_config(self):
    config = super().get_config()
    config['color'] = self.widget.config.get('color', 'white')
    return config
```

If you don't need a color picker at all, just don't call
`super().get_config()` - build and return your own dict from
`get_config()` instead (see the ESP32 Web Dashboard widget for an example
of a settings dialog with no color/behavior section at all).

## Advanced Widget Features
- Implement custom context menus for additional functionality.
- Use Qt's event system for complex interactions.
- Consider adding keyboard shortcuts for power users.

## Best Practices
- Follow PEP 8 style guidelines.
- Use meaningful variable and function names.
- Comment your code, especially for complex logic.
- Handle errors gracefully, especially when loading/saving configurations.
- Optimize for performance, especially if your widget updates frequently.

## Testing Your Widget
Put tests in `tests/test_<your_widget>.py`; [tests/README.md](../tests/README.md) explains how the test suite works and has more detail. In short:
- A widget is a plain `.py` file, so load it with `importlib.util.spec_from_file_location(...)`. A widget saves its config next to its own file; to keep the repository clean, copy the file to a temporary folder first (the `test_llm_chat_widget.py` tests do this).
- Set `os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')` **before** creating a `QApplication`, so the tests run without a screen (also in CI).
- Create as few Qt widgets as you can - one per test class, in `setUpClass` - and reset their state in `setUp`.
- **Never use the real network.** Patch the function that connects (see how the Gmail tests replace `imaplib.IMAP4_SSL`), and use clearly fake addresses such as `test.persoon@example.com`.
- Do not let timers or threads outlive your test class: a `QTimer.singleShot(...)` started in your widget's `__init__` fires later, during *another* test module. Patch it while creating the widget and stop the widget's timers in the class cleanup.
- Test the logic that does not need Qt (parsing, formatting, encryption) directly, and check it also behaves when an optional module is missing.

## Adding Your Widget to the Application
There are two situations.

**For your own use:**
1. Implement your widget as described in this guide, in a single `.py` file.
2. Ensure the main widget class is aliased as `Widget` (`Widget = MyCustomWidget`). The program recognises a widget by this line.
3. Copy the file **directly** into your widgets folder, `Documents\Imolia Desktop Customizer Widgets` (open it with **Open Widgets Map** in the Settings window). Subfolders are not scanned.
4. Click **Vernieuwen** in the Settings window, or restart the program. Tick your widget and click **Opslaan**.

**To contribute it to the project:** add a folder `widgets/<widget_name>/` containing the widget file, a `README.md` and a `screenshots/` folder, and follow the checklist in [widgets/README.md](../widgets/README.md#contributing-widgets-to-the-project) - including the GPL license header that the other files start with, and an entry in the [CHANGELOG](../CHANGELOG.md).

The program copies the `.py` files of the bundled widgets into the user's widgets folder at start, but only when no file with that name exists yet.

## Handling Dependencies
Dependencies are declared declaratively, not installed by your own code -
there is no `install_dependencies()` method to implement.

List every dependency as one `package==version` line per line, inside a
`Dependencies:` block in your widget file's module docstring:

```python
"""
MyCustomWidget

Dependencies:
PyQt5==5.15.6
requests==2.28.1
"""
```

`WidgetManager` parses this block automatically (see
`parse_dependencies()` in `src/utils/widget_loader.py`) and installs
anything missing via `PackageManager` before your widget is activated -
you don't write or call any install logic yourself. `PyQt5` is assumed
and doesn't strictly need to be listed, but doing so anyway is the
convention every bundled widget follows.

A few things worth knowing about how this works in practice:
- If the exact package (and version) is already importable in the running
  process - true for anything the app was built with, like `psutil` or
  `requests` - it's used as-is; nothing gets reinstalled.
- Otherwise, dependencies are installed into the app's own managed
  packages folder (`%APPDATA%\Imolia Desktop Customizer\packages`) via
  pip, using an embedded Python interpreter when running as a packaged
  `.exe`. This requires internet access and can take a moment the first
  time a genuinely new dependency is needed.
- **Packages with compiled parts (C extensions) can't be installed this way
  in the packaged `.exe`.** The embedded Python used for installing is a
  different version (3.13) than the one the `.exe` runs on (3.12), so a
  compiled package it installs can't be imported. Pure-Python packages are
  fine. For anything compiled (like `psutil`), add it to `hiddenimports` in
  `Imolia Desktop Customizer.spec` so it's bundled when the app is built.
  The same goes for standard-library modules that only a widget uses, such as
  `imaplib` and `winsound` (used by the Gmail Inbox widget): PyInstaller only
  includes what the app itself imports, so a widget needing more fails with
  `ModuleNotFoundError` in the `.exe` until the module is listed there and the
  app is rebuilt.
- Pin exact versions. An unpinned or since-removed version can make
  installation fail outright - `requests==2.22.1` in this project's own
  `requirements.txt` did exactly that after PyPI stopped distributing it.

## Error Handling and Logging
The program writes its log to `%APPDATA%\Imolia Desktop Customizer\logs\app.log` (it rotates at 2 MB). Only loggers whose name starts with `DesktopCustomizer` end up in that file, so name yours like this:

```python
import logging

logger = logging.getLogger('DesktopCustomizer.MyWidget')

# Usage
logger.debug("Debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

- **Do not use `logging.getLogger(__name__)`**: that logger is not under `DesktopCustomizer`, so your messages never reach `app.log` (users are told to look there when something goes wrong).
- **Never call `logging.basicConfig()`** in a widget. It reconfigures logging for the whole program (and, with a filename, writes a log file into the working directory).
- Log important events, errors, and state changes in your widget, but never secrets or what the user typed.
- Use try-except blocks to handle potential errors gracefully, especially in timer callbacks and signal handlers: an unhandled exception there is reported to the user (once per distinct error) and logged as critical.

## Troubleshooting Common Issues
- Widget not appearing: 
  - Check if it's properly registered in the widget manager.
  - Verify that all dependencies are correctly installed.
  - Check the application logs for any error messages during widget initialization.
- Styling issues: 
  - Ensure all style properties are properly set and updated.
  - Verify that the `updateStyle` method is called after any configuration changes.
- Performance problems: 
  - Profile your code and optimize heavy operations.
  - Consider using background threads for time-consuming tasks.
- Configuration not saving:
  - Verify the `save_config` method is called appropriately.
  - Check file permissions for the configuration file location.
  - If you copy a widget file to run multiple instances, make sure each
    copy's config filename is derived from its own filename (see the
    ESP32 Web Dashboard widget) - a fixed filename means every copy
    overwrites the same shared file.
- Settings dialog crashes on Save:
  - If your `get_config()` calls `super().get_config()`, make sure
    `add_custom_section()` created a `self.color_button` - see the
    gotcha explained under "Creating a Widget Settings Dialog".
- Dependency issues:
  - Double-check the `Dependencies:` block in your widget's docstring -
    package names and versions must match exactly what's installable
    from PyPI (a removed/yanked version will fail every time).
  - Installing a new dependency in a packaged `.exe` requires internet
    access; check the app log if it seems to hang or fail silently.

## Example Widgets
For more detailed examples, refer to the following widgets in the `widgets` folder:
- Clock Widget - color picker + font/format settings, the reference `choose_color`/`get_config` pattern
- System Monitor Widget - a periodic `QTimer` update, with its own defensive error handling
- System Overview Widget - a custom-painted interface (`QPainter`), live graphs, and measuring in a background thread
- Calculator Widget, Modern Todo Widget, Quick Notes Widget, Pomodoro Productivity Timer Widget - small, simple widgets
- Google Calendar Widget - fetching data from the network in a background thread, with a cache of the last result
- Gmail Inbox Widget - the most complete example: background threads and signals, encrypted passwords (DPAPI), a custom-painted interface with an embedded text view, graceful behavior when an optional module is missing, and an extensive test file
- LLM Chat Widget - an API key stored encrypted, a request in a background thread, and support for two versions of a library
- ESP32 Web Dashboard Widget - `QWebEngineView`, a fully custom settings dialog with no color/behavior section, and a per-file (not fixed) config filename to safely support running multiple copies at once

These examples demonstrate various techniques and best practices for widget development.

Remember to thoroughly test your widget in various scenarios and with different configurations to ensure stability and performance. Always provide clear error messages and logging to help diagnose issues that may arise during development or use.
