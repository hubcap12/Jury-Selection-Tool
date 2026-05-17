# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the webview-based UI.
# Run from the repo root with:  pyinstaller JuryTool_v2.spec
#
# Uses pywebview's Qt (PySide6) backend — no .NET dependency.

from PyInstaller.utils.hooks import collect_all

pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all('PySide6')

a = Analysis(
    ['jury_v2.py'],
    pathex=[],
    binaries=pyside6_binaries,
    datas=[
        ('icon.ico', '.'),
        ('jury_ui/static', 'jury_ui/static'),
        *pyside6_datas,
    ],
    hiddenimports=[
        *pyside6_hiddenimports,
        'qtpy',
        'webview.platforms.qt',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_pythonnet.py'],
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
    name='JuryTool_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JuryTool_v2',
)
