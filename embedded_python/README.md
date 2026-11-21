# embedded_python

A portable copy of Python for Windows (version **3.13.2**, the "embeddable package" from python.org) that is shipped with the program.

## What it is for

A build made with PyInstaller contains no pip. When a widget needs a package that is not in the build, the program uses **this** Python to run pip and install the package into `%APPDATA%\Imolia Desktop Customizer\packages` (see [ARCHITECTURE.md](../docs/ARCHITECTURE.md#dependencies-package_managerpy)). pip itself is set up on first use (`ensurepip`, or else `get-pip.py` is downloaded).

The folder is bundled into the build as plain files by the `datas` entry of `Imolia Desktop Customizer.spec`; PyInstaller does not process it. The program finds it at `embedded_python` next to the `.exe` or under `_internal`.

## Things to know

- **It is Python 3.13, but the program itself is built on Python 3.12.** Packages that have compiled parts (extension modules) and are installed with this Python cannot be imported by the 3.12 program. Pure-Python packages work. A widget that needs a compiled package must have that package bundled into the build instead (`hiddenimports` in the `.spec`).
- The extension modules (`*.pyd`) are part of the interpreter. They are tracked in git on purpose: the repository-wide `*.pyd` ignore rule has an exception for this folder. Without them `pip` cannot work (no `_ssl`, no `_ctypes`).
- `python313._pth` contains `import site`, which makes the interpreter look at `site-packages`; do not remove it.
- `LICENSE.txt` is the Python license. It must stay with the files.

## Updating it

1. Download the **Windows embeddable package (64-bit)** of the Python version you want from <https://www.python.org/downloads/windows/>. Using the same minor version as the build (currently 3.12) avoids the compiled-package problem described above.
2. Replace the files in this folder with its contents, keeping `get-pip.py`.
3. In the `python3XX._pth` file, make sure the line `import site` is not commented out.
4. Make sure the `*.pyd` files are added to git (`git status` shows them as new files).
5. Build the program and check that installing a widget dependency works, see [RELEASING.md](../docs/RELEASING.md).
