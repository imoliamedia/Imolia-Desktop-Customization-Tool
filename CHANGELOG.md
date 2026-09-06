# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [0.1.0] - 2024-09-26
### Added
- Initial release of the Desktop Customization Tool
- Basic structure for the application
- Transparent overlay functionality
- Clock widget
- System tray icon integration
- Basic settings and configuration options

[Unreleased]: https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/releases/tag/v0.1.0

