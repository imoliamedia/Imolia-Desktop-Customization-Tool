# Imolia Desktop Customizer 1.2.0

Small, always-visible widgets on your Windows desktop: a clock, system graphs, your inbox, a to-do list, and more. You can also write your own. Open source (GPL v3) by Imolia Media.

## Start

1. Keep **all files and folders** of this download together, in one folder anywhere you like (for example `C:\Imolia Desktop Customizer`). Do not move only the `.exe`.
2. Double-click **Imolia Desktop Customizer.exe**. Nothing else needs to be installed; no window opens, the program lives in the system tray (the icon may be hidden behind the `^` arrow next to the clock).
3. **Right-click** the tray icon, choose **Settings**, tick the widgets you want and click **Opslaan** (Save). They appear on your desktop right away.

**Left-click** the tray icon to show or hide all widgets; **Exit** in its right-click menu quits the program.

## Good to know

- **Eleven widgets are included:** Clock, Calculator, Modern To-Do, Pomodoro Timer, Quick Notes, System Monitor, System Overview, Google Calendar, Gmail Inbox, LLM Chat and ESP32 Web Dashboard.
- **Your data stays on your PC**, outside this folder: widgets and their settings in `Documents\Imolia Desktop Customizer Widgets`, the log and installed packages in `%APPDATA%\Imolia Desktop Customizer`. The program itself sends nothing anywhere; widgets only contact the services you set up (Gmail, your calendar, OpenAI, devices on your network).
- **Updating from an older version:** replace this folder with the new one. Your widgets and settings are kept, but **existing widget files are never overwritten**. To get the improved widgets, copy the `.py` files from the `_internal\widgets` folder of this download over the ones in `Documents\Imolia Desktop Customizer Widgets` (new widgets are copied automatically). Details: the User Guide, section "Updating".
- **Uninstalling:** quit the program and delete this folder. To remove your data as well, delete `Documents\Imolia Desktop Customizer Widgets` and `%APPDATA%\Imolia Desktop Customizer`.
- **Starting with Windows:** press `Win + R`, type `shell:startup`, and put a shortcut to the `.exe` in the folder that opens.

## Help

- User Guide: <https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/blob/main/docs/USER_GUIDE.md>
- Something not working? <https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/blob/main/docs/TROUBLESHOOTING.md> (the log file is `%APPDATA%\Imolia Desktop Customizer\logs\app.log`)
- Questions and bug reports: <https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/issues> - or info@imoliamedia.be
- Source code, changelog and widget development guide: <https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool>

## License

GNU General Public License v3.0, see the `LICENSE` file. Python and the libraries inside this download are covered by their own licenses.
