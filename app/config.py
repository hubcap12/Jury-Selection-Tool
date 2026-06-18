from __future__ import annotations
import json
import os

SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".jurytool_settings.json")

DEFAULT_SETTINGS: dict = {
    "rows":             4,
    "cols":             7,
    "jury_size":        12,
    "corner":           "TL",
    "pool_height":      240,
    "exc_height":       100,
    "def_height":       100,
    "pro_height":       100,
    "lf_width":         300,
    "fj_width":         250,
    "detail_height":    340,
    "vp_detail_height": 250,
    "seat_width":       125,
    "seat_height":      125,
    "seat_gap":         4,
    "font_size":        10,
    "seat_font_size":   10,
    "zoom_default":     1.0,
    "theme":            "dark",
    "rte_font":         "Helvetica",
    "rte_bold":         False,
    "rte_italic":       False,
    "rte_underline":    False,
    "num_panels":       3,
    "autosave_interval": 15,
    "autosave_keep":    3,
    "pdf_page_size":    "Letter",
    "pdf_margin":       0.75,
    "pdf_title":        "",
    "pdf_summary":      True,
    "pdf_hide_empty":   False,
    "pdf_font":         "Helvetica",
    "pdf_filename":     "jury_report.pdf",
    "work_dir":         "",
    "left_col_width":   280,
    "right_col_width":  280,
    "left_fracs":       [1.4, 0.7, 0.7, 0.7, 0.5],
    "right_fracs":      [1.3, 1.0],
    "both_height":      100,
    "dark_colors":      {},
    "light_colors":     {},
    "drag_enabled":     True,
    "ui_scale":         1.0,
}


def _load_settings() -> dict:
    s = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH) as f:
            s.update({k: v for k, v in json.load(f).items() if k in s})
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return s


def _save_settings(s: dict) -> None:
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(s, f, indent=2)
    except OSError:
        pass


SETTINGS: dict = _load_settings()
