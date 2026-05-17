"""pywebview window setup for Jury Selection Tool (jury_ui)."""
from __future__ import annotations

import atexit
import os
import sys

import webview as pywebview  # pywebview installs as 'webview' module

from .api import JuryAPI
from .fileio import Autosaver
from .state import populate_sample


def _resource_path(*parts: str) -> str:
    """Absolute path to a bundled asset, working both in dev and after
    PyInstaller has frozen the app (``sys._MEIPASS``)."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def _vendor_present() -> bool:
    """Sanity-check that the user has run ``vendor_setup.py``."""
    js_dir = _resource_path("jury_ui", "static", "js", "vendor")
    needed = ("react.development.js", "react-dom.development.js", "babel.min.js")
    return all(os.path.exists(os.path.join(js_dir, n)) for n in needed)


def _default_work_dir() -> str:
    """Where to put autosave snapshots and where file dialogs open by
    default.  Use the user's home directory; the original Tk app pulls
    this from its settings, which we'll wire up in Stage 4."""
    return os.path.expanduser("~")


def run() -> None:
    api = JuryAPI()
    work_dir = _default_work_dir()
    api.set_work_dir(work_dir)
    populate_sample(api)  # Stage-1 demo data; Stage 3 still seeds initially.

    html_path = _resource_path("jury_ui", "static", "index.html")
    if not os.path.exists(html_path):
        raise FileNotFoundError(
            f"UI bundle missing — expected {html_path}.  Did you copy the "
            f"`jury_ui/` folder into your repo?"
        )

    if not _vendor_present():
        print(
            "\n[!] React/Babel files not found under jury_ui/static/js/vendor/.\n"
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

    # Autosave to rotating snapshots in the work dir, same scheme as
    # the Tk app.  15-minute interval, keep 3 snapshots.
    autosaver = Autosaver(api, work_dir=work_dir, interval_min=15, keep=3)
    autosaver.start()
    atexit.register(autosaver.stop)

    # debug=True opens devtools — flip to False for shipped builds.
    pywebview.start(debug=False)


if __name__ == "__main__":
    run()
