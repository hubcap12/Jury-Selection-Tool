# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the webview-based UI (Stage 1+).
# Run from the repo root with:  pyinstaller JuryTool_v2.spec
#
# Differences vs. JuryTool.spec:
#   • Entry point is jury_v2.py instead of jury.py
#   • The static folder (webview/static) is bundled as data so pywebview
#     can find index.html / css / js / vendor at runtime.
#   • Output exe is renamed JuryTool_v2 so both can ship side-by-side.


a = Analysis(
    ['jury_v2.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
        ('webview/static', 'webview/static'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
