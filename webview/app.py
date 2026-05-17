"""pywebview window setup for Jury Selection Tool.

This is the Stage-1 entry point for the HTML-based UI.  The window loads
``webview/static/index.html`` from disk (no network) and exposes ``JuryAPI``
to JavaScript as ``window.pywebview.api``.

Existing CLI / Tkinter entry point (``jury.py``) is untouched; this lives
alongside it as ``jury_v2.py`` so you can run either while migrating.
"""
from __future__ import annotations

import os
import sys

import webview as pywebview

from .api import JuryAPI
from .state import populate_sample


def _resource_path(*parts: str) -> str:
    """Return absolute path to a bundled asset, working both in dev and
    after PyInstaller has frozen the app (``sys._MEIPASS``)."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def _vendor_present() -> bool:
    """Sanity-check that the user has run ``vendor_setup.py``.  If they
    haven't, React/Babel are missing and the UI will be blank."""
    js_dir = _resource_path("webview", "static", "js", "vendor")
    needed = ("react.development.js", "react-dom.development.js", "babel.min.js")
    return all(os.path.exists(os.path.join(js_dir, n)) for n in needed)


def run() -> None:
    api = JuryAPI()
    populate_sample(api)  # Stage-1 demo data — replace with real autosave-load in Stage 3.

    html_path = _resource_path("webview", "static", "index.html")
    if not os.path.exists(html_path):
        raise FileNotFoundError(
            f"UI bundle missing — expected {html_path}.  Did you copy the "
            f"`webview/` folder into your repo?"
        )

    if not _vendor_present():
        print(
            "\n[!] React/Babel files not found under webview/static/js/vendor/.\n"
            "    Run `python vendor_setup.py` once to download them (one-time, "
            "~1MB).  After that the app makes zero network calls.\n",
            file=sys.stderr,
        )

    window = pywebview.create_window(
        title="Jury Selection Tool",
        url=html_path,
        js_api=api,
        width=1600,
        height=1000,
        min_size=(960, 640),
        background_color="#1a1d28",
        easy_drag=False,
    )
    api._bind_window(window)

    # debug=True opens devtools — flip to False for shipped builds.
    pywebview.start(debug=False)


if __name__ == "__main__":
    run()
