# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-11-21
### Added
- New **Gmail Inbox** widget: the unread mail of several Gmail accounts at
  once, checked every X minutes. Give each account a display name so no
  address is visible on screen. Click a mail to read it **inside the widget**
  (text, or a simplified, safe version of formatted mails: images are never
  loaded and scripts, frames and forms are removed), mark it as read or move
  it to the trash from there. Choose your own notification sound and use the
  do-not-disturb button. Signs in with Google app passwords over IMAP; the
  passwords are stored encrypted with Windows DPAPI.
- New **System Overview** widget: a Task Manager-style dashboard showing CPU,
  memory, GPU, GPU memory, network and disk at once, each with a live graph.
  Includes GPU temperature and power draw (NVIDIA); CPU temperature is shown
  when LibreHardwareMonitor/OpenHardwareMonitor is running.
- New documents: `docs/TROUBLESHOOTING.md`, `docs/ARCHITECTURE.md`,
  `docs/RELEASING.md`, `tests/README.md`, `embedded_python/README.md`,
  `SECURITY.md`, a feature-request issue template and a pull request template.
  READMEs and screenshots for the widgets that had none, and a screenshot of a
  desktop in the main README.
- A `release/README.md` for the download and release notes per version in
  `docs/releases/`.

### Changed
- Documentation overhaul: the User Guide, all widget READMEs, the Widget
  Development Guide, CONTRIBUTING and the issue template were checked against
  the program and corrected (for example the settings window has no "Widgets"
  tab, the tray menu opens with a right-click, and the overlay sits behind
  normal windows). The Code of Conduct is now Contributor Covenant 2.1. The
  ESP32 README is in English. The product is called "Imolia Desktop Customizer"
  throughout. The contact address is info@imoliamedia.be.
- Widgets no longer rewrite their config file on every mouse movement while
  being dragged or resized: changes are bundled and written shortly after
  you stop (and always when the widget closes or the app quits).
- The application log now rotates (2 MB, 3 backups) instead of growing without
  limit - it had reached 93 MB.
- The Calculator, Pomodoro, Quick Notes and Google Calendar widgets now log
  under `DesktopCustomizer.<Name>`, so their messages end up in `app.log`; they
  also no longer call `logging.basicConfig`, which reconfigured logging for the
  whole program.
- The System Monitor settings window shows one update-interval field instead of
  two (the second one was ignored).
- All source files now start with the GPL license header.
- CI tests on Python 3.9 and 3.12 and shows which test failed.
- `setup.py` is up to date (version, Python versions) and its `desktop-customizer`
  command works from an editable install (`pip install -e .`).

### Fixed
- Opening *Widgets Beheren* no longer starts an endless refresh loop
  (`RecursionError`) that flooded the log.
- Clock widget: the color and font pickers now take effect, the text no longer
  overflows when you resize (also for italic), and the resize handle stays at
  the visible text.
- The settings of the Pomodoro and System Monitor widgets no longer crash on
  *Save*, and both now have a working color picker. The To-Do widget now keeps
  the colors you choose instead of always saving the default.
- The Google Calendar widget no longer freezes the desktop while it downloads
  your calendars (up to 10 seconds per calendar on a slow or missing
  connection, and again on every click on a date). It now downloads in the
  background and keeps showing the last loaded events if a refresh fails.
- The LLM Chat widget could not connect at all with the bundled `openai`
  0.27: it only supported the newer API. It now works with both, no longer
  freezes while waiting for an answer, and no longer lists retired
  non-chat models.
- The LLM Chat widget stored your OpenAI API key as plain text in its config
  file and wrote it to a debug log. The key is now stored encrypted with
  Windows DPAPI (an existing plain-text key is converted automatically) and
  is never logged.
- Gmail Inbox and LLM Chat both use Windows DPAPI; when both were active they
  overwrote each other's settings and encryption failed.
- The packaged program now contains the standard-library modules the Gmail
  Inbox widget needs (`imaplib`, `html.parser`, `winsound`); without them the
  widget failed to load.
- The package manager no longer needs `distutils`, which was removed in
  Python 3.12 (it only worked where `setuptools` happened to be installed).
- A stale `settings.json` with test data is no longer tracked in git, and the
  extension modules (`*.pyd`) of the bundled embedded Python are now tracked,
  so a fresh clone can build a complete app.

## [1.1.0] - 2026-09-06
### Added
- New ESP32 Web Dashboard widget: embeds the web interface of any device on
  your local network (an ESP32 project, a 3D printer's Mainsail/Fluidd page,
  etc.) directly on the desktop. Supports multiple systems via a dropdown,
  or copy the widget file under a different name to show several dashboards
  at once, each remembering its own configuration.
- Automated test suite (`tests/`) covering settings, the package manager,
  and widget auto-discovery.
- The real PyInstaller build recipe (`Imolia Desktop Customizer.spec`) is
  now version-controlled, so every build is reproducible.

### Fixed
- The app no longer crashes silently on startup - errors are logged and
  shown in a message box instead.
- A fresh installation no longer shows an empty overlay: bundled widgets
  are now automatically copied into the user's widgets folder.
- Widgets no longer try to reinstall their dependencies (and stall
  startup by several seconds) every time the app launches.
- Fixed a System Monitor crash caused by an outdated `psutil` pin
  incompatible with modern Python.
- The overlay is now properly click-through outside of widgets: it no
  longer intercepts clicks meant for the desktop or taskbar.
- The overlay now spans all connected monitors instead of only the one
  active at startup, so widgets can be placed on any screen.
- Fixed a black-screen/taskbar-disappearing issue caused by Windows'
  fullscreen-detection heuristics.
- `pip install -r requirements.txt` and CI no longer fail (a corrupted
  requirements file, and later a yanked `requests` version, both fixed).

## [1.0.0] - 2025-04-17
### Added
- New Google Calendar widget for displaying events from multiple Google Calendars
- Improved menu display for better user interaction

### Changed
- Enhanced overall user interface for a more modern look
- Updated widget management system for better performance
- Updated project license from MIT to GNU General Public License v3.0

### Removed
- Removed multi-language support to simplify the application
- Removed the option to start automatically with Windows due to system restrictions

### Fixed
- Various bug fixes and performance improvements

## 0.1.0 - 2024-09-26
### Added
- Initial release of the Desktop Customization Tool
- Basic structure for the application
- Transparent overlay functionality
- Clock widget
- System tray icon integration
- Basic settings and configuration options

[Unreleased]: https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/compare/Beta...v1.1.0
[1.0.0]: https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/releases/tag/Beta
