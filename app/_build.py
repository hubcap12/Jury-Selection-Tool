from __future__ import annotations
import tkinter as tk

from .colors import C
from .config import SETTINGS
from .fonts import FONTS
from .richtext import RichTextEditor


class BuildMixin:

    def _build_menu(self):
        m = tk.Menu(self)
        self.config(menu=m)

        fm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="File", menu=fm)
        fm.add_command(label="New",  accelerator="Ctrl+N", command=self._new)
        fm.add_command(label="Save", accelerator="Ctrl+S", command=self._save)
        fm.add_command(label="Open", accelerator="Ctrl+O", command=self._open)
        fm.add_separator()
        fm.add_command(label="Quit", command=self.quit)

        sm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="Settings", menu=sm)
        sm.add_command(label="Preferences…", command=self._open_settings,
                       accelerator="Ctrl+Comma")

        self.bind_all("<Control-n>", lambda _: self._new())
        self.bind_all("<Control-s>", lambda _: self._save())
        self.bind_all("<Control-o>", lambda _: self._open())
        self.bind_all("<Control-comma>", lambda _: self._open_settings())

    def _build_ui(self):
        self._pane_outer = tk.PanedWindow(self, orient="horizontal", bg=C["divider"],
                               sashwidth=6, sashrelief="flat", bd=0,
                               opaqueresize=True)
        outer = self._pane_outer
        outer.pack(fill="both", expand=True, padx=10, pady=(6, 12))

        lf = tk.Frame(outer, bg=C["bg"])
        rf = tk.Frame(outer, bg=C["bg"])
        fj = tk.Frame(outer, bg=C["bg"])
        outer.add(lf, minsize=140, width=215, stretch="never")
        outer.add(rf, minsize=300, stretch="always")
        outer.add(fj, minsize=140, width=SETTINGS["fj_width"], stretch="never")

        # ── Left panel vertical PanedWindow ──────────────────────────────────
        self._pane_lv = tk.PanedWindow(lf, orient="vertical", bg=C["divider"],
                            sashwidth=6, sashrelief="flat", bd=0,
                            opaqueresize=True)
        lv = self._pane_lv
        lv.pack(fill="both", expand=True)

        # ── Pool pane ─────────────────────────────────────────────────────────
        pool_pane = tk.Frame(lv, bg=C["bg"])
        lv.add(pool_pane, minsize=80, height=SETTINGS["pool_height"], stretch="always")

        tk.Label(pool_pane, text="Preliminary Pool", font=FONTS["xl_bold"],
                 bg=C["bg"], fg=C["txt_dark"]).pack(anchor="w", pady=(2, 4))

        box = tk.Frame(pool_pane, bg=C["bg"])
        box.pack(fill="both", expand=True)
        sb = tk.Scrollbar(box, bg=C["btn_bg"], troughcolor=C["input_bg"],
                          activebackground=C["btn_hover"],
                          highlightthickness=0, relief="flat", bd=0)
        sb.pack(side="right", fill="y")
        self.pool_lb = tk.Listbox(
            box, yscrollcommand=sb.set, font=FONTS["lg"],
            selectmode="single", activestyle="none",
            relief="solid", bd=1, highlightthickness=0,
            bg=C["input_bg"], fg=C["input_fg"],
            selectbackground=C["pool_sel"], selectforeground=C["txt_light"],
        )
        self.pool_lb.pack(fill="both", expand=True)
        sb.config(command=self.pool_lb.yview)

        self.pool_lb.bind("<ButtonPress-1>",  self._lb_press)
        self.pool_lb.bind("<B1-Motion>",       self._lb_drag)
        self.pool_lb.bind("<ButtonRelease-1>", self._lb_release)
        self.pool_lb.bind("<Double-Button-1>", self._edit_selected)
        self.pool_lb.bind("<Button-3>",        self._pool_rclick)
        self.pool_lb.bind("<Button-2>",        self._pool_rclick)
        self.pool_lb.bind("<<ListboxSelect>>", self._lb_selection_changed)

        btn_kw = dict(bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                      highlightthickness=0, highlightbackground=C["bg"],
                      activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                      font=FONTS["md"], padx=8, pady=4, cursor="hand2")
        bf = tk.Frame(pool_pane, bg=C["bg"])
        bf.pack(fill="x", pady=(6, 2))
        row1 = tk.Frame(bf, bg=C["bg"])
        row1.pack(fill="x")
        tk.Button(row1, text="Add",       command=self._add,            **btn_kw).pack(side="left", padx=(0, 4))
        tk.Button(row1, text="Edit",      command=self._edit_selected,   **btn_kw).pack(side="left", padx=(0, 4))
        tk.Button(row1, text="Auto Seat", command=self._auto_seat,       **btn_kw).pack(side="left")
        row2 = tk.Frame(bf, bg=C["bg"])
        row2.pack(fill="x", pady=(4, 0))
        tk.Button(row2, text="Remove", command=self._remove, **btn_kw).pack(side="left", padx=(0, 4))
        tk.Button(row2, text="Save",   command=self._save,   **btn_kw).pack(side="left")
        row3 = tk.Frame(bf, bg=C["bg"])
        row3.pack(fill="x", pady=(4, 0))
        tk.Button(row3, text="Upload CSV", command=self._upload_csv,
                  **btn_kw).pack(side="left", padx=(0, 4))
        tk.Button(row3, text="Export PDF", command=self._export_pdf,
                  **btn_kw).pack(side="left")
        row4 = tk.Frame(bf, bg=C["bg"])
        row4.pack(fill="x", pady=(4, 0))
        tk.Button(row4, text="Reset", command=self._new,
                  bg=C["danger_bg"], fg=C["danger_fg"], relief="solid", bd=1,
                  highlightthickness=0, highlightbackground=C["bg"],
                  activebackground=C["danger_hover"], activeforeground=C["danger_fg"],
                  font=FONTS["md"], padx=8, pady=4, cursor="hand2").pack(side="left")

        # ── Excused pane ──────────────────────────────────────────────────────
        exc_pane = tk.Frame(lv, bg=C["bg"])
        lv.add(exc_pane, minsize=50, height=SETTINGS["exc_height"], stretch="never")
        tk.Label(exc_pane, text="Excused", font=FONTS["lg_bold"],
                 bg=C["bg"], fg=C["txt_secondary"]).pack(anchor="w", pady=(4, 2), padx=2)
        exc_box = tk.Frame(exc_pane, bg=C["bg"])
        exc_box.pack(fill="both", expand=True)
        exc_sb = tk.Scrollbar(exc_box, bg=C["btn_bg"], troughcolor=C["input_bg"],
                              activebackground=C["btn_hover"],
                              highlightthickness=0, relief="flat", bd=0)
        exc_sb.pack(side="right", fill="y")
        self.excused_lb = tk.Listbox(
            exc_box, yscrollcommand=exc_sb.set, font=FONTS["md"],
            selectmode="single", activestyle="none",
            relief="solid", bd=1, highlightthickness=0,
            bg=C["input_bg"], fg=C["txt_secondary"],
            selectbackground=C["seat_excused"], selectforeground=C["txt_light"],
        )
        self.excused_lb.pack(fill="both", expand=True)
        exc_sb.config(command=self.excused_lb.yview)
        self.excused_lb.bind("<Button-3>",        self._dismissed_rclick)
        self.excused_lb.bind("<Button-2>",        self._dismissed_rclick)
        self.excused_lb.bind("<<ListboxSelect>>", self._lb_selection_changed)
        self._excused_ids: list[int] = []

        # ── Defense Struck pane ───────────────────────────────────────────────
        def_pane = tk.Frame(lv, bg=C["bg"])
        lv.add(def_pane, minsize=50, height=SETTINGS["def_height"], stretch="never")
        tk.Label(def_pane, text="Defense Struck", font=FONTS["lg_bold"],
                 bg=C["bg"], fg=C["danger_fg"]).pack(anchor="w", pady=(4, 2), padx=2)
        def_box = tk.Frame(def_pane, bg=C["bg"])
        def_box.pack(fill="both", expand=True)
        def_sb = tk.Scrollbar(def_box, bg=C["btn_bg"], troughcolor=C["input_bg"],
                              activebackground=C["btn_hover"],
                              highlightthickness=0, relief="flat", bd=0)
        def_sb.pack(side="right", fill="y")
        self.def_struck_lb = tk.Listbox(
            def_box, yscrollcommand=def_sb.set, font=FONTS["md"],
            selectmode="single", activestyle="none",
            relief="solid", bd=1, highlightthickness=0,
            bg=C["danger_bg"], fg=C["danger_fg"],
            selectbackground=C["seat_struck"], selectforeground=C["txt_light"],
        )
        self.def_struck_lb.pack(fill="both", expand=True)
        def_sb.config(command=self.def_struck_lb.yview)
        self.def_struck_lb.bind("<Button-3>",        self._dismissed_rclick)
        self.def_struck_lb.bind("<Button-2>",        self._dismissed_rclick)
        self.def_struck_lb.bind("<<ListboxSelect>>", self._lb_selection_changed)
        self._def_struck_ids: list[int] = []

        # ── Prosecution Struck pane ───────────────────────────────────────────
        pro_pane = tk.Frame(lv, bg=C["bg"])
        lv.add(pro_pane, minsize=50, height=SETTINGS["pro_height"], stretch="never")
        tk.Label(pro_pane, text="Prosecution Struck", font=FONTS["lg_bold"],
                 bg=C["bg"], fg=C["danger_fg"]).pack(anchor="w", pady=(4, 2), padx=2)
        pro_box = tk.Frame(pro_pane, bg=C["bg"])
        pro_box.pack(fill="both", expand=True)
        pro_sb = tk.Scrollbar(pro_box, bg=C["btn_bg"], troughcolor=C["input_bg"],
                              activebackground=C["btn_hover"],
                              highlightthickness=0, relief="flat", bd=0)
        pro_sb.pack(side="right", fill="y")
        self.pro_struck_lb = tk.Listbox(
            pro_box, yscrollcommand=pro_sb.set, font=FONTS["md"],
            selectmode="single", activestyle="none",
            relief="solid", bd=1, highlightthickness=0,
            bg=C["danger_bg"], fg=C["danger_fg"],
            selectbackground=C["seat_struck"], selectforeground=C["txt_light"],
        )
        self.pro_struck_lb.pack(fill="both", expand=True)
        pro_sb.config(command=self.pro_struck_lb.yview)
        self.pro_struck_lb.bind("<Button-3>",        self._dismissed_rclick)
        self.pro_struck_lb.bind("<Button-2>",        self._dismissed_rclick)
        self.pro_struck_lb.bind("<<ListboxSelect>>", self._lb_selection_changed)
        self._pro_struck_ids: list[int] = []

        # ── Both Struck pane ──────────────────────────────────────────────────
        both_pane = tk.Frame(lv, bg=C["bg"])
        lv.add(both_pane, minsize=50, height=SETTINGS["both_height"], stretch="never")
        tk.Label(both_pane, text="Both Struck", font=FONTS["lg_bold"],
                 bg=C["bg"], fg=C["danger_fg"]).pack(anchor="w", pady=(4, 2), padx=2)
        both_box = tk.Frame(both_pane, bg=C["bg"])
        both_box.pack(fill="both", expand=True)
        both_sb = tk.Scrollbar(both_box, bg=C["btn_bg"], troughcolor=C["input_bg"],
                               activebackground=C["btn_hover"],
                               highlightthickness=0, relief="flat", bd=0)
        both_sb.pack(side="right", fill="y")
        self.both_struck_lb = tk.Listbox(
            both_box, yscrollcommand=both_sb.set, font=FONTS["md"],
            selectmode="single", activestyle="none",
            relief="solid", bd=1, highlightthickness=0,
            bg=C["danger_bg"], fg=C["danger_fg"],
            selectbackground=C["seat_struck"], selectforeground=C["txt_light"],
        )
        self.both_struck_lb.pack(fill="both", expand=True)
        both_sb.config(command=self.both_struck_lb.yview)
        self.both_struck_lb.bind("<Button-3>",        self._dismissed_rclick)
        self.both_struck_lb.bind("<Button-2>",        self._dismissed_rclick)
        self.both_struck_lb.bind("<<ListboxSelect>>", self._lb_selection_changed)
        self._both_struck_ids: list[int] = []

        # ── Final Jury panel (far right) ──────────────────────────────────────
        tk.Label(fj, text="Final Jury", font=FONTS["xl_bold"],
                 bg=C["bg"], fg=C["seat_alt_fin"]).pack(anchor="w", pady=(2, 4))

        self._pane_fj = tk.PanedWindow(fj, orient="vertical", bg=C["divider"],
                            sashwidth=6, sashrelief="flat", bd=0,
                            opaqueresize=True)
        pane_fj = self._pane_fj
        pane_fj.pack(fill="both", expand=True)

        fj_list_pane = tk.Frame(pane_fj, bg=C["bg"])
        pane_fj.add(fj_list_pane, minsize=60, stretch="always")

        fj_box = tk.Frame(fj_list_pane, bg=C["bg"])
        fj_box.pack(fill="both", expand=True)
        fj_sb = tk.Scrollbar(fj_box, bg=C["btn_bg"], troughcolor=C["input_bg"],
                             activebackground=C["btn_hover"],
                             highlightthickness=0, relief="flat", bd=0)
        fj_sb.pack(side="right", fill="y")
        self.final_lb = tk.Listbox(
            fj_box, yscrollcommand=fj_sb.set, font=FONTS["lg"],
            selectmode="single", activestyle="none",
            relief="solid", bd=1, highlightthickness=0,
            bg=C["input_bg"], fg=C["input_fg"],
            selectbackground=C["seat_final"], selectforeground=C["txt_light"],
        )
        self.final_lb.pack(fill="both", expand=True)
        fj_sb.config(command=self.final_lb.yview)
        self.final_lb.bind("<<ListboxSelect>>", self._fj_lb_selection_changed)
        self.final_lb.bind("<Button-3>", self._final_rclick)
        self.final_lb.bind("<Button-2>", self._final_rclick)
        self.final_lb.bind("<Up>",   lambda _: self._fj_nav(-1) or "break")
        self.final_lb.bind("<Down>", lambda _: self._fj_nav( 1) or "break")
        self._final_lb_ids: list[int] = []

        # ── FJ Detail panel ───────────────────────────────────────────────────
        fj_dp = tk.Frame(pane_fj, bg=C["fj_det_bg"], relief="flat")
        pane_fj.add(fj_dp, minsize=40, height=SETTINGS["detail_height"], stretch="never")

        tk.Label(fj_dp, text="Final Jury Info", bg=C["seat_final"],
                 fg=C["txt_light"], font=FONTS["sm_bold"],
                 anchor="w", padx=8, pady=3).pack(fill="x")
        tk.Frame(fj_dp, bg=C["seat_final"], height=1).pack(fill="x")

        fj_inner = tk.Frame(fj_dp, bg=C["fj_det_bg"])
        fj_inner.pack(side="left", fill="both", expand=True, padx=8, pady=6)
        fj_inner.columnconfigure(1, weight=1)
        fj_inner.rowconfigure(2, weight=1)

        self._fj_det_name = tk.StringVar()
        tk.Label(fj_inner, textvariable=self._fj_det_name, bg=C["fj_det_bg"],
                 fg=C["txt_dark"], font=FONTS["lg_bold"], anchor="w"
                 ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        tk.Label(fj_inner, text="Keywords:", bg=C["fj_det_bg"],
                 fg=C["txt_secondary"], font=FONTS["md"]
                 ).grid(row=1, column=0, sticky="w", padx=(0, 6))
        self._fj_det_kw_entry = tk.Entry(
            fj_inner, bg=C["input_bg"], fg=C["input_fg"],
            font=FONTS["md"], relief="flat",
            insertwidth=0, highlightthickness=1, highlightbackground=C["divider"],
            state="readonly", readonlybackground=C["input_bg"],
        )
        self._fj_det_kw_entry.grid(row=1, column=1, sticky="ew", pady=2)

        tk.Label(fj_inner, text="Notes:", bg=C["fj_det_bg"],
                 fg=C["txt_secondary"], font=FONTS["md"]
                 ).grid(row=2, column=0, sticky="nw", padx=(0, 6), pady=(2, 0))
        self._fj_det_notes_text = tk.Text(
            fj_inner, bg=C["input_bg"], fg=C["input_fg"],
            font=FONTS["md_italic"], relief="flat",
            height=2, wrap="word",
            insertwidth=0, highlightthickness=1, highlightbackground=C["divider"],
            state="disabled",
        )
        self._fj_det_notes_text.grid(row=2, column=1, sticky="nsew", pady=2)

        # ── Seating panel (center) ────────────────────────────────────────────
        tk.Label(rf, text="Juror Pool", font=FONTS["xl_bold"],
                 bg=C["bg"], fg=C["txt_dark"]).pack(anchor="center", pady=(2, 2))

        tb = tk.Frame(rf, bg=C["bg"])
        tb.pack(fill="x", pady=(0, 6))

        spin_kw = dict(bg=C["input_bg"], fg=C["input_fg"], relief="solid", bd=1,
                       highlightthickness=0, highlightbackground=C["bg"],
                       font=FONTS["lg"], width=3, justify="center",
                       buttonbackground=C["btn_bg"],
                       disabledbackground=C["input_bg"], disabledforeground=C["txt_muted"])
        lbl_kw  = dict(bg=C["bg"], fg=C["txt_dark"], font=FONTS["lg"])

        tk.Label(tb, text="Rows:", **lbl_kw).pack(side="left", padx=(8, 0))
        self.rows_var = tk.IntVar(value=SETTINGS["rows"])
        tk.Spinbox(tb, from_=1, to=10, textvariable=self.rows_var,
                   command=self._layout_changed, **spin_kw).pack(side="left", padx=(4, 12))

        tk.Label(tb, text="Columns:", **lbl_kw).pack(side="left")
        self.cols_var = tk.IntVar(value=SETTINGS["cols"])
        tk.Spinbox(tb, from_=1, to=12, textvariable=self.cols_var,
                   command=self._layout_changed, **spin_kw).pack(side="left", padx=(4, 20))

        tk.Label(tb, text="Jury Size:", **lbl_kw).pack(side="left", padx=(0, 4))
        self.jury_size_var = tk.IntVar(value=SETTINGS["jury_size"])
        tk.Spinbox(tb, from_=1, to=24, textvariable=self.jury_size_var,
                   command=self._refresh, **spin_kw).pack(side="left", padx=(4, 20))

        tk.Label(tb, text="Start #1:", **lbl_kw).pack(side="left", padx=(0, 6))
        self.corner_var = tk.StringVar(value=SETTINGS["corner"])
        cf = tk.Frame(tb, bg=C["bg"])
        cf.pack(side="left")
        for sym, val, row, col in [("↖", "TL", 0, 0), ("↗", "TR", 0, 1),
                                    ("↙", "BL", 1, 0), ("↘", "BR", 1, 1)]:
            tk.Radiobutton(
                cf, text=sym, variable=self.corner_var, value=val,
                command=self._corner_changed,
                indicatoron=False, width=2,
                bg=C["btn_bg"], selectcolor=C["seat_seated"], fg=C["btn_fg"],
                activebackground=C["btn_hover"], relief="flat",
                font=FONTS["lg"],
            ).grid(row=row, column=col, padx=1, pady=1)

        theme_f = tk.Frame(tb, bg=C["bg"])
        theme_f.pack(side="right", padx=(0, 10))
        self._btn_theme_light = tk.Button(
            theme_f, text="Light", width=5,
            command=lambda: self._apply_theme("light"),
            bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
            highlightthickness=0, highlightbackground=C["bg"],
            activebackground=C["btn_hover"], activeforeground=C["txt_light"],
            padx=6, pady=2, cursor="hand2", font=FONTS["md"],
        )
        self._btn_theme_light.pack(side="left")
        self._btn_theme_dark = tk.Button(
            theme_f, text="Dark", width=5,
            command=lambda: self._apply_theme("dark"),
            bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
            highlightthickness=0, highlightbackground=C["bg"],
            activebackground=C["btn_hover"], activeforeground=C["txt_light"],
            padx=6, pady=2, cursor="hand2", font=FONTS["md"],
        )
        self._btn_theme_dark.pack(side="left", padx=(4, 0))

        self._panel_tab_frame = tk.Frame(tb, bg=C["bg"])
        self._panel_tab_frame.pack(side="left", padx=(20, 0))
        self._panel_tab_btns: list = []

        self._pane_vp = tk.PanedWindow(rf, orient="vertical", bg=C["divider"],
                            sashwidth=6, sashrelief="flat", bd=0,
                            opaqueresize=True)
        vp = self._pane_vp
        vp.pack(fill="both", expand=True)

        cf = tk.Frame(vp, bg=C["canvas_bg"])
        vp.add(cf, minsize=100, stretch="always")

        self._zoom_var = tk.DoubleVar(value=SETTINGS["zoom_default"])
        zoom_frame = tk.Frame(cf, bg=C["status_bg"], width=28)
        zoom_frame.pack(side="right", fill="y")
        zoom_frame.pack_propagate(False)
        tk.Label(zoom_frame, text="+", bg=C["status_bg"], fg=C["txt_secondary"],
                 font=FONTS["md_bold"]).pack(pady=(6, 0))
        self._zoom_slider = tk.Scale(
            zoom_frame, variable=self._zoom_var,
            from_=2.0, to=0.3, orient="vertical", resolution=0.05,
            showvalue=False, command=lambda _: self._redraw(),
            bg=C["status_bg"], troughcolor=C["divider"],
            activebackground=C["btn_hover"], highlightthickness=0,
            bd=0, width=10, sliderlength=18,
        )
        self._zoom_slider.pack(fill="y", expand=True)
        tk.Label(zoom_frame, text="−", bg=C["status_bg"], fg=C["txt_secondary"],
                 font=FONTS["md_bold"]).pack(pady=(0, 6))

        self.canvas = tk.Canvas(cf, bg=C["canvas_bg"], highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>",      lambda _: self._redraw())
        self.canvas.bind("<Motion>",          self._cv_motion)
        self.canvas.bind("<Leave>",           self._cv_leave)
        self.canvas.bind("<ButtonPress-1>",   self._cv_press)
        self.canvas.bind("<B1-Motion>",       self._cv_seat_drag)
        self.canvas.bind("<ButtonRelease-1>", self._cv_drop)
        self.canvas.bind("<Button-3>",        self._cv_rclick)
        self.canvas.bind("<Button-2>",        self._cv_rclick)

        # ── Detail panel ──────────────────────────────────────────────────────
        dp = tk.Frame(vp, bg=C["status_bg"], relief="flat")
        vp.add(dp, minsize=40, height=SETTINGS["vp_detail_height"], stretch="never")

        tk.Label(dp, text="Juror Details", bg=C["status_bg"],
                 fg=C["txt_secondary"], font=FONTS["sm_bold"],
                 anchor="w", padx=12, pady=3).pack(fill="x")
        tk.Frame(dp, bg=C["divider"], height=1).pack(fill="x")

        inner = tk.Frame(dp, bg=C["status_bg"])
        inner.pack(side="left", fill="both", expand=True, padx=12, pady=6)
        inner.columnconfigure(1, weight=1)
        inner.rowconfigure(2, weight=1)

        self._det_name = tk.StringVar()
        tk.Label(inner, textvariable=self._det_name, bg=C["status_bg"],
                 fg=C["txt_dark"], font=FONTS["xl_bold"], anchor="w"
                 ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        tk.Label(inner, text="Keywords:", bg=C["status_bg"],
                 fg=C["txt_secondary"], font=FONTS["md"]
                 ).grid(row=1, column=0, sticky="w", padx=(0, 8))
        self._det_kw_entry = tk.Entry(
            inner, bg=C["input_bg"], fg=C["input_fg"],
            font=FONTS["md"], relief="flat",
            insertbackground=C["input_fg"], insertwidth=0,
            highlightthickness=1, highlightbackground=C["divider"],
            state="readonly", readonlybackground=C["input_bg"],
        )
        self._det_kw_entry.grid(row=1, column=1, sticky="ew", pady=2)
        self._det_kw_entry.bind("<FocusIn>",  lambda _: self._det_kw_entry.config(insertwidth=2))
        self._det_kw_entry.bind("<FocusOut>", lambda _: (self._det_kw_entry.config(insertwidth=0), self._save_detail()))
        self._det_kw_entry.bind("<Return>",   lambda _: self._save_detail() or self.focus_set())

        tk.Label(inner, text="Notes:", bg=C["status_bg"],
                 fg=C["txt_secondary"], font=FONTS["md"]
                 ).grid(row=2, column=0, sticky="nw", padx=(0, 8), pady=(2, 0))
        self._det_notes_text = RichTextEditor(inner, height=2)
        self._det_notes_text.grid(row=2, column=1, sticky="nsew", pady=2)
        self._det_notes_text.bind_text("<FocusOut>", lambda _: self._save_detail())
        self._det_notes_text._text.config(state="disabled")

        tk.Label(inner, text="Priority:", bg=C["status_bg"],
                 fg=C["txt_secondary"], font=FONTS["md"]
                 ).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(6, 0))
        rf2 = tk.Frame(inner, bg=C["status_bg"])
        rf2.grid(row=3, column=1, sticky="w", pady=(6, 0))
        self._rating_btns: dict[int, tk.Button] = {}
        btn_r = dict(relief="solid", bd=1, highlightthickness=0,
                     padx=7, pady=2, cursor="hand2", font=FONTS["md"])
        for val, label in [(3, "▲▲▲"), (2, "▲▲"), (1, "▲")]:
            b = tk.Button(rf2, text=label, bg=C["btn_bg"], fg=C["btn_fg"],
                          activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                          command=lambda v=val: self._set_rating(v), **btn_r)
            b.pack(side="left", padx=(0, 3))
            self._rating_btns[val] = b
        tk.Frame(rf2, bg=C["divider"], width=1).pack(side="left", fill="y", padx=(2, 5))
        for val, label in [(-1, "▼"), (-2, "▼▼"), (-3, "▼▼▼")]:
            b = tk.Button(rf2, text=label, bg=C["btn_bg"], fg=C["btn_fg"],
                          activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                          command=lambda v=val: self._set_rating(v), **btn_r)
            b.pack(side="left", padx=(0, 3))
            self._rating_btns[val] = b

        self.status = tk.StringVar()
        self._update_theme_buttons()
