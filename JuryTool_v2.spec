# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the webview-based UI.
# Run from the repo root with:  pyinstaller JuryTool_v2.spec
#
# Uses pywebview's Qt (PySide6/QtWebEngine) backend — no .NET dependency.
#
# Bundle-size strategy: let collect_all() + PyInstaller hooks do their full
# analysis, then post-filter a.binaries / a.datas to strip everything that
# pywebview's Qt/WebEngine path never loads at runtime.

import os
from PyInstaller.utils.hooks import collect_all

pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all('PySide6')

# ── Modules we are NOT bundling — pass to Analysis.excludes ───────────────────
_PYTHON_EXCLUDES = [
    # tkinter (not used with Qt backend)
    'tkinter', '_tkinter', 'turtle', 'turtledemo',
    # Pillow (not used by jury tool)
    'PIL',
    # pythonnet / clr_loader (replaced by Qt backend)
    'pythonnet', 'clr', 'clr_loader',
    # Unused PySide6 modules
    'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore', 'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender',
    'PySide6.QtAsyncio', 'PySide6.QtBluetooth', 'PySide6.QtCharts',
    'PySide6.QtDataVisualization', 'PySide6.QtDesigner',
    'PySide6.QtGraphs', 'PySide6.QtHelp', 'PySide6.QtHttpServer',
    'PySide6.QtLocation', 'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'PySide6.QtNfc', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    # PySide6.QtQml, QtQuick, QtPositioning, QtQuickWidgets are intentionally
    # NOT excluded — their C++ DLLs are required by Qt6WebEngineCore/Widgets.
    'PySide6.QtQuick3D', 'PySide6.QtQuickControls2',
    'PySide6.QtRemoteObjects',
    'PySide6.QtScxml', 'PySide6.QtSensors',
    'PySide6.QtSerialBus', 'PySide6.QtSerialPort',
    'PySide6.QtSpatialAudio', 'PySide6.QtStateMachine',
    'PySide6.QtTextToSpeech', 'PySide6.QtUiTools',
    'PySide6.QtWebEngineQuick', 'PySide6.QtWebView',
]

# ── Post-analysis TOC filters ──────────────────────────────────────────────────
# These patterns match the DESTINATION name inside the bundle (forward-slash
# normalised, lower-cased).  PyInstaller's hooks re-add files even if we
# filtered them out of the collect_all() lists, so we must strip them here.

# Qt6 DLL name prefixes to drop (lower-case, without .dll).
# Prefix matching catches all variants: Qt6Quick.dll, Qt6Quick3D.dll,
# Qt6QuickEffects.dll, Qt6ChartsQml.dll, Qt63DQuickRender.dll, etc.
_DROP_QT6_PREFIXES = (
    'qt63d',                   # all Qt3D modules + QML variants
    'qt6bluetooth',
    'qt6canvaspainter',
    'qt6charts',               # Qt6Charts.dll, Qt6ChartsQml.dll
    'qt6datavisualization',    # Qt6DataVisualization.dll, Qt6DataVisualizationQml.dll
    'qt6designer',
    'qt6graphs',
    'qt6help',
    'qt6httpserver',
    'qt6labsstylekit',
    'qt6location',
    'qt6multimedia',           # Qt6Multimedia.dll, Qt6MultimediaWidgets.dll, Qt6MultimediaQuick.dll
    'qt6nfc',
    'qt6pdf',                  # Qt6Pdf.dll, Qt6PdfWidgets.dll, Qt6PdfQuick.dll
    # qt6positioning is REQUIRED by Qt6WebEngineCore (HTML5 Geolocation)
    # Qt6Qml.dll, Qt6QmlModels.dll, Qt6QmlMeta.dll are REQUIRED (transitive
    # deps of Qt6WebEngineCore + Qt6WebEngineWidgets + Qt6WebChannel).
    # Only exclude the higher-level QML sub-modules we don't need.
    'qt6qmlcompiler',          # JIT compiler for QML source — not needed at runtime
    # qt6qmlworkerscript is REQUIRED: Qt6QmlMeta.dll imports it directly
    'qt6qmllocalstorage',      # QML SQLite access
    # Qt6Quick.dll and Qt6QuickWidgets.dll are REQUIRED (Qt6WebEngineWidgets
    # depends on both). Only exclude the Quick sub-modules we don't need.
    'qt6quick3d',              # 3D rendering for Quick
    'qt6quickcontrols2',       # UI control framework
    'qt6quickdialogs2',        # dialog framework
    'qt6quicktemplates2',      # control templates
    'qt6quickeffects',         # visual effects
    'qt6quickparticles',       # particle system
    'qt6remoteobjects',
    'qt6scxml',
    'qt6sensors',
    'qt6serialbus',
    'qt6serialport',
    # qt6shadertools is REQUIRED by Qt6Quick (RHI shader pipeline) which is
    # required by Qt6WebEngineWidgets — do NOT exclude
    'qt6spatialaudio',
    'qt6statemachine',
    'qt6texttospeech',
    'qt6uitools',
    'qt6virtualkeyboard',
    'qt6canvaspainter',
    'qt6lottie',               # Lottie animation
    'qt6test',                 # test framework (dev-only)
    'qt6dbus',                 # D-Bus (Linux IPC, not used on Windows)
    'qt6networkauth',          # OAuth2 auth (not used by pywebview)
    'qt6labs',                 # Qt Labs experimental modules (LabsPlatform, etc.)
    'qt6webenginequick',       # QML-based WebEngine (we use WebEngineWidgets)
    'qt6webview',              # simplified WebView (not WebEngineWidgets)
)

