from __future__ import annotations
import tkinter as tk

from .colors import C, DARK, LIGHT

# Probe which properties each widget class supports once, then cache.
# Avoids repeated TclError catches across the whole widget tree on every theme switch.
_WIDGET_PROPS_CACHE: dict[type, tuple] = {}
from .config import SETTINGS
from .fonts import FONTS, _FONT_DEFS
from .richtext import _load_rich_into_text


class ThemeMixin:

    def _rescale_fonts(self, base: int) -> None:
        SETTINGS["font_size"] = base
        scale = base / 10.0
        for name, spec in _FONT_DEFS.items():
            FONTS[name].configure(size=max(6, round(spec[0] * scale)))
        self._det_notes_text.refresh_fonts()
        if self._selected_final_jid:
            j = self.jurors.get(self._selected_final_jid)
            self._fj_det_notes_text.config(state="normal")
            _load_rich_into_text(self._fj_det_notes_text, j.notes if j else "")
            self._fj_det_notes_text.config(state="disabled")
        self._redraw()

    def _apply_theme(self, name: str):
        old = dict(C)
        base = DARK if name == "dark" else LIGHT
        C.update({**base, **SETTINGS.get(f"{name}_colors", {})})
        self._theme_name = name
        color_map = {old[k]: C[k] for k in C if old.get(k) != C.get(k)}
        self._retheme_widget(self, color_map)
        self.canvas.configure(bg=C["canvas_bg"])
        self._update_theme_buttons()
        self._redraw()

    def _retheme_widget(self, widget, color_map: dict):
        cls = type(widget)
        if cls not in _WIDGET_PROPS_CACHE:
            _all = ("background", "foreground", "selectbackground", "selectforeground",
                    "activebackground", "activeforeground", "insertbackground",
                    "highlightbackground", "buttonbackground", "troughcolor",
                    "readonlybackground", "selectcolor")
            supported = []
            for prop in _all:
                try:
                    widget.cget(prop)
                    supported.append(prop)
                except tk.TclError:
                    pass
            _WIDGET_PROPS_CACHE[cls] = tuple(supported)
        kw = {}
        for prop in _WIDGET_PROPS_CACHE[cls]:
            val = str(widget.cget(prop))
            if val in color_map:
                kw[prop] = color_map[val]
        if kw:
            try:
                widget.configure(**kw)
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._retheme_widget(child, color_map)

    def _update_theme_buttons(self):
        dark_active = self._theme_name == "dark"
        self._btn_theme_dark.configure(
            bg=C["seat_seated"] if dark_active else C["btn_bg"],
            fg=C["txt_light"] if dark_active else C["btn_fg"],
            relief="sunken" if dark_active else "solid",
        )
        self._btn_theme_light.configure(
            bg=C["seat_seated"] if not dark_active else C["btn_bg"],
            fg=C["txt_light"] if not dark_active else C["btn_fg"],
            relief="sunken" if not dark_active else "solid",
        )
