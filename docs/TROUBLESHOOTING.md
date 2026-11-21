# Troubleshooting

Start here when something does not work. For how the program is meant to work, see the [User Guide](USER_GUIDE.md).

## The log file

Almost everything is explained in the log:

```
%APPDATA%\Imolia Desktop Customizer\logs\app.log
```

(Paste that path into the Explorer address bar.) The log rotates: when `app.log` reaches 2 MB it becomes `app.log.1`, and so on up to `app.log.3`. Open `app.log` and look for lines containing `ERROR` or `CRITICAL` - the lines before them usually say what happened. Messages from widgets appear in the same file, prefixed with `DesktopCustomizer.<WidgetName>`.

## Nothing appears on my desktop

1. Is the program running? Look for its icon in the system tray (it may be behind the `^` arrow next to the clock).
2. **Left-click** the icon: this shows or hides the whole overlay. You may have hidden it.
3. Right-click the icon, choose **Settings**, make sure your widgets are ticked and click **Opslaan**.
4. A widget may be off-screen (for example after you disconnected a monitor). Positions are pulled back into view when the program starts, so restart it with **Exit** and start again.
5. Still nothing: check `app.log`.

## "De widget '...' kon niet worden geladen"

This message means a widget file failed to load. The log shows why:

- `ModuleNotFoundError: No module named '...'` for a widget that comes with the program: the **program build is older than the widget file**. A packaged build only contains the Python modules that were included when it was made (for example the Gmail Inbox widget needs `imaplib`, and uses `html.parser` for formatted mails). Update the program to a newer build, or run from source. See also [Widget Development Guide](WIDGET_DEVELOPMENT.md#handling-dependencies).
- A `SyntaxError` or another error in a widget you wrote or edited: fix the file, or remove it from the widgets folder.

## A widget is not in the list

- The file must be **directly** in `Documents\Imolia Desktop Customizer Widgets` - subfolders are not scanned.
- It must contain the line `Widget = <ClassName>`.
- Click **Vernieuwen** in the Settings window.

## The checkbox of a widget is greyed out

The widget needs packages that are not installed yet. Click **Installeer** next to it (or use **Widgets Beheren**). This needs an internet connection. If installing fails, `app.log` shows the pip error.

In the packaged program only packages without compiled parts can be installed this way; a widget that needs a compiled package must be bundled when the program is built (see the [Widget Development Guide](WIDGET_DEVELOPMENT.md#handling-dependencies)).

## The settings button of a widget does nothing

It only works for widgets that are active. Tick the widget, click **Opslaan**, open **Settings** again and click the button.

## Reset a widget or everything

- **One widget:** close the program (**Exit**), delete that widget's `<filename>_config.json` in the widgets folder, start again.
- **Which widgets are active:** delete `%APPDATA%\Imolia Desktop Customizer\settings.json`.

## The screen turns black or the taskbar disappears

This is a rare Windows desktop-composition problem. It was fixed in version 1.1.0 (the overlay is made 1 pixel smaller than the screen, and the web view of the ESP32 widget uses software rendering). If it still happens, end the program from Task Manager and [report it](https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/issues) with the end of `app.log`.

## The program uses a lot of CPU or memory

Increase the refresh interval in the settings of the widgets that update often (System Monitor, System Overview, Gmail Inbox, Google Calendar), or deactivate widgets you do not need.

## Widget-specific problems

**Gmail Inbox**
- A red **!** next to an account: hover it for the reason.
- *Inloggen mislukt* - the app password is wrong or was revoked. Create a new one at <https://myaccount.google.com/apppasswords> (2-Step Verification must be on; accounts with Advanced Protection cannot create one) and use **Bewerken…** in the widget settings.
- *Geen verbinding met Gmail* / *time-out* - no internet, or a firewall blocks `imap.gmail.com` on port 993.
- *Wachtwoord kan niet worden gelezen - voer het opnieuw in* - passwords are encrypted for one Windows user on one PC; if you copied the widget's `_config.json` from elsewhere, enter the app password again.
- *Deze versie van de app bevat de module imaplib niet* - the program build is too old for this widget, see above.

**Google Calendar**
- *Fout bij laden van agenda*: check the iCal URL (copy it again from Google Calendar; if you reset the "secret address" in Google the old URL stops working) and your internet connection. After a failed refresh the widget keeps showing the events it already had.

**System Overview**
- GPU panels show *n.v.t.*: they need an NVIDIA card; check that running `nvidia-smi` in a terminal works.
- No CPU temperature: Windows does not provide it to normal programs. Run LibreHardwareMonitor to get it.

**LLM Chat**
- Errors from OpenAI appear in the chat window as `Error: ...` (wrong key, no access to the chosen model, no credit). Every question is sent on its own; the AI does not remember earlier messages.

**ESP32 Web Dashboard**
- *QtWebEngine is niet geïnstalleerd*: install `PyQtWebEngine==5.15.6`; the packaged program already contains it.
- A blank page: open the same address in a normal browser to check that the device answers.

## Reporting a bug

Open an [issue](https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/issues/new/choose) and include: your Windows version, whether you run the `.exe` or the source (and the Python version), the name of the widget, what you did, and the last 50 lines of `app.log`. **Remove passwords, API keys and secret calendar addresses** from anything you paste.
