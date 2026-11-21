# Tests

The tests use Python's built-in `unittest`. Run them from the project root:

```
python -m unittest discover tests
```

Run one file or one test:

```
python -m unittest tests.test_logger
python -m unittest tests.test_gmail_inbox_widget.TestFetchMessage.test_returns_the_parsed_mail
```

The GitHub CI (`.github/workflows/ci.yml`) runs the same command on **Python 3.9 and 3.12** on Windows. If it fails, the failing test is printed at the end of the job log. If Qt itself crashes, the log shows `Windows fatal exception: access violation` and the test that was running.

## What is tested

| File | Covers |
|---|---|
| `test_config.py` | The application name and the name of the widgets folder |
| `test_package_manager.py` | Parsing of package specs and the `LooseVersion` replacement (including loading without `distutils`) |
| `test_widget_seeder.py` | Copying the bundled widgets to the user's folder without overwriting |
| `test_logger.py` | The rotating log |
| `test_draggable_widget.py` | The bundling of `save_config()` calls |
| `test_google_calendar_widget.py` | Downloading in a background thread, the cache, failure behavior |
| `test_llm_chat_widget.py` | Encrypting the key, both `openai` versions, the request in a background thread |
| `test_gmail_inbox_widget.py` | Parsing and reading mail, the sanitizer, IMAP calls with a fake server, the reader in the widget |
| `test_system_overview_widget.py` | Parsing of GPU output, CPU temperature selection, formatting |

The settings file (`settings.py`), the overlay, the settings windows and the widget loader are not covered by automated tests yet.

## Writing tests for Qt widgets

These rules come from real failures (a crash only seen on Python 3.9 in CI, and a test that tried to log in to Gmail):

- Set `os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')` before creating a `QApplication`, and create it once per module with `QApplication.instance() or QApplication([])`.
- Create as few widgets as possible: one per test class, in `setUpClass`, and reset their state in `setUp`. Creating and discarding many widgets next to running threads has crashed Qt.
- **Never touch the real network or accounts.** Patch whatever connects (for example `imaplib.IMAP4_SSL`, `requests.get`, `ask_openai`) - for the whole test class, not only inside a test - and use fake data such as `test.persoon@example.com`.
- A `QTimer.singleShot(...)` started in a widget's `__init__` (the Gmail widget plans a check after 1.5 s) fires later, during another test module. Patch `singleShot` while creating the widget and stop the widget's timers in a class cleanup.
- Wait with a helper that checks the condition first and only then processes events (`_wait_until` in the test files). Do not process Qt events when there is nothing to wait for.
- Widgets save their config next to their own `.py` file. Copy the file to a temporary folder before loading it (see `test_llm_chat_widget.py`) or patch `load_config`/`save_config`, so the repository stays clean.
- Test pure logic (parsing, sanitizing, encryption) without Qt where you can; it is faster and stable.
- Write for Python 3.9: no `match` statements and no `X | Y` type unions.
