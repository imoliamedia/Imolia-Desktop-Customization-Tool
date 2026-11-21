# Architecture

How Imolia Desktop Customizer is put together. For using the program see the [User Guide](USER_GUIDE.md); for writing a widget see the [Widget Development Guide](WIDGET_DEVELOPMENT.md).

## The big picture

```
main.py ──► Settings ──► %APPDATA%\Imolia Desktop Customizer\settings.json
   │
   ├──► Overlay  (transparent window over all screens, holds the widgets)
   │       ├── WidgetManager ──► scans Documents\Imolia Desktop Customizer Widgets\*.py
   │       │        └── PackageManager ──► installs missing widget dependencies (embedded Python + pip)
   │       ├── widget_seeder ──► copies the bundled widgets there if missing
   │       └── widgets: DraggableWidget subclasses, one per active widget
   │
   └──► SystemTrayIcon ──► SettingsWindow ──► WidgetManagerDialog / WidgetInstallationDialog
```

| Piece | File |
|---|---|
| Start-up, error handling | `main.py` |
| The overlay | `src/core/overlay.py` |
| Tray icon and its menu | `src/core/tray_icon.py` |
| Settings window, widget manager, installation dialog | `src/gui/` |
| Finding, loading and activating widgets | `src/utils/widget_loader.py` |
| Installing widget dependencies | `src/utils/package_manager.py` |
| Copying the bundled widgets to the user | `src/utils/widget_seeder.py` |
| Application settings | `src/utils/settings.py` |
| Base class of every widget and the standard settings dialog | `src/utils/draggable_widget.py` |
| Logging | `src/utils/logger.py` |
| Names and folder constants | `src/config.py` |

## Start-up (`main.py`)

1. When running as a PyInstaller build (`sys.frozen`), the file first prepares the environment: the embedded Python and its `Scripts` folder are put on `PATH`, and `QT_QPA_PLATFORM_PLUGIN_PATH` and the Qt DLL folder are set (needed because PyInstaller 6 nests data under `_internal`). In every run, also from source, the QtWebEngine flags `--disable-gpu --disable-gpu-compositing --disable-software-rasterizer` are set (unless already set): Chromium's GPU rendering conflicted with the transparent overlay and could black out the screen and hide the taskbar.
2. `QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)` is set at module level, before any `QApplication` exists, because the ESP32 widget loads `QtWebEngineWidgets` only later.
3. `sys.excepthook` is replaced: an uncaught exception is logged and shown in a message box **once per distinct error**, the program keeps running (Qt keeps its event loop going after an error in a slot).
4. The logger is set up, then `Settings`, `Overlay` and `SystemTrayIcon` are created. A failure here shows a message box and exits.

## The overlay (`src/core/overlay.py`)

- A frameless, translucent window (`WindowStaysOnBottomHint | Tool`), so it sits at the bottom of the window stack: widgets are visible on the desktop, normal windows cover them.
- Its geometry is the union of **all screens**, made 1 pixel smaller than the screen. A borderless window that exactly covers a monitor is treated by Windows as a fullscreen game, which could make the desktop compositor black out the screen.
- It is clickable only where a widget is: every 250 ms `update_click_through_mask()` sets a mask (`setMask`) containing the geometries of the visible widgets, so clicks elsewhere fall through to the desktop.
- `load_active_widgets()` activates the widgets named in settings and deactivates the rest. Each widget becomes a child of the overlay; its saved size and position are clamped to the screen, because a configuration may come from another monitor setup.
- If a widget cannot be activated, a message box says so; the details are in the log.

## Widgets (`src/utils/draggable_widget.py`)

Every widget is a `DraggableWidget` (a frameless `QWidget` with a translucent background) that handles dragging and a resize handle in the bottom-right corner. A widget provides `load_config()`, `save_config()`, `updateConfig()` and `openSettings()`, and ends its file with `Widget = <ClassName>`.

`DraggableWidget` wraps each subclass's `save_config()` (through `__init_subclass__`) so that calls are **bundled**: the write happens about 0.4 s after the last call, and always on `closeEvent` and `aboutToQuit` (`flush_config()`). Before this, dragging rewrote the config file for every mouse move.

`WidgetSettingsDialog` is the standard settings dialog (Save/Cancel and an update-interval spinner); widgets add their own fields through `add_custom_section()` and `get_config()`.

## Finding, loading and activating widgets (`widget_loader.py`)

