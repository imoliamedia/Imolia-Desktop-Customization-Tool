# Releasing

How to build, check and publish a version of Imolia Desktop Customizer. Read [ARCHITECTURE.md](ARCHITECTURE.md#packaging-imolia-desktop-customizerspec) first if you are new to the build.

## 1. Before you build

- Everything you want in the release is on `main`, and the [CI](../.github/workflows/ci.yml) is green on Python 3.9 and 3.12.
- Update the [CHANGELOG](../CHANGELOG.md): rename `## [Unreleased]` to the new version with today's date, and start a new empty `## [Unreleased]` above it. Update the compare links at the bottom of the file.
- Set the same version in `setup.py`, and in the heading of `release/README.md`.
- Write the release notes in `docs/releases/v<version>.md` (copy the previous one as a starting point): they become the description of the GitHub release.
- Does a widget need a module that PyInstaller cannot see (a standard-library module only the widget imports, or a package that has compiled parts)? It must be in `hiddenimports` in `Imolia Desktop Customizer.spec`, otherwise it is missing in the `.exe`.

## 2. Build

```
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm "Imolia Desktop Customizer.spec"
```

The result is `dist\Imolia Desktop Customizer\`. The `embedded_python` folder must be in the project root (see [its README](../embedded_python/README.md)). A good habit is to build into a separate folder first, so a build you have not checked yet does not replace the one you use:

```
pyinstaller --noconfirm "Imolia Desktop Customizer.spec" --distpath C:\temp\build\dist --workpath C:\temp\build\work
```

## 3. Check the build

1. **Is every module there?** Make sure the modules your widgets need are in the build. One way is to list the modules inside the program's archive:

   ```python
   from PyInstaller.archive.readers import CArchiveReader, ZlibArchiveReader
   exe = r"dist\Imolia Desktop Customizer\Imolia Desktop Customizer.exe"
   ca = CArchiveReader(exe)
   for name in ca.toc:
       if name.endswith(".pyz"):
           modules = set(ZlibArchiveReader(exe, ca._start_offset + ca.toc[name][0]).toc.keys())
   print("imaplib" in modules, "html.parser" in modules)
   ```

   (`_start_offset` is an internal attribute of PyInstaller's reader and can change between versions.)
2. **Does it start and load every widget?** Close any running copy of the program (a running `.exe` cannot be replaced), start the new build, wait about 15 seconds, then read `%APPDATA%\Imolia Desktop Customizer\logs\app.log` from the start of your test: there should be no `ERROR` or `CRITICAL` lines, and a *successfully activated* line for each active widget.
3. Try the widgets you changed with real data (a mail account, a calendar, ...). Tests use made-up data.

## 4. Publish

1. Copy `release/README.md` and `LICENSE` into the folder `dist\Imolia Desktop Customizer\` (as `README.md` and `LICENSE`), then put the **entire folder** - not only the `.exe` - into a `.zip`, for example `Imolia Desktop Customizer 1.2.0.zip`. Optionally note the checksum with `Get-FileHash "Imolia Desktop Customizer 1.2.0.zip"` in the release description.
2. Tag the commit and push the tag - the changelog's compare links need the tags to exist on GitHub:

   ```
   git tag v1.2.0
   git push origin v1.2.0
   ```

3. On GitHub, create a release from that tag, attach the `.zip`, and paste `docs/releases/v<version>.md` as the description.

## 5. After the release

- Users who run the `.exe` keep their widgets and settings; see [Updating](USER_GUIDE.md#9-updating) for how they get improved widgets (the program never overwrites a widget file that already exists in the user's widgets folder).
- Keep the previous build folder around until you have seen the new one work.
