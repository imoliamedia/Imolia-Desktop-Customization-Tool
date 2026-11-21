# ESP32 Web Dashboard Widget

Shows the web interface of a device on your local network - for example an ESP32 project with a built-in web server such as a climate cabinet or a hydroponics system, a 3D printer's Mainsail/Fluidd page, or any other homemade dashboard - directly as a widget on your desktop. Always visible, without opening a browser window.

This widget has no screenshot on purpose: it shows **whatever web page you point it at** - a Mainsail or Fluidd page of your 3D printer, a climate cabinet's own dashboard, ... - so what you see is the page of your device, in a frameless window on your desktop.

## Features

- Add one or more *systems*, each with a name and an IP address (or a full URL).
- Switch between systems with the drop-down at the top of the widget.
- Click **Herlaad** (Reload) to refresh the current page.
- The widget remembers which system you looked at last, and the size and position of its window.

## Requirements

This widget uses `QWebEngineView` to display web pages, so besides `PyQt5` it needs `PyQtWebEngine`:

```
PyQt5==5.15.6
PyQtWebEngine==5.15.6
```

The packaged program already contains it. If `PyQtWebEngine` is not available, the widget shows a clear message (*QtWebEngine is niet geïnstalleerd*) instead of crashing.

## Adding a system

1. Right-click the tray icon, choose **Settings**, tick **Esp32 Web Dashboard** and click **Opslaan**.
2. Open **Settings** again and click the settings button on the widget's row.
3. Click **Nieuw systeem** (New system).
4. Enter a recognizable name (for example "Climate cabinet") and the local IP address of the device (for example `192.168.1.50`, with or without a port such as `192.168.1.50:80`).
5. Click **Bijwerken** (Update) to confirm the name and address, and close the dialog with **Save** to keep them. To remove a system, select it and click **Verwijderen** (Delete).

## Several dashboards visible at the same time

The drop-down lets you switch between systems, but shows only one at a time. Want your climate cabinet and two 3D printers **all at once**, in separate windows?

1. Copy `esp32_web_dashboard.py` in your widgets folder (`Documents\Imolia Desktop Customizer Widgets`) and give the copy another file name (for example `printer_ad5x.py`).
2. Restart the program (or click **Vernieuwen** in the widget list). The copy appears as a separate widget, named after its file.
3. Activate it in Settings and give it its own system (name + IP address).

Every copy automatically gets its **own, independent** configuration file (see below), so copies do not affect each other.

## Configuration file

The settings are saved next to the widget file in a file named `<file name without .py>_config.json`. For `esp32_web_dashboard.py` that is `esp32_web_dashboard_config.json`; for a copy `printer_ad5x.py` it is `printer_ad5x_config.json`. This is how every copy has its own settings even though they all live in the same folder.

## Troubleshooting

- A blank page: open the same address in a normal browser to check that the device answers.
- The widget loads web pages with software rendering. This avoids a Windows desktop problem (black screen, vanishing taskbar) that the hardware-accelerated web view could cause on the transparent overlay.
- See also the [Troubleshooting guide](../../docs/TROUBLESHOOTING.md) and `%APPDATA%\Imolia Desktop Customizer\logs\app.log`.