# PySide6 .pyd extension-module short-name prefixes to drop
_DROP_PYD_PREFIXES = (
    'qt3d', 'qtaxcontainer', 'qtbluetooth', 'qtcharts', 'qtdatavisualization',
    'qtdesigner', 'qtgraphs', 'qthelp', 'qthttpserver',
    'qtlocation', 'qtmultimedia', 'qtnfc', 'qtpdf',
    # qtpositioning, qtqml, qtquick pyds are NOT dropped — their C++ DLLs
    # are required by Qt6WebEngineCore/Widgets at runtime.
    'qtremoteobjects',
    'qtscxml', 'qtsensors', 'qtserialbus', 'qtserialport',
    'qtspatialaudio', 'qtstatemachine', 'qttexttospeech',
    'qtuitools', 'qtwebenginequick', 'qtwebview', 'qtasyncio',
    'qtcanvaspainter', 'qttest',
    # Python bindings for C++ modules pywebview never imports from Python
    'qtopengl',       # 8.3 MB — WebEngine uses OpenGL via C++, not Python
    'qtsql',          # Qt6Sql.dll is kept for WebEngine storage, .pyd not needed
    'qtdbus',         # D-Bus Python binding (not used on Windows)
    'qtnetworkauth',  # OAuth2 (pywebview doesn't use it)
    'qtxml',          # XML Python binding (not imported by pywebview)
)

_DROP_FILENAMES = {
    # DevTools UI paks (only useful when pywebview starts with debug=True)
    'qtwebengine_devtools_resources.pak',
    # Dev-time Qt tools
    'qmlls.exe', 'qmlformat.exe', 'linguist.exe', 'assistant.exe',
    'lupdate.exe', 'lrelease.exe', 'qmllint.exe', 'metaobjectdump.exe',
    'designer.exe', 'uic.exe', 'qmltyperegistrar.exe',
    # tkinter runtime DLLs
    'tcl86t.dll', 'tk86t.dll', 'tcl86.dll', 'tk86.dll',
}


_DROP_PLUGIN_SUBDIRS = {
    # Qt3D asset pipeline (renderers/ kept — contains rhirenderer.dll required by Qt Quick/WebEngine)
    'assetimporters', 'sceneparsers', 'renderplugins', 'geometryloaders',
    # QML tooling (debug/profiler/linter)
    'qmltooling', 'qmllint',
    # Qt Designer plugins
    'designer',
    # Multimedia (no audio/video playback)
    'multimedia',
    # Hardware peripherals
    'sensors', 'position', 'canbus', 'geoservices',
    # Text-to-speech, SCXML state machines
    'texttospeech', 'scxmldatamodel',
    # Touch/virtual keyboard
    'generic', 'platforminputcontexts', 'virtualkeyboard',
    # Simplified WebView (we use full WebEngineWidgets)
    'webview',
    # Lottie animations
    'vectorimageformats',
}

