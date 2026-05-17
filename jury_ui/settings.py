"""Settings bridge between the webview UI and the Tk app's settings file.

We share ``~/.jurytool_settings.json`` with the Tk app via
``app.config.SETTINGS`` so prefs round-trip between both UIs.  Only a
subset of keys are exposed through the webview Preferences modal —
Tk-specific layout heights, sash positions, etc. are left untouched.
"""
from __future__ import annotations

import json
import os
from typing import Any

from app.config import SETTINGS, SETTINGS_PATH, DEFAULT_SETTINGS

# Keys the Preferences UI lets the user edit.  Anything not in this list
# is preserved as-is when ``update`` writes the settings back to disk.
EDITABLE_KEYS: tuple[str, ...] = (
    # Defaults applied to a New Jury
    "rows", "cols", "jury_size", "corner", "num_panels",
    # Autosave
    "autosave_interval", "autosave_keep",
    # PDF export
    "pdf_page_size", "pdf_margin", "pdf_summary", "pdf_hide_empty",
    "pdf_font", "pdf_filename", "pdf_title",
    # Working directory
    "work_dir",
    # Rich-text defaults
    "rte_font", "rte_bold", "rte_italic", "rte_underline",
)

PAGE_SIZE_CHOICES = ("Letter", "A4", "Legal")
PDF_FONT_CHOICES  = ("Helvetica", "Times", "Courier")
RTE_FONT_CHOICES  = ("Helvetica", "Arial", "Times New Roman",
                     "Courier New", "Georgia", "Verdana", "Calibri")
CORNER_CHOICES    = ("TL", "TR", "BL", "BR")


def snapshot() -> dict[str, Any]:
    """Return a copy of the editable settings."""
    return {k: SETTINGS.get(k, DEFAULT_SETTINGS.get(k)) for k in EDITABLE_KEYS}


def update(patch: dict[str, Any]) -> dict[str, Any]:
    """Merge ``patch`` into SETTINGS (in-place) and persist.

    Returns the new snapshot.  Unknown keys are ignored.  Type coercion
    is applied for ints / floats / bools so JS-sent values land cleanly.
    """
    coerced: dict[str, Any] = {}
    for k, v in patch.items():
        if k not in EDITABLE_KEYS:
            continue
        default = DEFAULT_SETTINGS.get(k)
        try:
            if isinstance(default, bool):
                coerced[k] = bool(v)
            elif isinstance(default, int):
                coerced[k] = int(v)
            elif isinstance(default, float):
                coerced[k] = float(v)
            else:
                coerced[k] = v
        except (TypeError, ValueError):
            continue
    SETTINGS.update(coerced)
    _persist()
    return snapshot()


def _persist() -> None:
    """Write the FULL SETTINGS dict (not just our edits) so the Tk app's
    layout-position keys survive a round-trip."""
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(SETTINGS, f, indent=2)
    except OSError:
        pass


def autosave_interval_min() -> int:
    return max(0, int(SETTINGS.get("autosave_interval", 15)))


def autosave_keep() -> int:
    return max(1, int(SETTINGS.get("autosave_keep", 3)))


def work_dir() -> str:
    d = SETTINGS.get("work_dir", "") or ""
    if d and os.path.isdir(d):
        return d
    return os.path.expanduser("~")
