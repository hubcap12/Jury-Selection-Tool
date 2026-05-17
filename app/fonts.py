from __future__ import annotations
import os
import sys
import tkinter.font as tkfont

_FONT_DEFS: dict = {
    "xs":        (8,  "normal", "roman"),
    "sm":        (9,  "normal", "roman"),
    "sm_bold":   (9,  "bold",   "roman"),
    "md":        (10, "normal", "roman"),
    "md_bold":   (10, "bold",   "roman"),
    "md_italic": (10, "normal", "italic"),
    "lg":        (11, "normal", "roman"),
    "lg_bold":   (11, "bold",   "roman"),
    "xl_reg":    (12, "normal", "roman"),
    "xl_bold":   (13, "bold",   "roman"),
    "xxl_bold":  (20, "bold",   "roman"),
}

# Populated by _init_fonts() once a Tk root exists
FONTS: dict = {}


def _init_fonts(base: int = 10) -> None:
    scale = base / 10.0
    for name, (b_size, weight, slant) in _FONT_DEFS.items():
        FONTS[name] = tkfont.Font(
            family="Helvetica",
            size=max(6, round(b_size * scale)),
            weight=weight,
            slant=slant,
        )


def _resource_path(relative: str) -> str:
    """Return path to a bundled resource that works both from source and frozen exe."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        # In dev mode app/ is one level below the project root where resources live
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)