# SQL drivers we don't need (WebEngine only needs SQLite)
_DROP_SQL_DRIVERS = {
    'qsqlibase.dll', 'qsqloci.dll', 'qsqlpsql.dll',
    'qsqlodbc.dll', 'qsqlmimer.dll',
}

# Image formats not useful for a web UI (web images are handled by WebEngine)
_DROP_IMAGE_FORMATS = {'qicns.dll', 'qtga.dll', 'qwbmp.dll', 'qpdf.dll'}


def _keep_binary(dest_name):
    """Return False for binaries that should be stripped from the bundle."""
    n = dest_name.replace('\\', '/').lower()
    base = os.path.basename(n)
    stem, _, _ = base.partition('.')  # 'qt6quick' from 'qt6quick.dll'

    # Drop everything under qml/ (Qt Quick engine data; we use HTML+JS)
    if '/qml/' in n + '/':
        return False

    # Drop unused Qt6 DLLs by prefix (catches all module variants)
    if base.endswith('.dll') and stem.startswith(_DROP_QT6_PREFIXES):
        return False

    # Drop unused PySide6 .pyd extension modules
    if '.pyd' in base or base.endswith('.so'):
        if stem.startswith(_DROP_PYD_PREFIXES):
            return False

    # Drop specific filenames (dev tools, tkinter, devtools pak)
    if base in _DROP_FILENAMES:
        return False

    # Drop entire plugin subdirectories we don't need
    if '/plugins/' in n:
        # Extract the subdirectory immediately under plugins/
        after_plugins = n.split('/plugins/', 1)[1]
        plugin_subdir = after_plugins.split('/')[0]
        if plugin_subdir in _DROP_PLUGIN_SUBDIRS:
            return False
        # Drop unused SQL drivers (keep only qsqlite.dll)
        if plugin_subdir == 'sqldrivers' and base in _DROP_SQL_DRIVERS:
            return False
        # Drop unused image format plugins
        if plugin_subdir == 'imageformats' and base in _DROP_IMAGE_FORMATS:
            return False

    # Drop clr_loader DLLs
    if n.startswith('clr_loader/') or '/clr_loader/' in n:
        return False

    # Drop pywebview's Edge/WebView2 backend DLLs (we force Qt backend)
    if n.startswith('webview/lib/') or '/webview/lib/' in n:
        return False

    # Drop PIL/Pillow extension modules (.pyd) — not used by jury tool
    if n.startswith('pil/') or '/pil/' in n:
        return False

    return True


def _keep_data(dest_name):
    """Return False for data files that should be stripped from the bundle."""
    n = dest_name.replace('\\', '/').lower()
    base = os.path.basename(n)

    # Debug resources (never loaded in release builds)
    if '.debug.' in base:
        return False

    # DevTools pak
    if base == 'qtwebengine_devtools_resources.pak':
        return False

    # WebEngine locale paks — keep only English
    if 'qtwebengine_locales' in n:
        return base in ('en-us.pak', 'en-gb.pak')

    # QML engine files (we use HTML+JS via WebEngine, not QML)
    if '/qml/' in n + '/':
        return False

    # .pyi type stubs (IDE-only, never imported at runtime)
    if base.endswith('.pyi'):
        return False

    # Qt metatypes JSON (QML designer tooling, not runtime)
    if '/metatypes/' in n + '/':
        return False

    # Qt UI translation files (.qm) — Qt defaults to English, no QTranslator
    # is installed, so all locale .qm files are dead weight.
    if base.endswith('.qm'):
        return False

    # tkinter data directories
    if n.startswith('_tcl_data/') or n.startswith('_tk_data/'):
        return False

    # clr_loader data
    if n.startswith('clr_loader/') or '/clr_loader/' in n:
        return False

    # PIL / Pillow data files
    if n.startswith('pil/') or '/pil/' in n:
        return False

    # Python packaging metadata (RECORD, WHEEL, METADATA, etc.)
    if '.dist-info/' in n + '/':
        return False

    return True


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
    excludes=_PYTHON_EXCLUDES,
    noarchive=False,
    optimize=2,
)

# ── Post-analysis strip ───────────────────────────────────────────────────────
# Filter AFTER Analysis so we catch files added by PyInstaller's own hooks.
a.binaries = [(n, p, t) for n, p, t in a.binaries if _keep_binary(n)]
a.datas    = [(n, p, t) for n, p, t in a.datas    if _keep_data(n)]

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
