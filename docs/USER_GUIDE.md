# User Guide for Imolia Desktop Customizer

Imolia Desktop Customizer puts small, always-visible widgets (a clock, system graphs, your inbox, ...) on your Windows desktop.

> The program's interface is partly Dutch (for example **Opslaan** = Save, **Annuleren** = Cancel). Both names are given where it matters.

## Table of contents
1. [Requirements and installation](#1-requirements-and-installation)
2. [First use](#2-first-use)
3. [The tray icon](#3-the-tray-icon)
4. [The overlay](#4-the-overlay)
5. [The settings window](#5-the-settings-window)
6. [Managing widgets](#6-managing-widgets)
7. [Where your data is stored](#7-where-your-data-is-stored)
8. [Starting with Windows](#8-starting-with-windows)
9. [Updating](#9-updating)
10. [Privacy and security](#10-privacy-and-security)
11. [Frequently asked questions](#11-frequently-asked-questions)

Something not working? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## 1. Requirements and installation

- Windows (developed and tested on Windows 11; Windows 10 should work too).
- Running the downloaded program (`.exe`) needs nothing else. Running from source needs Python 3.9 or newer (the program is tested on 3.9 and 3.12).

**Option A - download a release:**

1. Go to the [Releases page](https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/releases) and download the `.zip` of the release you want. Compare its version with the [CHANGELOG](../CHANGELOG.md): newer features are only in releases made after them. If the newest release is older than what you need, use option B, or build the program yourself (see the [README](../README.md#building-the-windows-executable)).
2. Unzip it and keep all files together in one folder.
3. Run `Imolia Desktop Customizer.exe`.

**Option B - run from source:**

```
git clone https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool.git
cd Imolia-Desktop-Customization-Tool
pip install -r requirements.txt
python main.py
```

## 2. First use

1. Start the program. It runs in the background and shows an icon in the system tray (it may be hidden behind the `^` arrow next to the clock).
2. **Right-click** the icon and choose **Settings**.
3. Tick the widgets you want. A widget whose box is greyed out still needs its dependencies - click **Installeer** next to it (needs an internet connection the first time).
4. Click **Opslaan** (Save). The widgets appear on your desktop immediately; no restart is needed.

Every time the program starts, the widgets that come with it are copied into your widgets folder, `Documents\Imolia Desktop Customizer Widgets`, **if they are not there yet**. Existing files are never overwritten, so your own changes survive (see [Updating](#9-updating)).

## 3. The tray icon

| Action | What happens |
|---|---|
| **Left-click** | Shows or hides the overlay (all your widgets at once). |
| **Right-click** | Opens the menu: **Toggle Overlay**, **Settings**, **Exit**. |

To quit the program completely, use **Exit**. Closing windows or hiding the overlay does not stop it.

## 4. The overlay

The overlay is a transparent layer that covers your whole desktop; your widgets live on it.

- It spans **all connected monitors**, so you can drag a widget to any screen.
- It sits on the desktop, **behind your normal windows**. Widgets are drawn above the desktop (and above its icons, so an icon under a widget is hidden by it).
- Clicks outside the widgets go straight through to the desktop, the taskbar and your other programs.

## 5. The settings window

Open it with right-click on the tray icon, then **Settings**. It is a single window (there are no tabs):

- At the top: the program name and a link, **Download widgets van GitHub**, that opens the widgets folder of the project on GitHub.
- **Open Widgets Map** opens your widgets folder (`Documents\Imolia Desktop Customizer Widgets`) in Explorer.
- **Widgets Beheren** opens the widget manager: a list of all widgets with their dependency status, and an **Installeren** button to install the dependencies of the selected widget.
- **Vernieuwen** rescans the widgets folder (use it after you added or changed a widget file).
- The list shows one row per widget: a checkbox, its name, a status or an **Installeer** button when dependencies are missing, and a settings button (tooltip *Widget instellingen*).
- **Opslaan** applies your choices and closes the window; **Annuleren** closes it without changes.

## 6. Managing widgets

### Activating and deactivating

Tick or untick the checkbox and click **Opslaan**.

### Using widgets

- Drag a widget anywhere to move it.
- Drag the small grey square in its bottom-right corner to resize it. (The calculator also has a move handle in its bottom-left corner.)
- Positions and sizes are remembered. They are also kept on screen: a position saved on a larger or other monitor is pulled back into view at the next start.
- What each widget does is described in its own README, see the [list of bundled widgets](../widgets/README.md#bundled-widgets).

### Configuring a widget

1. Make sure the widget is ticked **and saved** (the settings button only works for active widgets).
2. Open **Settings** again and click the settings button on the widget's row.
3. Change what you want and use the dialog's own Save button.

### Adding your own widgets

1. Click **Open Widgets Map**.
2. Put the widget's single `.py` file **directly in that folder** (not in a subfolder - subfolders are not scanned).
3. Click **Vernieuwen**. The widget appears in the list.

A widget file is recognised by the line `Widget = <ClassName>`. To write one, see the [Widget Development Guide](WIDGET_DEVELOPMENT.md).

You can run the same widget several times by copying its file under another name; each copy gets its own configuration (the ESP32 widget README explains this).

### Removing a widget

Untick it and save, then delete its `.py` file from the widgets folder. Its settings are kept in `<filename>_config.json` next to it; delete that file too if you want to start fresh.

## 7. Where your data is stored

| What | Where |
|---|---|
| Which widgets are active | `%APPDATA%\Imolia Desktop Customizer\settings.json` |
| Log file | `%APPDATA%\Imolia Desktop Customizer\logs\app.log` (the log rotates: `app.log` plus up to three older files of 2 MB each) |
| Installed widget dependencies | `%APPDATA%\Imolia Desktop Customizer\packages` (plus `pip_cache` and `packages_status.json` next to it) |
| The widgets themselves | `Documents\Imolia Desktop Customizer Widgets` |
| Each widget's settings | In the same folder, next to the widget: `<widget filename>_config.json` (some widgets keep extra data, such as the To-Do list in `modern_todo_widget_tasks.json`) |

The program does not store anything in the folder it is installed in. Paste `%APPDATA%\Imolia Desktop Customizer` into the Explorer address bar to open the first folder.

## 8. Starting with Windows

Starting automatically with Windows is not built in (it was removed in version 1.0.0). To do it yourself: press `Win + R`, type `shell:startup`, press Enter, and put a shortcut to `Imolia Desktop Customizer.exe` in the folder that opens.

## 9. Updating

1. Close the program with **Exit** in the tray menu.
2. Replace the program folder with the new one (your widgets, settings and logs are stored elsewhere and are kept).
3. **Widgets are not updated automatically.** Because the program never overwrites files in your widgets folder, a new version's improved widgets only appear if you copy them over yours: take the `.py` files from the new download (they are in the folder `_internal\widgets\<widget name>\`; in the GitHub repository they are in `widgets\<widget name>\`) and replace the ones in `Documents\Imolia Desktop Customizer Widgets`. Your widget settings are kept, because they are stored in separate `_config.json` files. A widget file you delete is copied back from the new version at the next start.

## 10. Privacy and security

The program itself does not collect or send any data. Its only internet use is installing widget dependencies from PyPI and opening links you click.

**Widgets can use the internet, because that is their job** - only enable what you need:

| Widget | Contacts |
|---|---|
| Gmail Inbox | `imap.gmail.com` (your mail, read directly; nothing goes anywhere else) |
| Google Calendar | the iCal URLs you enter |
| LLM Chat | OpenAI: every message you type is sent to OpenAI |
| ESP32 Web Dashboard | the devices on your own network that you add |
| System Overview | nothing (it only reads your own PC, using `nvidia-smi` for the GPU) |

**Secrets:** the Gmail app passwords and the OpenAI key are stored **encrypted with Windows DPAPI**, which ties them to your Windows user on this PC (a copied config file does not work elsewhere). Other settings, **including the secret iCal addresses of your calendars**, are stored as plain text in the `_config.json` files. Treat those addresses like passwords and do not share your widgets folder.

## 11. Frequently asked questions

**How do I exit completely?** Right-click the tray icon, then **Exit**.

**Can I use several monitors?** Yes, the overlay covers all of them.

**A widget disappeared / is off-screen.** Positions are pulled back into view at start. If it still does not show, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**How do I reset a widget?** Close the program, delete that widget's `<filename>_config.json` in the widgets folder, and start again.

**How do I make my own widget?** See the [Widget Development Guide](WIDGET_DEVELOPMENT.md).

For further help, open an issue on [GitHub](https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/issues) and attach the end of `app.log`.
