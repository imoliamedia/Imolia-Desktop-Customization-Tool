# Contributing to Imolia Desktop Customizer

We welcome contributions to the Imolia Desktop Customizer! Here are some guidelines to help you get started. By taking part you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing to this project, you agree that your contributions will be licensed under the GNU General Public License v3.0. Make sure you have read and understood the [LICENSE](LICENSE) file. New source files start with the same GPL header as the existing ones.

## Getting started

1. Install Python 3.9 or newer (the program runs on 3.12, CI tests 3.9 and 3.12). The program is for Windows.
2. Fork and clone the repository, then:
   ```
   pip install -r requirements.txt
   python main.py
   ```
   Optionally `pip install -e .` adds a `desktop-customizer` command; it only works as an editable install from a clone, because the widgets and resources live outside the `src` package.
3. Run the tests: `python -m unittest discover tests` (see [tests/README.md](tests/README.md)).
4. Read how it fits together: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Submitting changes

1. Create a new branch from `main` for your feature or bug fix, with a descriptive name.
2. Make your changes in the new branch. Keep a pull request focused on one thing.
3. Run the tests; add tests for what you changed (see below).
4. Update the documentation and the [CHANGELOG](CHANGELOG.md) (see below).
5. Submit a pull request with a clear description of what changed and why. The pull request template has a checklist.

Write commit messages with a short summary line in the imperative ("Fix ...", "Add ...") and, if it helps, a few lines on *why* the change was needed.

## Code style

- Follow the [PEP 8](https://peps.python.org/pep-0008/) style guide for Python code.
- Use meaningful variable and function names.
- Comment where it helps, especially to explain *why* something is done. Comments may be in English or Dutch (the existing code has both); new documentation is in English.
- Write code that runs on **Python 3.9** (no `match` statements, no `X | Y` type unions): CI runs it there.
- The program's interface is partly Dutch. Keep the language consistent within a window or dialog.
- Do not block the UI thread with slow work, and never write secrets or user content to the log (see the [Widget Development Guide](docs/WIDGET_DEVELOPMENT.md)).

## Tests

- If you add or change behavior, add or update tests. The rules for writing tests that behave well in CI (especially for Qt widgets) are in [tests/README.md](tests/README.md).
- Tests must never use the real network or real accounts.
- CI runs `python -m unittest discover tests` on Python 3.9 and 3.12 for every push and pull request; both must pass.

## Documentation and the changelog

- Update the `README.md` and the files in `docs/` when your change affects what users or developers see or do. If you add or change a widget, update its own README (and its screenshot).
- Add a line under `## [Unreleased]` in the [CHANGELOG](CHANGELOG.md) for every user-visible change (Added, Changed, Fixed, Removed).

## Contributing widgets

We encourage the community to contribute new widgets. To contribute a widget:

1. Develop your widget following the [Widget Development Guide](docs/WIDGET_DEVELOPMENT.md).
2. Make sure it follows the directory structure and the checklist in [widgets/README.md](widgets/README.md#contributing-widgets-to-the-project): a README and at least one screenshot, the license header, the `DesktopCustomizer.<WidgetName>` logger, and tests where there is logic to test.
3. Add your widget to the `widgets` directory in your fork.
4. Submit a pull request.
5. Our team will review your submission. If approved, your widget will be added to the main repository.

## Reporting bugs

- Use the [issue tracker](https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/issues/new/choose) and pick the bug report template.
- Describe the bug in detail, including steps to reproduce it.
- Include your Windows version, whether you run the `.exe` or the source (and the Python version), the widget involved, and the end of the log file `%APPDATA%\Imolia Desktop Customizer\logs\app.log`.
- Remove passwords, API keys and secret calendar addresses from anything you post.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) may already solve it.

## Reporting a security problem

Please do not open a public issue. See [SECURITY.md](SECURITY.md).

Thank you for contributing to the Imolia Desktop Customizer!
