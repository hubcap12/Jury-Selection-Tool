# Jury Selection Tool — Webview UI (Stage 1)

This adds an HTML/CSS/JS rendered UI alongside the existing Tkinter one.
It runs in a native window via [pywebview](https://pywebview.flowrl.com/),
uses the system webview component (Edge WebView2 on Windows), and **makes
zero network calls** at runtime.  All Python business logic stays in Python.

The original `jury.py` and `app/` package are **untouched** — run either.

---

## What's in this bundle

```
jury_v2.py                         ← new entry point (`python jury_v2.py`)
vendor_setup.py                    ← one-time React/Babel downloader
requirements_webview.txt           ← `pywebview>=4.4`
webview/
  __init__.py
  app.py                           ← pywebview window setup
  api.py                           ← JuryAPI exposed to JS as window.pywebview.api
  state.py                         ← sample seed data (replace in Stage 3)
  static/
    index.html
    css/main.css
    js/
      app.jsx · seats.jsx · sidebars.jsx · controls.jsx
      modal.jsx · tweaks-panel.jsx · data.js
      vendor/                      ← populated by vendor_setup.py (gitignored)
```

## Setup

```bash
pip install -r requirements_webview.txt
python vendor_setup.py              # one-time, downloads React+Babel (~1 MB)
python jury_v2.py
```

After `vendor_setup.py` runs, the app makes zero network calls.  You can
verify in Task Manager → Performance → network: zero traffic for the
process.  The HTML / JS / CSS files are all served from disk by pywebview,
just like the rest of your Python source.

## What works in Stage 2

- Window opens, redesigned UI renders
- Sample data loaded from `webview/state.py` (William Miller etc.)
- **Add / Edit / Remove juror** — modal dialog with name, age, keywords, notes
- **Drag-and-drop seating** — drag any juror onto a seat to assign; drop on
  the Preliminary Pool pane to unseat
- **Status changes** — pill row in Juror Details panel covers Seated,
  Excused, Def. Strike, Pro. Strike, Both Struck, Final, Unseat
- **Priority arrows** — ▲▲▲ to ▼▼▼, click to set rating (-3..+3), "—" clears
- **Keywords + notes** — saved per juror on blur
- **Auto Seat** — fills empty seats on active panel from the pool
- **Reset** — wipes all jurors (with confirmation)
- Panel tabs 1/2/3 · Light/Dark toggle · full Tweaks panel

## What's stubbed (Stage 3+)

The action buttons and File menu commands all show a "coming soon" toast
right now.  Each one maps to existing logic in your `app/` package — the
plan is to wire them in stages so you can push working increments:

| Stage | Wires in                                                       |
|-------|----------------------------------------------------------------|
| 3     | Save / Open / Autosave (reuses `app/_fileio.py`) · CSV upload  |
|       | · PDF export (reuses `app/pdf_export.py`)                      |
| 4     | Preferences dialog · rich-text notes editor (uses `app/richtext.py`) |

## Packaging for distribution

Update `JuryTool.spec` to include the static folder.  The existing block:

```python
a = Analysis(
    ['jury.py'],
    ...
    datas=[],
    ...
)
```

becomes:

```python
a = Analysis(
    ['jury_v2.py'],
    ...
    datas=[('webview/static', 'webview/static')],
    ...
)
```

Then build with `pyinstaller JuryTool.spec` as before.  The webview HTML
and vendored JS get bundled into the `.exe` — same self-contained
distribution model you already ship.

## Transparency note for the README

The webview UI is built from the same kind of files anyone can audit:
`webview/static/index.html` and the `.jsx` files alongside it.  React and
Babel come from official upstream sources via `vendor_setup.py` and are
checksummed (where possible).  Nothing else hits the network.
