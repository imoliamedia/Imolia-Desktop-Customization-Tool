# Imolia Desktop Customization Tool

![Imolia Media Logo](https://www.imoliamedia.be/assets/img/favicon/android-chrome-192x192.png)

A powerful, open-source desktop customization tool developed by Imolia Media.

## Features

- Customizable overlay for your desktop
- Widget system for easy extensibility
- System tray integration
- User-friendly settings interface

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool.git
   ```

2. Navigate to the project directory:
   ```
   cd Imolia-Desktop-Customization-Tool
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application by executing:

```
python main.py
```

For detailed usage instructions, please refer to our [User Guide](docs/USER_GUIDE.md). See [widgets/README.md](widgets/README.md) for the list of bundled widgets (clock, calculator, system monitor, Google Calendar, LLM chat, and an [ESP32 Web Dashboard](widgets/ESP32%20Web%20Dashboard%20Widget/README.md) that embeds any local device's own web interface — an ESP32 project, a 3D printer's Mainsail/Fluidd page, etc. — directly on the desktop).

## Building the Windows executable

The distributable build is produced from `Imolia Desktop Customizer.spec`, the authoritative, version-controlled build recipe (previous builds were made with ad-hoc, undocumented PyInstaller flags, which is why the resulting `.exe` used to behave inconsistently across machines).

```
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm "Imolia Desktop Customizer.spec"
```

This requires an `embedded_python` folder (a portable Python build) in the project root — it's bundled as-is via the spec's `datas`, not processed by PyInstaller.

The result is `dist/Imolia Desktop Customizer/`. **Distribute the entire folder**, not just the `.exe` file inside it.

## Running the tests

```
python -m unittest discover tests
```

## Contributing

We welcome contributions! Please see our [Contribution Guidelines](CONTRIBUTING.md) for more details.

## Widget Development

Interested in creating your own widgets? Check out our [Widget Development Guide](https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/blob/main/docs/WIDGET_DEVELOPMENT.md).

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## About Imolia Media

Imolia Media is committed to creating innovative, user-friendly software solutions. Learn more about us at [www.imoliamedia.be](https://www.imoliamedia.be).
