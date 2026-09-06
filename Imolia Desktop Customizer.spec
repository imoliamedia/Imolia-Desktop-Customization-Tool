# -*- mode: python ; coding: utf-8 -*-


# Belangrijk: 'widgets' stond hier eerder NIET in datas, waardoor de
# gebouwde executable geen enkele standaard-widget bevatte - een verse
# installatie kreeg zo altijd een volledig lege overlay. runtime_hooks
# stond ook leeg, waardoor runtime_hook.py nooit uitgevoerd werd.
# PyQt5.QtWebEngineWidgets (voor de ESP32 Web Dashboard widget) en openai
# (voor de LLM Chat widget) ontbraken in hiddenimports, waardoor die
# widgets bij elke start via de embedded Python probeerden te installeren
# in plaats van al gewoon aanwezig te zijn.
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources'), ('src', 'src'), ('widgets', 'widgets'), ('embedded_python', 'embedded_python')],
    hiddenimports=['PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWebEngineWidgets', 'psutil', 'json', 'importlib', 'icalendar', 'recurring_ical_events', 'requests', 'openai'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Imolia Desktop Customizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources\\icons\\tray_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Imolia Desktop Customizer',
)
