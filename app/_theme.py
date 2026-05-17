from __future__ import annotations
import tkinter as tk
import tkinter.ttk as ttk

from .colors import C, DARK, LIGHT
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

    def _configure_scrollbar_style(self):
        s = self._ttk_style
        for orient in ("Vertical", "Horizontal"):
            s.configure(f"{orient}.TScrollbar",
                background=C["btn_bg"],
                troughcolor=C["input_bg"],
                arrowcolor=C["txt_secondary"],
                borderwidth=0,
                relief="flat",
                arrowsize=12,
            )
            s.map(f"{orient}.TScrollbar",
                background=[("active", C["btn_hover"]), ("disabled", C["btn_bg"])],
                arrowcolor=[("disabled", C["txt_muted"])],
            )

    def _apply_theme(self, name: str):
        old = dict(C)
        C.update(DARK if name == "dark" else LIGHT)
        self._theme_name = name
        color_map = {old[k]: C[k] for k in C if old.get(k) != C.get(k)}
        self._retheme_widget(self, color_map)
        self._configure_scrollbar_style()
        self.canvas.configure(bg=C["canvas_bg"])
        self._update_theme_buttons()
        self._redraw()

    def _retheme_widget(self, widget, color_map: dict):
        props = ("background", "foreground", "selectbackground", "selectforeground",
                 "activebackground", "activeforeground", "insertbackground",
                 "highlightbackground", "buttonbackground", "troughcolor",
                 "readonlybackground", "selectcolor")
        kw = {}
        for prop in props:
            try:
                val = str(widget.cget(prop))
                if val in color_map:
                    kw[prop] = color_map[val]
            except tk.TclError:
                pass
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
