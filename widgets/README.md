# Imolia Desktop Customizer Widgets

This directory contains the widgets that come with the Imolia Desktop Customizer. As an open-source project, we welcome contributions from the community in the form of new widgets or improvements to existing ones.

## Bundled widgets

| Widget | File | Extra requirements |
|---|---|---|
| [Clock](clock_widget/README.md) | `clock_widget.py` | - |
| [Calculator](calculator/README.md) | `calculator.py` | - |
| [Modern To-Do](modern_todo_widget/README.md) | `modern_todo_widget.py` | - |
| [Pomodoro Timer](Pomodoro%20Productivity%20Timer%20Widget/README.md) | `Pomodoro Productivity Timer.py` | - |
| [Quick Notes](Quick%20Notes%20Widget/README.md) | `Quick Notes.py` | - |
| [System Monitor](system_monitor_widget/README.md) | `system_monitor_widget.py` | `psutil` |
| [System Overview](system_overview_widget/README.md) | `system_overview_widget.py` | `psutil`; an NVIDIA GPU for the GPU panels |
| [Google Calendar](google_calendar_widget/README.md) | `google_calendar_widget.py` | `icalendar`, `recurring_ical_events`, `requests`; the iCal URL of your calendar |
| [Gmail Inbox](gmail_inbox_widget/README.md) | `gmail_inbox_widget.py` | A Google *app password* per Gmail account |
| [LLM Chat](LLM%20Chat/README.md) | `LLMChat.py` | `openai`; your own OpenAI API key |
| [ESP32 Web Dashboard](ESP32%20Web%20Dashboard%20Widget/README.md) | `esp32_web_dashboard.py` | `PyQtWebEngine` |

Dependencies are installed from the Settings window (**Installeer**) the first time you need them; the packaged program already contains the common ones.

## Two places, two layouts

**In this repository** every widget has its own folder:

```
widgets\
└── widget_name\
    ├── widget_name.py
    ├── README.md
    └── screenshots\
        └── widget_screenshot.png
```

**On your PC** the program reads widgets from one flat folder:

```
C:\Users\[YourUsername]\Documents\Imolia Desktop Customizer Widgets\
├── clock_widget.py
├── calculator.py
├── clock_widget_config.json      <- created by the widget: its settings
└── ...
```

Only the `.py` file of each widget is copied there (at program start, and only if it is not there yet). READMEs and screenshots stay in the repository. **Subfolders of the widgets folder are not scanned**, so put a widget's `.py` file directly in the folder.

## How to use widgets

1. Right-click the tray icon and choose **Settings**.
2. Tick the widgets you want to activate in the list.
3. Click **Opslaan** (Save). The widgets appear on your desktop.

See the [User Guide](../docs/USER_GUIDE.md) for the whole settings window.

## Adding custom widgets

To add a widget for personal use:

1. In the Settings window, click **Open Widgets Map**. This opens the widgets folder.
2. Copy the widget's `.py` file into that folder - directly, not in a subfolder.
3. Click **Vernieuwen**. The widget appears in the list; tick it and save.

A file is recognised as a widget when it contains the line `Widget = <ClassName>`. Its dependencies are read from the `Dependencies:` block in the file's docstring, see the [Widget Development Guide](../docs/WIDGET_DEVELOPMENT.md).

A widget's own settings are saved next to it as `<filename>_config.json`, so a copy of a widget under another name has its own settings.

## Creating your own widget

See the [Widget Development Guide](../docs/WIDGET_DEVELOPMENT.md).

## Contributing widgets to the project

1. Develop your widget following the [Widget Development Guide](../docs/WIDGET_DEVELOPMENT.md).
2. Fork the repository on GitHub.
3. Add a folder for your widget to the `widgets` directory, with the layout above. A widget needs:
   - the widget file, named after its folder, with `Widget = <ClassName>` and a `Dependencies:` block in its docstring;
   - a `README.md` that describes what it does, how to configure it, what data it uses or sends where, and troubleshooting tips;
   - at least one screenshot in `screenshots\`, referenced from the README;
   - the GPL license header used by the other files;
   - a logger named `DesktopCustomizer.<WidgetName>` (see the guide), and tests for any logic that can be tested;
   - an entry in the [CHANGELOG](../CHANGELOG.md) and in the widget tables of this file and of the main README.
4. Create a pull request.
5. Our team will review your submission. If approved, your widget will be added to the main repository and will be available to all users in future releases.

Please note that while anyone can create and use custom widgets locally, only reviewed and approved widgets will be added to the official GitHub repository. This ensures the quality and security of the widgets available to all users.

For more details, see the [Contribution Guidelines](../CONTRIBUTING.md).

## Widget marketplace

Currently, there is no official widget marketplace. All approved widgets are included in the main repository. We may consider a marketplace in the future to make it easier to discover and install community-created widgets. If you have ideas for improving widget distribution and discovery, please open an issue on our GitHub repository to start a discussion.
