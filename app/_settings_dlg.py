from __future__ import annotations
import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog

from tkinter import colorchooser
from .colors import C, DARK, LIGHT
from .config import SETTINGS, DEFAULT_SETTINGS, _save_settings, _load_settings
from .fonts import FONTS
from .richtext import RichTextEditor


class SettingsDlgMixin:

    def _open_settings(self):
        self._kill_drag_win()
        self._drag_id = None
        self._drag_source = None
        self._drag_seat_info = None

        dlg = tk.Toplevel(self)
        dlg.title("Preferences")
        dlg.resizable(True, True)
        dlg.minsize(380, 400)
        dlg.transient(self)
        dlg.configure(bg=C["bg"])
        dlg.withdraw()

        _orig_font_size      = SETTINGS["font_size"]
        _orig_seat_font_size = SETTINGS["seat_font_size"]
        _orig_dark_colors    = dict(SETTINGS.get("dark_colors",  {}))
        _orig_light_colors   = dict(SETTINGS.get("light_colors", {}))
        _color_edits = {
            "dark":  dict(SETTINGS.get("dark_colors",  {})),
            "light": dict(SETTINGS.get("light_colors", {})),
        }

        _COLOR_GROUPS = [
            ("Background", [
                ("bg",        "App Background"),
                ("canvas_bg", "Canvas"),
                ("status_bg", "Detail Panel"),
                ("fj_det_bg", "Final Jury Panel"),
            ]),
            ("Seats", [
                ("seat_empty",   "Empty Seat"),
                ("seat_seated",  "Seated"),
                ("seat_excused", "Excused"),
                ("seat_struck",  "Struck"),
                ("seat_final",   "Final Juror"),
                ("seat_alt_fin", "Alternate"),
            ]),
            ("Text", [
                ("txt_dark",      "Primary Text"),
                ("txt_secondary", "Secondary Text"),
                ("input_fg",      "Input Text"),
                ("btn_fg",        "Button Text"),
            ]),
            ("Controls", [
                ("input_bg", "Input Background"),
                ("btn_bg",   "Button Background"),
                ("divider",  "Divider"),
            ]),
            ("Strike Lists", [
                ("danger_bg", "Background"),
                ("danger_fg", "Text"),
            ]),
        ]
        _orig_rte_font       = SETTINGS["rte_font"]
        _orig_rte_bold       = SETTINGS["rte_bold"]
        _orig_rte_italic     = SETTINGS["rte_italic"]
        _orig_rte_underline  = SETTINGS["rte_underline"]
        _orig_zoom           = float(self._zoom_var.get())
        _panel_keys = ("pool_height", "exc_height", "def_height", "pro_height", "both_height",
                       "lf_width", "fj_width", "vp_detail_height", "detail_height")
        _saved_panel_pos = [_load_settings()]

        _dlg_fonts = {name: tkfont.Font(
            family="Helvetica",
            size=FONTS[name].cget("size"),
            weight=FONTS[name].cget("weight"),
            slant=FONTS[name].cget("slant"),
        ) for name in FONTS}

        lbl_kw = dict(bg=C["bg"], fg=C["txt_dark"], font=_dlg_fonts["md"], anchor="e")
        spn_kw = dict(bg=C["input_bg"], fg=C["input_fg"], relief="solid", bd=1,
                      highlightthickness=0, font=_dlg_fonts["md"], width=6,
                      justify="center", buttonbackground=C["btn_bg"])

        def add_section(parent, text, row):
            tk.Label(parent, text=text, bg=C["bg"], fg=C["txt_secondary"],
                     font=_dlg_fonts["sm_bold"]).grid(
                row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 1))
            tk.Frame(parent, bg=C["divider"], height=1).grid(
                row=row + 1, column=0, columnspan=3, sticky="ew", padx=10)

        def add_spinbox(parent, label, from_, to, val, row, unit=None):
            tk.Label(parent, text=label + ":", **lbl_kw).grid(
                row=row, column=0, padx=(10, 6), pady=4, sticky="e")
            var = tk.IntVar(value=int(val))
            tk.Spinbox(parent, from_=from_, to=to, textvariable=var,
                       **spn_kw).grid(row=row, column=1, sticky="w", pady=4)
            if unit:
                tk.Label(parent, text=unit, bg=C["bg"], fg=C["txt_muted"],
                         font=_dlg_fonts["sm"]).grid(row=row, column=2, sticky="w", padx=(4, 10))
            return var

        tab_bar = tk.Frame(dlg, bg=C["bg"])
        tab_bar.pack(fill="x", padx=10, pady=(10, 0))

        content = tk.Frame(dlg, bg=C["bg"], relief="flat", bd=1,
                           highlightthickness=1, highlightbackground=C["divider"])
        content.pack(fill="both", expand=True, padx=10, pady=4)

        pages:       dict[str, tk.Frame]  = {}
        inner_pages: dict[str, tk.Frame]  = {}
        tab_btns:    dict[str, tk.Button] = {}

        def _make_scroll_page(name: str) -> None:
            outer = tk.Frame(content, bg=C["bg"])
            outer.rowconfigure(0, weight=1)
            outer.columnconfigure(0, weight=1)

            cv  = tk.Canvas(outer, bg=C["bg"], highlightthickness=0)
            vsb = tk.Scrollbar(outer, orient="vertical", command=cv.yview)
            cv.configure(yscrollcommand=vsb.set)
            cv.grid(row=0, column=0, sticky="nsew")

            inner = tk.Frame(cv, bg=C["bg"])
            inner.columnconfigure(1, weight=1)
            inner_id = cv.create_window((0, 0), window=inner, anchor="nw")

            def _sync(*_):
                cv.configure(scrollregion=cv.bbox("all"))
                if inner.winfo_reqheight() > max(1, cv.winfo_height()):
                    vsb.grid(row=0, column=1, sticky="ns")
                else:
                    vsb.grid_remove()

            def _on_cv_resize(e):
                cv.itemconfig(inner_id, width=e.width)
                _sync()

            inner.bind("<Configure>", _sync)
            cv.bind("<Configure>", _on_cv_resize)

            def _scroll(e):
                if inner.winfo_reqheight() > cv.winfo_height():
                    cv.yview_scroll(int(-1 * (e.delta / 120)), "units")

            outer.bind("<Enter>", lambda _: cv.bind_all("<MouseWheel>", _scroll))
            outer.bind("<Leave>", lambda _: cv.unbind_all("<MouseWheel>"))

            pages[name]       = outer
            inner_pages[name] = inner

        _canvas_events = ("<Motion>", "<Leave>", "<ButtonPress-1>", "<B1-Motion>",
                          "<ButtonRelease-1>", "<Button-3>", "<Button-2>")
        _disabled_states: dict = {}

        def _lock_main():
            _disabled_states.clear()
            def _walk(w):
                if isinstance(w, tk.Toplevel):
                    return
                cls = w.__class__.__name__
                if cls == "PanedWindow":
                    for child in w.panes():
                        _walk(self.nametowidget(child))
                    return
                if cls in ("Button", "Listbox", "Scale", "Spinbox", "OptionMenu"):
                    try:
                        _disabled_states[w] = w.cget("state")
                        w.configure(state="disabled")
                    except Exception:
                        pass
                for child in w.winfo_children():
                    _walk(child)
            _walk(self)
            for ev in _canvas_events:
                self.canvas.unbind(ev)

        def _unlock_main():
            for w, st in _disabled_states.items():
                try:
                    w.configure(state=st)
                except Exception:
                    pass
            _disabled_states.clear()
            self.canvas.bind("<Motion>",          self._cv_motion)
            self.canvas.bind("<Leave>",           self._cv_leave)
            self.canvas.bind("<ButtonPress-1>",   self._cv_press)
            self.canvas.bind("<B1-Motion>",       self._cv_seat_drag)
            self.canvas.bind("<ButtonRelease-1>", self._cv_drop)
            self.canvas.bind("<Button-3>",        self._cv_rclick)
            self.canvas.bind("<Button-2>",        self._cv_rclick)

        def show_tab(name: str):
            for pg in pages.values():
                pg.pack_forget()
            pages[name].pack(fill="both", expand=True)
            for n, b in tab_btns.items():
                if n == name:
                    b.configure(bg=C["seat_seated"], fg=C["txt_light"], relief="solid")
                else:
                    b.configure(bg=C["btn_bg"], fg=C["btn_fg"], relief="solid")
            if name == "Panels":
                dlg.grab_release()
                dlg.attributes("-topmost", True)
                _lock_main()
            else:
                _unlock_main()
                dlg.grab_set()
                dlg.attributes("-topmost", False)

        for tab_name in ("Grid", "Panels", "Appearance", "Notes", "Misc", "PDF"):
            _make_scroll_page(tab_name)
            b = tk.Button(tab_bar, text=tab_name, relief="solid",
                          bg=C["btn_bg"], fg=C["btn_fg"],
                          activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                          font=_dlg_fonts["md"], padx=14, pady=5, cursor="hand2",
                          bd=1, highlightthickness=0, highlightbackground=C["divider"],
                          command=lambda n=tab_name: show_tab(n))
            b.pack(side="left", padx=(0, 2))
            tab_btns[tab_name] = b

        # ── Grid tab ──────────────────────────────────────────────────────────
        gt = inner_pages["Grid"]
        r = 0
        add_section(gt, "Default Layout", r); r += 2
        v_rows       = add_spinbox(gt, "Rows",       1, 10, SETTINGS["rows"],                  r); r += 1
        v_cols       = add_spinbox(gt, "Columns",    1, 12, SETTINGS["cols"],                  r); r += 1
        v_jury       = add_spinbox(gt, "Jury Size",  1, 24, SETTINGS["jury_size"],             r); r += 1
        v_num_panels = add_spinbox(gt, "Panels",     1, 10, SETTINGS.get("num_panels", 3),     r); r += 1

        tk.Label(gt, text="Starting Corner:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        v_corner = tk.StringVar(value=SETTINGS["corner"])
        cf = tk.Frame(gt, bg=C["bg"])
        cf.grid(row=r, column=1, sticky="w", pady=4)
        for sym, val, crow, ccol in [("↖", "TL", 0, 0), ("↗", "TR", 0, 1),
                                      ("↙", "BL", 1, 0), ("↘", "BR", 1, 1)]:
            tk.Radiobutton(cf, text=sym, variable=v_corner, value=val,
                           indicatoron=False, width=2,
                           bg=C["btn_bg"], selectcolor=C["seat_seated"], fg=C["btn_fg"],
                           activebackground=C["btn_hover"], relief="flat",
                           font=_dlg_fonts["lg"],
                           ).grid(row=crow, column=ccol, padx=1, pady=1)
        r += 1

        add_section(gt, "Seat Tiles", r); r += 2
        v_sw = add_spinbox(gt, "Seat Width",  60, 300, SETTINGS["seat_width"],  r, "px"); r += 1
        v_sh = add_spinbox(gt, "Seat Height", 60, 300, SETTINGS["seat_height"], r, "px"); r += 1
        v_sg = add_spinbox(gt, "Gap",          0,  30, SETTINGS["seat_gap"],    r, "px"); r += 1

        add_section(gt, "Seating Area", r); r += 2
        v_sfs = tk.IntVar(value=SETTINGS["seat_font_size"])
        _sfs_lbl = tk.Label(gt, bg=C["bg"], fg=C["txt_secondary"], font=_dlg_fonts["sm"])
        _sfs_lbl.grid(row=r, column=2, sticky="w", padx=(4, 10))

        def _on_seat_size(val):
            _sfs_lbl.configure(text=f"{int(float(val))}pt")
            SETTINGS["seat_font_size"] = int(float(val))
            self._redraw()

        _on_seat_size(SETTINGS["seat_font_size"])
        tk.Label(gt, text="Seat Text:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        tk.Scale(gt, from_=7, to=18, orient="horizontal", variable=v_sfs,
                 resolution=1, showvalue=False, command=_on_seat_size,
                 bg=C["bg"], troughcolor=C["divider"],
                 activebackground=C["btn_hover"], highlightthickness=0,
                 bd=0, sliderlength=20,
                 ).grid(row=r, column=1, sticky="ew", pady=4)
        r += 1

        v_zoom = tk.DoubleVar(value=round(float(SETTINGS["zoom_default"]), 2))
        _zoom_lbl = tk.Label(gt, bg=C["bg"], fg=C["txt_secondary"], font=_dlg_fonts["sm"])
        _zoom_lbl.grid(row=r, column=2, sticky="w", padx=(4, 10))

        def _on_zoom(val):
            z = round(float(val), 2)
            _zoom_lbl.configure(text=f"{z:.2f}×")
            self._temp_zoom = z
            self._redraw()

        _on_zoom(SETTINGS["zoom_default"])
        tk.Label(gt, text="Default Zoom:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        tk.Scale(gt, from_=0.3, to=2.0, orient="horizontal", variable=v_zoom,
                 resolution=0.05, showvalue=False, command=_on_zoom,
                 bg=C["bg"], troughcolor=C["divider"],
                 activebackground=C["btn_hover"], highlightthickness=0,
                 bd=0, sliderlength=20,
                 ).grid(row=r, column=1, sticky="ew", pady=4)
        r += 1

        # ── Panels tab ────────────────────────────────────────────────────────
        pt = inner_pages["Panels"]
        r = 0
        tk.Label(pt,
                 text="Drag panel edges in the main window to resize.\n"
                      "Use the buttons below to save or reset that layout.",
                 bg=C["bg"], fg=C["txt_muted"], font=_dlg_fonts["sm"], justify="left"
                 ).grid(row=r, column=0, columnspan=3, sticky="w", padx=10, pady=(14, 12))
        r += 1

        def _save_panel_positions():
            sw = 6
            try:
                c0 = self._pane_lv.sash_coord(0)
                c1 = self._pane_lv.sash_coord(1)
                c2 = self._pane_lv.sash_coord(2)
                c3 = self._pane_lv.sash_coord(3)
                SETTINGS["pool_height"] = max(80, c0[1])
                SETTINGS["exc_height"]  = max(40, c1[1] - c0[1] - sw)
                SETTINGS["def_height"]  = max(40, c2[1] - c1[1] - sw)
                SETTINGS["pro_height"]  = max(40, c3[1] - c2[1] - sw)
                SETTINGS["both_height"] = max(40, self._pane_lv.winfo_height() - c3[1] - sw)
            except Exception:
                pass
            try:
                c0 = self._pane_outer.sash_coord(0)
                SETTINGS["lf_width"] = max(140, c0[0])
            except Exception:
                pass
            try:
                c1 = self._pane_outer.sash_coord(1)
                SETTINGS["fj_width"] = max(140, self._pane_outer.winfo_width() - c1[0] - sw)
            except Exception:
                pass
            try:
                c0 = self._pane_vp.sash_coord(0)
                SETTINGS["vp_detail_height"] = max(40, self._pane_vp.winfo_height() - c0[1] - sw)
            except Exception:
                pass
            try:
                c0 = self._pane_fj.sash_coord(0)
                SETTINGS["detail_height"] = max(40, self._pane_fj.winfo_height() - c0[1] - sw)
            except Exception:
                pass
            _save_settings(SETTINGS)
            _saved_panel_pos[0] = {k: SETTINGS[k] for k in _panel_keys}
            _save_btn.configure(text="Saved!", bg=C["seat_final"])
            dlg.after(1500, lambda: _save_btn.configure(
                text="Save Current Positions as Default", bg=C["seat_seated"]))

        def _reset_panel_positions():
            for k in ("pool_height", "exc_height", "def_height", "pro_height", "both_height",
                      "lf_width", "fj_width", "vp_detail_height", "detail_height"):
                SETTINGS[k] = DEFAULT_SETTINGS[k]
            _save_settings(SETTINGS)
            self._apply_panel_positions(SETTINGS)
            _reset_btn.configure(text="Reset!", bg=C["seat_final"])
            dlg.after(1500, lambda: _reset_btn.configure(
                text="Reset to Factory Defaults", bg=C["btn_bg"]))

        def _reset_to_saved_positions():
            self._apply_panel_positions(_saved_panel_pos[0])
            _saved_btn.configure(text="Reset!", bg=C["seat_final"])
            dlg.after(1500, lambda: _saved_btn.configure(
                text="Reset to Saved", bg=C["btn_bg"]))

        _save_btn = tk.Button(pt, text="Save Current Positions as Default",
                              command=_save_panel_positions,
                              bg=C["seat_seated"], fg=C["txt_light"], relief="solid", bd=1,
                              highlightthickness=0, highlightbackground=C["bg"],
                              activebackground=C["primary_active"], activeforeground=C["txt_light"],
                              font=_dlg_fonts["md"], padx=8, pady=8, cursor="hand2")
        _save_btn.grid(row=r, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 8))
        r += 1

        _saved_btn = tk.Button(pt, text="Reset to Saved",
                               command=_reset_to_saved_positions,
                               bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                               highlightthickness=0, highlightbackground=C["bg"],
                               activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                               font=_dlg_fonts["md"], padx=8, pady=8, cursor="hand2")
        _saved_btn.grid(row=r, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 8))
        r += 1

        _reset_btn = tk.Button(pt, text="Reset to Factory Defaults",
                               command=_reset_panel_positions,
                               bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                               highlightthickness=0, highlightbackground=C["bg"],
                               activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                               font=_dlg_fonts["md"], padx=8, pady=8, cursor="hand2")
        _reset_btn.grid(row=r, column=0, columnspan=3, sticky="ew", padx=10)

        # ── Appearance tab ────────────────────────────────────────────────────
        at = inner_pages["Appearance"]
        r = 0
        add_section(at, "Default Theme", r); r += 2
        v_theme = tk.StringVar(value=SETTINGS["theme"])
        tf = tk.Frame(at, bg=C["bg"])
        tf.grid(row=r, column=0, columnspan=3, sticky="w", padx=10, pady=6)
        for tval, tlbl in (("dark", "Dark"), ("light", "Light")):
            tk.Radiobutton(tf, text=tlbl, variable=v_theme, value=tval,
                           bg=C["bg"], fg=C["txt_dark"], selectcolor=C["btn_bg"],
                           activebackground=C["bg"], font=_dlg_fonts["md"],
                           ).pack(side="left", padx=(0, 16))
        r += 1
        add_section(at, "Text Size", r); r += 2
        v_fs = tk.IntVar(value=SETTINGS["font_size"])
        _size_lbl = tk.Label(at, bg=C["bg"], fg=C["txt_secondary"], font=_dlg_fonts["sm"])
        _size_lbl.grid(row=r, column=2, sticky="w", padx=(4, 10))

        def _on_size(val):
            _size_lbl.configure(text=f"{int(float(val))}pt")
            self._rescale_fonts(int(float(val)))

        _on_size(SETTINGS["font_size"])
        tk.Label(at, text="Text Size:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        tk.Scale(at, from_=7, to=18, orient="horizontal", variable=v_fs,
                 resolution=1, showvalue=False, command=_on_size,
                 bg=C["bg"], troughcolor=C["divider"],
                 activebackground=C["btn_hover"], highlightthickness=0,
                 bd=0, sliderlength=20,
                 ).grid(row=r, column=1, sticky="ew", pady=4)
        r += 1

        add_section(at, "Theme Colors", r); r += 2

        # Which theme's colors to edit
        v_edit_theme = tk.StringVar(value=self._theme_name)
        _swatch_btns: dict = {}

        def _base_palette(theme):
            return DARK if theme == "dark" else LIGHT

        def _pick_color(theme, key, label):
            cur = _color_edits[theme].get(key, _base_palette(theme)[key])
            res = colorchooser.askcolor(color=cur, parent=dlg, title=f"Color — {label}")
            if not res or not res[1]:
                return
            chosen = res[1].lower()
            default_val = _base_palette(theme).get(key, "").lower()
            if chosen == default_val:
                _color_edits[theme].pop(key, None)
            else:
                _color_edits[theme][key] = res[1]
            if (theme, key) in _swatch_btns:
                _swatch_btns[(theme, key)].configure(bg=res[1])

        def _build_color_grid():
            for w in _cgrid.winfo_children():
                w.destroy()
            _swatch_btns.clear()
            theme = v_edit_theme.get()
            base  = _base_palette(theme)
            _cgrid.columnconfigure(0, weight=1)
            _cgrid.columnconfigure(1, weight=1)
            cr = 0
            for grp_name, entries in _COLOR_GROUPS:
                tk.Label(_cgrid, text=grp_name, bg=C["bg"], fg=C["txt_secondary"],
                         font=_dlg_fonts["sm_bold"]
                         ).grid(row=cr, column=0, columnspan=2, sticky="w",
                                padx=2, pady=(8, 2))
                cr += 1
                col = 0
                for key, lbl in entries:
                    color = _color_edits[theme].get(key, base[key])
                    cell  = tk.Frame(_cgrid, bg=C["bg"])
                    cell.grid(row=cr, column=col, sticky="w", padx=(2, 10), pady=3)
                    btn = tk.Button(cell, bg=color, width=3, height=1,
                                    relief="solid", bd=1, cursor="hand2",
                                    highlightthickness=0,
                                    command=lambda t=theme, k=key, l=lbl: _pick_color(t, k, l))
                    btn.pack(side="left", padx=(0, 6))
                    tk.Label(cell, text=lbl, bg=C["bg"], fg=C["txt_dark"],
                             font=_dlg_fonts["sm"]).pack(side="left")
                    _swatch_btns[(theme, key)] = btn
                    col += 1
                    if col >= 2:
                        col = 0
                        cr += 1
                if col > 0:
                    cr += 1

        def _reset_colors():
            _color_edits[v_edit_theme.get()].clear()
            _build_color_grid()

        tsf = tk.Frame(at, bg=C["bg"])
        tsf.grid(row=r, column=0, columnspan=3, sticky="ew", padx=10, pady=(4, 0))
        tsf.columnconfigure(1, weight=1)
        ef = tk.Frame(tsf, bg=C["bg"])
        ef.grid(row=0, column=0, sticky="w")
        tk.Label(ef, text="Edit:", bg=C["bg"], fg=C["txt_dark"],
                 font=_dlg_fonts["md"]).pack(side="left", padx=(0, 8))
        for tv, tl in (("dark", "Dark"), ("light", "Light")):
            tk.Radiobutton(ef, text=tl, variable=v_edit_theme, value=tv,
                           bg=C["bg"], fg=C["txt_dark"], selectcolor=C["btn_bg"],
                           activebackground=C["bg"], font=_dlg_fonts["md"],
                           command=_build_color_grid).pack(side="left", padx=(0, 10))
        tk.Button(tsf, text="Reset to Default", cursor="hand2",
                  bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                  highlightthickness=0, activebackground=C["btn_hover"],
                  activeforeground=C["txt_light"], font=_dlg_fonts["sm"],
                  padx=6, pady=2, command=_reset_colors
                  ).grid(row=0, column=2, sticky="e", padx=(0, 10))
        r += 1

        _cgrid = tk.Frame(at, bg=C["bg"])
        _cgrid.grid(row=r, column=0, columnspan=3, sticky="ew", padx=10, pady=(2, 6))
        _build_color_grid()
        r += 1

        # ── Notes tab ─────────────────────────────────────────────────────────
        nt = inner_pages["Notes"]
        r = 0
        add_section(nt, "Default Formatting", r); r += 2

        v_rte_font = tk.StringVar(value=SETTINGS["rte_font"])
        rte_fam = tk.OptionMenu(nt, v_rte_font, *RichTextEditor._FAMILIES)
        rte_fam.configure(bg=C["input_bg"], fg=C["input_fg"], relief="solid", bd=1,
                          highlightthickness=0, padx=4, pady=2, width=14,
                          activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                          font=_dlg_fonts["md"], anchor="w")
        rte_fam["menu"].configure(bg=C["input_bg"], fg=C["input_fg"],
                                  activebackground=C["pool_sel"],
                                  activeforeground=C["txt_light"],
                                  font=_dlg_fonts["md"])
        tk.Label(nt, text="Font:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        rte_fam.grid(row=r, column=1, sticky="w", pady=4, padx=(0, 10))
        r += 1

        v_rte_bold      = tk.BooleanVar(value=SETTINGS["rte_bold"])
        v_rte_italic    = tk.BooleanVar(value=SETTINGS["rte_italic"])
        v_rte_underline = tk.BooleanVar(value=SETTINGS["rte_underline"])

        cbk = dict(bg=C["bg"], fg=C["txt_dark"], selectcolor=C["btn_bg"],
                   activebackground=C["bg"], font=_dlg_fonts["md"],
                   highlightthickness=0, bd=0)
        tk.Label(nt, text="Style:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        sf = tk.Frame(nt, bg=C["bg"])
        sf.grid(row=r, column=1, sticky="w", pady=4)
        tk.Checkbutton(sf, text="Bold",      variable=v_rte_bold,      **cbk).pack(side="left", padx=(0, 10))
        tk.Checkbutton(sf, text="Italic",    variable=v_rte_italic,    **cbk).pack(side="left", padx=(0, 10))
        tk.Checkbutton(sf, text="Underline", variable=v_rte_underline, **cbk).pack(side="left")
        r += 1

        # ── Misc tab ──────────────────────────────────────────────────────────
        mc = inner_pages["Misc"]
        r = 0
        add_section(mc, "Autosave", r); r += 2
        v_autosave = add_spinbox(mc, "Interval", 0, 120,
                                 SETTINGS.get("autosave_interval", 15), r, "min  (0 = off)")
        r += 1
        v_autosave_keep = add_spinbox(mc, "Keep", 1, 20,
                                      SETTINGS.get("autosave_keep", 3), r, "files")
        r += 1

        add_section(mc, "Working Directory", r); r += 2
        tk.Label(mc, text="Directory:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        v_work_dir = tk.StringVar(value=SETTINGS.get("work_dir", ""))
        dir_f = tk.Frame(mc, bg=C["bg"])
        dir_f.grid(row=r, column=1, columnspan=2, sticky="ew", pady=4, padx=(0, 10))
        dir_f.columnconfigure(0, weight=1)
        tk.Entry(dir_f, textvariable=v_work_dir,
                 bg=C["input_bg"], fg=C["input_fg"], font=_dlg_fonts["md"],
                 relief="solid", bd=1, highlightthickness=0,
                 insertbackground=C["input_fg"]
                 ).grid(row=0, column=0, sticky="ew")

        def _browse_work_dir():
            chosen = filedialog.askdirectory(
                title="Select Working Directory",
                initialdir=v_work_dir.get() or os.path.expanduser("~"),
                parent=dlg,
            )
            if chosen:
                v_work_dir.set(chosen)

        tk.Button(dir_f, text="Browse…", command=_browse_work_dir,
                  bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                  highlightthickness=0, activebackground=C["btn_hover"],
                  activeforeground=C["txt_light"],
                  font=_dlg_fonts["md"], padx=8, pady=2, cursor="hand2"
                  ).grid(row=0, column=1, padx=(6, 0))
        r += 1
        tk.Label(mc, text="All save / open dialogs will default to this folder.",
                 bg=C["bg"], fg=C["txt_muted"], font=_dlg_fonts["sm"], justify="left"
                 ).grid(row=r, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 6))

        # ── PDF tab ────────────────────────────────────────────────────────────
        pc = inner_pages["PDF"]
        r = 0
        add_section(pc, "Document", r); r += 2

        tk.Label(pc, text="Page Size:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        v_pdf_page_size = tk.StringVar(value=SETTINGS.get("pdf_page_size", "Letter"))
        _ps_f = tk.Frame(pc, bg=C["bg"])
        _ps_f.grid(row=r, column=1, columnspan=2, sticky="w", pady=4)
        for _pg_size in ("Letter", "A4", "Legal"):
            tk.Radiobutton(_ps_f, text=_pg_size, variable=v_pdf_page_size, value=_pg_size,
                           bg=C["bg"], fg=C["txt_dark"], selectcolor=C["input_bg"],
                           activebackground=C["bg"], font=_dlg_fonts["md"],
                           highlightthickness=0).pack(side="left", padx=(0, 12))
        r += 1

        tk.Label(pc, text="Margins:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        v_pdf_margin = tk.DoubleVar(value=SETTINGS.get("pdf_margin", 0.75))
        tk.Spinbox(pc, from_=0.25, to=2.0, textvariable=v_pdf_margin,
                   increment=0.25, format="%.2f",
                   **spn_kw).grid(row=r, column=1, sticky="w", pady=4)
        tk.Label(pc, text="in  (all sides)", bg=C["bg"], fg=C["txt_muted"],
                 font=_dlg_fonts["sm"]).grid(row=r, column=2, sticky="w", padx=(4, 10))
        r += 1

        add_section(pc, "Content", r); r += 2

        _cbk_pdf = dict(bg=C["bg"], fg=C["txt_dark"], selectcolor=C["input_bg"],
                        activebackground=C["bg"], font=_dlg_fonts["md"],
                        highlightthickness=0)
        v_pdf_summary    = tk.BooleanVar(value=bool(SETTINGS.get("pdf_summary",    True)))
        v_pdf_hide_empty = tk.BooleanVar(value=bool(SETTINGS.get("pdf_hide_empty", False)))
        tk.Label(pc, text="Summary page:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        tk.Checkbutton(pc, text="Include", variable=v_pdf_summary, **_cbk_pdf).grid(
            row=r, column=1, sticky="w", pady=4)
        r += 1
        tk.Label(pc, text="Empty seats:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        tk.Checkbutton(pc, text="Hide", variable=v_pdf_hide_empty, **_cbk_pdf).grid(
            row=r, column=1, sticky="w", pady=4)
        r += 1

        add_section(pc, "Typography", r); r += 2

        tk.Label(pc, text="Font:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        v_pdf_font = tk.StringVar(value=SETTINGS.get("pdf_font", "Helvetica"))
        _fnt_f = tk.Frame(pc, bg=C["bg"])
        _fnt_f.grid(row=r, column=1, columnspan=2, sticky="w", pady=4)
        for _fn_name in ("Helvetica", "Times", "Courier"):
            tk.Radiobutton(_fnt_f, text=_fn_name, variable=v_pdf_font, value=_fn_name,
                           bg=C["bg"], fg=C["txt_dark"], selectcolor=C["input_bg"],
                           activebackground=C["bg"], font=_dlg_fonts["md"],
                           highlightthickness=0).pack(side="left", padx=(0, 12))
        r += 1

        add_section(pc, "Defaults", r); r += 2

        tk.Label(pc, text="Report title:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        v_pdf_title = tk.StringVar(value=SETTINGS.get("pdf_title", ""))
        tk.Entry(pc, textvariable=v_pdf_title,
                 bg=C["input_bg"], fg=C["input_fg"], font=_dlg_fonts["md"],
                 relief="solid", bd=1, highlightthickness=0,
                 insertbackground=C["input_fg"]
                 ).grid(row=r, column=1, columnspan=2, sticky="ew", pady=4, padx=(0, 10))
        r += 1
        tk.Label(pc, text="Pre-fills the title dialog on each export.",
                 bg=C["bg"], fg=C["txt_muted"], font=_dlg_fonts["sm"], justify="left"
                 ).grid(row=r, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 4))
        r += 1

        tk.Label(pc, text="Filename:", **lbl_kw).grid(
            row=r, column=0, padx=(10, 6), pady=4, sticky="e")
        v_pdf_filename = tk.StringVar(value=SETTINGS.get("pdf_filename", "jury_report.pdf"))
        tk.Entry(pc, textvariable=v_pdf_filename,
                 bg=C["input_bg"], fg=C["input_fg"], font=_dlg_fonts["md"],
                 relief="solid", bd=1, highlightthickness=0,
                 insertbackground=C["input_fg"]
                 ).grid(row=r, column=1, columnspan=2, sticky="ew", pady=4, padx=(0, 10))

        show_tab("Grid")

        # ── Button bar ────────────────────────────────────────────────────────
        bf = tk.Frame(dlg, bg=C["bg"])
        bf.pack(fill="x", padx=10, pady=(0, 10))

        _orig_autosave       = SETTINGS.get("autosave_interval", 15)
        _orig_autosave_keep  = SETTINGS.get("autosave_keep", 3)
        _orig_pdf_page_size  = SETTINGS.get("pdf_page_size",  "Letter")
        _orig_pdf_margin     = SETTINGS.get("pdf_margin",     0.75)
        _orig_pdf_title      = SETTINGS.get("pdf_title",      "")
        _orig_pdf_summary    = SETTINGS.get("pdf_summary",    True)
        _orig_pdf_hide_empty = SETTINGS.get("pdf_hide_empty", False)
        _orig_pdf_font       = SETTINGS.get("pdf_font",       "Helvetica")
        _orig_pdf_filename   = SETTINGS.get("pdf_filename",   "jury_report.pdf")
        _orig_work_dir       = SETTINGS.get("work_dir", "")

        def _on_cancel():
            _unlock_main()
            self._temp_zoom = None
            SETTINGS["zoom_default"]        = _orig_zoom
            SETTINGS["seat_font_size"]      = _orig_seat_font_size
            SETTINGS["dark_colors"]         = _orig_dark_colors
            SETTINGS["light_colors"]        = _orig_light_colors
            SETTINGS["rte_font"]            = _orig_rte_font
            SETTINGS["rte_bold"]            = _orig_rte_bold
            SETTINGS["rte_italic"]          = _orig_rte_italic
            SETTINGS["rte_underline"]       = _orig_rte_underline
            SETTINGS["autosave_interval"]   = _orig_autosave
            SETTINGS["autosave_keep"]       = _orig_autosave_keep
            SETTINGS["pdf_page_size"]       = _orig_pdf_page_size
            SETTINGS["pdf_margin"]          = _orig_pdf_margin
            SETTINGS["pdf_title"]           = _orig_pdf_title
            SETTINGS["pdf_summary"]         = _orig_pdf_summary
            SETTINGS["pdf_hide_empty"]      = _orig_pdf_hide_empty
            SETTINGS["pdf_font"]            = _orig_pdf_font
            SETTINGS["pdf_filename"]        = _orig_pdf_filename
            SETTINGS["work_dir"]            = _orig_work_dir
            if SETTINGS["font_size"] != _orig_font_size:
                self._rescale_fonts(_orig_font_size)
            self._apply_theme(self._theme_name)
            dlg.destroy()

        def _reset():
            v_rows.set(DEFAULT_SETTINGS["rows"])
            v_cols.set(DEFAULT_SETTINGS["cols"])
            v_jury.set(DEFAULT_SETTINGS["jury_size"])
            v_num_panels.set(DEFAULT_SETTINGS["num_panels"])
            v_corner.set(DEFAULT_SETTINGS["corner"])
            v_sw.set(DEFAULT_SETTINGS["seat_width"])
            v_sh.set(DEFAULT_SETTINGS["seat_height"])
            v_sg.set(DEFAULT_SETTINGS["seat_gap"])
            v_theme.set(DEFAULT_SETTINGS["theme"])
            v_sfs.set(DEFAULT_SETTINGS["seat_font_size"])
            SETTINGS["seat_font_size"] = DEFAULT_SETTINGS["seat_font_size"]
            v_fs.set(DEFAULT_SETTINGS["font_size"])
            self._rescale_fonts(DEFAULT_SETTINGS["font_size"])
            v_zoom.set(DEFAULT_SETTINGS["zoom_default"])
            _on_zoom(DEFAULT_SETTINGS["zoom_default"])
            v_rte_font.set(DEFAULT_SETTINGS["rte_font"])
            v_rte_bold.set(DEFAULT_SETTINGS["rte_bold"])
            v_rte_italic.set(DEFAULT_SETTINGS["rte_italic"])
            v_rte_underline.set(DEFAULT_SETTINGS["rte_underline"])
            v_autosave.set(DEFAULT_SETTINGS["autosave_interval"])
            v_autosave_keep.set(DEFAULT_SETTINGS["autosave_keep"])
            v_pdf_page_size.set(DEFAULT_SETTINGS["pdf_page_size"])
            v_pdf_margin.set(DEFAULT_SETTINGS["pdf_margin"])
            v_pdf_title.set(DEFAULT_SETTINGS["pdf_title"])
            v_pdf_summary.set(DEFAULT_SETTINGS["pdf_summary"])
            v_pdf_hide_empty.set(DEFAULT_SETTINGS["pdf_hide_empty"])
            v_pdf_font.set(DEFAULT_SETTINGS["pdf_font"])
            v_pdf_filename.set(DEFAULT_SETTINGS["pdf_filename"])
            v_work_dir.set(DEFAULT_SETTINGS["work_dir"])
            _color_edits["dark"].clear()
            _color_edits["light"].clear()
            _build_color_grid()

        def _commit():
            new_rows   = int(v_rows.get())
            new_cols   = int(v_cols.get())
            new_jury   = int(v_jury.get())
            new_corner = v_corner.get()

            new_num_panels = int(v_num_panels.get())
            SETTINGS["rows"]         = new_rows
            SETTINGS["cols"]         = new_cols
            SETTINGS["jury_size"]    = new_jury
            SETTINGS["corner"]       = new_corner
            SETTINGS["num_panels"]   = new_num_panels
            SETTINGS["seat_width"]   = int(v_sw.get())
            SETTINGS["seat_height"]  = int(v_sh.get())
            SETTINGS["seat_gap"]     = int(v_sg.get())
            SETTINGS["theme"]        = v_theme.get()
            SETTINGS["zoom_default"] = round(float(v_zoom.get()), 2)
            SETTINGS["rte_font"]            = v_rte_font.get()
            SETTINGS["rte_bold"]            = bool(v_rte_bold.get())
            SETTINGS["rte_italic"]          = bool(v_rte_italic.get())
            SETTINGS["rte_underline"]       = bool(v_rte_underline.get())
            SETTINGS["autosave_interval"]   = int(v_autosave.get())
            SETTINGS["autosave_keep"]       = int(v_autosave_keep.get())
            SETTINGS["pdf_page_size"]       = v_pdf_page_size.get()
            SETTINGS["pdf_margin"]          = round(float(v_pdf_margin.get()), 2)
            SETTINGS["pdf_title"]           = v_pdf_title.get().strip()
            SETTINGS["pdf_summary"]         = bool(v_pdf_summary.get())
            SETTINGS["pdf_hide_empty"]      = bool(v_pdf_hide_empty.get())
            SETTINGS["pdf_font"]            = v_pdf_font.get()
            SETTINGS["pdf_filename"]        = v_pdf_filename.get().strip() or "jury_report.pdf"
            SETTINGS["work_dir"]            = v_work_dir.get().strip()
            self._schedule_autosave()
            self.SW   = SETTINGS["seat_width"]
            self.SH   = SETTINGS["seat_height"]
            self.SGAP = SETTINGS["seat_gap"]

            layout_changed = (new_rows != self.rows_var.get() or
                              new_cols != self.cols_var.get())
            self.rows_var.set(new_rows)
            self.cols_var.set(new_cols)
            self.jury_size_var.set(new_jury)

            if layout_changed:
                self._layout_changed()

            if new_corner != self._corner:
                self.corner_var.set(new_corner)
                self._corner_changed()

            if new_num_panels != len(self.panel_seats):
                self._resize_panels(new_num_panels)

            SETTINGS["dark_colors"]  = dict(_color_edits["dark"])
            SETTINGS["light_colors"] = dict(_color_edits["light"])
            self._apply_theme(SETTINGS["theme"])
            self._temp_zoom = None
            self._zoom_var.set(SETTINGS["zoom_default"])
            self._redraw()

        def _apply():
            _commit()
            for name in _dlg_fonts:
                _dlg_fonts[name].configure(size=FONTS[name].cget("size"))
            dlg.update_idletasks()
            new_w = max(dlg.winfo_width(), dlg.winfo_reqwidth())
            new_h = max(dlg.winfo_height(), dlg.winfo_reqheight())
            dlg.geometry(f"{new_w}x{new_h}")

        def _save():
            _unlock_main()
            _commit()
            _save_settings(SETTINGS)
            dlg.destroy()

        tk.Button(bf, text="Reset to Defaults", command=_reset,
                  bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                  highlightthickness=0, highlightbackground=C["bg"],
                  activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                  font=_dlg_fonts["md"], padx=8, pady=4, cursor="hand2").pack(side="left")
        tk.Button(bf, text="Cancel", command=_on_cancel,
                  bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                  highlightthickness=0, highlightbackground=C["bg"],
                  activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                  font=_dlg_fonts["md"], padx=8, pady=4, cursor="hand2").pack(side="right")
        tk.Button(bf, text="Save", command=_save,
                  bg=C["seat_seated"], fg=C["txt_light"], relief="solid", bd=1,
                  highlightthickness=0, highlightbackground=C["bg"],
                  activebackground=C["primary_active"], activeforeground=C["txt_light"],
                  font=_dlg_fonts["md"], padx=8, pady=4, cursor="hand2").pack(side="right", padx=(0, 8))
        tk.Button(bf, text="Apply", command=_apply,
                  bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                  highlightthickness=0, highlightbackground=C["bg"],
                  activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                  font=_dlg_fonts["md"], padx=8, pady=4, cursor="hand2").pack(side="right", padx=(0, 4))

        dlg.update_idletasks()
        dw = dlg.winfo_reqwidth()
        dh = int(dlg.winfo_reqheight() * 1.5)
        x = self.winfo_rootx() + (self.winfo_width()  - dw) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dh) // 2
        dlg.geometry(f"{dw}x{dh}+{max(0, x)}+{max(0, y)}")
        dlg.protocol("WM_DELETE_WINDOW", _on_cancel)
        dlg.deiconify()
