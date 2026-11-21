## What does this change, and why?

<!-- A short description. Link the issue if there is one: Fixes #123 -->

## Checklist

- [ ] `python -m unittest discover tests` passes (CI runs it on Python 3.9 and 3.12)
- [ ] I added or updated tests for what I changed (and they never use the real network or real accounts)
- [ ] The code runs on Python 3.9 (no `match` statements or `X | Y` type unions)
- [ ] I updated the documentation (README, `docs/`, the widget's README and screenshot) where behavior changed
- [ ] I added a line under `[Unreleased]` in the CHANGELOG
- [ ] New source files start with the GPL license header
- [ ] Nothing here writes secrets or user content to the log, and slow work does not run on the UI thread

### For a new or changed widget

- [ ] It follows [widgets/README.md](https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool/blob/main/widgets/README.md#contributing-widgets-to-the-project) (README with screenshot, `Widget = ...`, `Dependencies:` block, `DesktopCustomizer.<Name>` logger)
- [ ] If it needs a module that only widgets use, I added it to `hiddenimports` in `Imolia Desktop Customizer.spec`

## How did you test it?

<!-- What you ran or clicked, on which Windows version -->