- **Scanning** (`WidgetManager.scan_widgets`): every `*.py` directly in the widgets folder is a candidate; subfolders are not scanned. A file counts as a widget when it contains `Widget = <name>` (`is_valid_widget_file`). The name shown in the settings is made from the file name (`LLMChat.py` becomes "Llmchat").
- **Dependencies** (`parse_dependencies`): read from a `Dependencies:` block in the module docstring (one `package==version` per line). If there is none, `<name>_requirements.txt` or `<name>_dependencies.json` next to the widget are tried. `PyQt5==5.15.6` is always added.
- **Activating** (`activate_widget`): check the dependencies (installing them first if needed, in a background thread), import the file with `importlib` (the widgets folder and the packages folder are put on `sys.path` for the import), and instantiate its `Widget`. A module is imported once per process, so a changed widget file is picked up after a restart.
- **Deactivating**: `widget.close()` and forget the instance.

Because widgets are imported by file name, two widget files with the same name cannot coexist.

## Dependencies (`package_manager.py`)

1. First check whether the package is already importable in the running process (true for everything bundled into the `.exe`, and for packages in a source environment); if so nothing is installed.
2. Otherwise run `pip install <package> --target %APPDATA%\Imolia Desktop Customizer\packages` with the **embedded Python** (`embedded_python\python.exe`, a portable Python 3.13, see [its README](../embedded_python/README.md)). pip itself is set up on first use (`ensurepip`, or else `get-pip.py` is downloaded). A pip cache lives in `pip_cache` and the installed packages are recorded in `packages_status.json`, both next to the `packages` folder.

Limitations: the embedded Python (3.13) is not the Python the `.exe` runs on (3.12), so packages with compiled extension modules installed this way cannot be imported; they must be bundled into the build instead (`hiddenimports`, see below). Versions are compared with a small `LooseVersion` class in this file (the standard `distutils` was removed in Python 3.12).

## Seeding the widgets (`widget_seeder.py`)

At every start, `seed_default_widgets()` copies the `.py` file of each bundled widget (from the project's `widgets/` folder, or from the build's data) into the user's widgets folder **if no file with that name exists there**. Existing files are never overwritten, so a user's edits survive; the flip side is that improved bundled widgets do not reach users who already have an older copy until they replace the file (see [Updating](USER_GUIDE.md#9-updating)).

## Settings (`settings.py`)

`settings.json` lives in `%APPDATA%\Imolia Desktop Customizer\` and mainly holds `active_widgets`. A `settings.json` from an older version (next to the `.exe` or in the working directory) is copied there once if no new file exists. Each widget's own settings are **not** in this file: they live next to the widget as `<file name>_config.json`.

## Logging (`logger.py`)

Handlers are attached to the logger named `DesktopCustomizer`: a rotating file handler (`%APPDATA%\Imolia Desktop Customizer\logs\app.log`, 2 MB, three backups) and a console handler at INFO. Every module and widget logs through a child logger (`DesktopCustomizer.<Name>`) so its messages end up in the same file.

## The windows (`src/gui/`)

- `SettingsWindow`: one window with the widget list (checkbox, name, dependency status or an **Installeer** button, a settings button) and the buttons **Open Widgets Map**, **Widgets Beheren**, **Vernieuwen**, **Opslaan** and **Annuleren**. Saving checks the dependencies of every ticked widget, stores `active_widgets`, and calls `Overlay.load_active_widgets()`, so no restart is needed.
- `WidgetManagerDialog`: a list of all widgets with their dependency status and an **Installeren** button.
- `WidgetInstallationDialog`: shows the progress of an installation.
- `SystemTrayIcon`: left-click toggles the overlay, the right-click menu has *Toggle Overlay*, *Settings* and *Exit*.

## Packaging (`Imolia Desktop Customizer.spec`)

The build is a PyInstaller one-directory build. `datas` adds `resources`, `src`, `widgets` and `embedded_python` as plain files; `hiddenimports` lists what PyInstaller cannot see because widgets are loaded at run time: `psutil`, `icalendar`, `recurring_ical_events`, `requests`, `openai`, `PyQt5.QtWebEngineWidgets`, and the standard-library modules only widgets use (`imaplib`, `html.parser`, `winsound`). A widget that needs a module that is not in the build fails with `ModuleNotFoundError` in the `.exe`; the fix is to list the module in `hiddenimports` and rebuild. See [RELEASING.md](RELEASING.md).

`runtime_hook.py` runs inside the build at start-up and sets `IMOLIA_WIDGETS_PATH` and appends the widgets folder to `sys.path`; nothing in the program reads that variable.

## Rules that keep the desktop responsive

- All widgets and the overlay share one UI thread: never block it. Do network and slow work in a thread and return results with a signal (see the [Widget Development Guide](WIDGET_DEVELOPMENT.md#doing-slow-work-without-freezing-the-desktop)).
- Never block start-up on the network: dependency installs run in a background thread.
- Do not log secrets.
