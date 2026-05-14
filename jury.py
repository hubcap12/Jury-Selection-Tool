#!/usr/bin/env python3
"""Jury Selection Tool — drag jurors from the pool onto the seating chart."""
from __future__ import annotations

import csv
import html
import json
import os
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import date, datetime
from tkinter import filedialog, messagebox

def _resource_path(relative):
    """Resolve a bundled-resource path that works both in source and frozen exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


# ── Settings ──────────────────────────────────────────────────────────────────

SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".jurytool_settings.json")

DEFAULT_SETTINGS: dict = {
    "rows":           4,
    "cols":           7,
    "jury_size":      12,
    "corner":         "TL",
    "pool_height":    240,
    "exc_height":     100,
    "def_height":     100,
    "pro_height":     100,
    "lf_width":        300,
    "fj_width":        250,
    "detail_height":   250,
    "vp_detail_height": 250,
    "seat_width":     125,
    "seat_height":    125,
    "seat_gap":       4,
    "font_size":      10,
    "seat_font_size": 10,
    "zoom_default":   1.0,
    "theme":          "dark",
    "rte_font":       "Helvetica",
    "rte_bold":       False,
    "rte_italic":     False,
    "rte_underline":  False,
    "num_panels":     3,
    "autosave_interval": 15,
    "work_dir":       "",
}


def _load_settings() -> dict:
    s = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH) as f:
            s.update({k: v for k, v in json.load(f).items() if k in s})
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return s


def _save_settings(s: dict):
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(s, f, indent=2)
    except OSError:
        pass


SETTINGS: dict = _load_settings()

DATE_FMTS = (
    "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%Y/%m/%d",
    "%m/%d/%y", "%m-%d-%y", "%B %d, %Y", "%b %d, %Y",
    "%d/%m/%Y", "%d-%m-%Y",
)

# ── Font registry ─────────────────────────────────────────────────────────────
# Base sizes at scale 1.0 (font_size == 10). All scale proportionally.
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
FONTS: dict = {}  # populated by _init_fonts() after a Tk root exists


def _init_fonts(base: int = 10) -> None:
    scale = base / 10.0
    for name, (b_size, weight, slant) in _FONT_DEFS.items():
        FONTS[name] = tkfont.Font(
            family="Helvetica",
            size=max(6, round(b_size * scale)),
            weight=weight,
            slant=slant,
        )

# ─────────────────────────────────────────────────────────────────────────────

STATUS_DISPLAY = {
    "excused":    "Excused",
    "struck_def": "Def. Strike",
    "struck_pro": "Pro. Strike",
}

# ── Visual constants ──────────────────────────────────────────────────────────
SW:   int = SETTINGS["seat_width"]
SH:   int = SETTINGS["seat_height"]
SGAP: int = SETTINGS["seat_gap"]

DARK = dict(
    bg           = "#1e2130",
    input_bg     = "#13151f",
    input_fg     = "#c4c8dc",
    btn_bg       = "#2d3248",
    btn_hover    = "#3a3f58",
    btn_fg       = "#c4c8dc",
    divider      = "#353a52",
    txt_dark     = "#dde0ec",
    txt_light    = "#ffffff",
    txt_secondary= "#7a88b0",
    txt_muted    = "#4a5272",
    danger_bg    = "#2e1a1a",
    danger_fg    = "#e06868",
    danger_hover = "#3d2222",
    canvas_bg    = "#161924",
    seat_empty   = "#282c42",
    seat_hover   = "#3d4468",
    seat_seated  = "#3a72d8",
    seat_excused = "#5a6070",
    seat_struck  = "#c84040",
    seat_final   = "#2a7248",
    seat_alt_fin = "#5a9e72",
    seat_empty_txt = "#4e5880",
    border       = "#404040",
    pool_sel     = "#3a72d8",
    status_bg    = "#252838",
    fj_det_bg    = "#1a2b22",
    test_bg      = "#252010",
    test_fg      = "#c8b030",
    test_hover   = "#303018",
    test_fg_act  = "#d8c040",
    primary_active = "#2a58b8",
)

LIGHT = dict(
    bg           = "#f2f3f7",
    input_bg     = "#ffffff",
    input_fg     = "#111111",
    btn_bg       = "#f0f0f0",
    btn_hover    = "#dddddd",
    btn_fg       = "#111111",
    divider      = "#c0c4cc",
    txt_dark     = "#111111",
    txt_light    = "#ffffff",
    txt_secondary= "#555555",
    txt_muted    = "#888888",
    danger_bg    = "#fdeaea",
    danger_fg    = "#993333",
    danger_hover = "#f5c6c6",
    canvas_bg    = "#e4e5e9",
    seat_empty   = "#ffffff",
    seat_hover   = "#dde8ff",
    seat_seated  = "#2d6dce",
    seat_excused = "#909090",
    seat_struck  = "#cc4444",
    seat_final   = "#2e7d4f",
    seat_alt_fin = "#6aab82",
    seat_empty_txt = "#aaaaaa",
    border       = "#404040",
    pool_sel     = "#2d6dce",
    status_bg    = "#e8eaef",
    fj_det_bg    = "#eff8f2",
    test_bg      = "#fffde8",
    test_fg      = "#665800",
    test_hover   = "#fff9c4",
    test_fg_act  = "#443800",
    primary_active = "#1a4fa0",
)

C = dict(DARK)

# ── Data model ────────────────────────────────────────────────────────────────

class Juror:
    _next = 1

    def __init__(self, name: str, age: str = "", notes: str = "", keywords: str = "", jid: int | None = None):
        if jid is None:
            jid = Juror._next
            Juror._next += 1
        self.id       = jid
        self.name     = name
        self.age      = age
        self.notes    = notes
        self.keywords = keywords
        self.seat: int | None = None
        self.is_alt: bool     = False
        self.status: str      = "pool"  # pool | seated | excused | struck
        self.rating: int      = 0       # -3 to +3  (thumbs down/up, 1–3 intensity)
        self.panel: int       = 0       # which panel index (0-based) this juror is seated in

    @property
    def label(self) -> str:
        return f"#{self.id}  {self.name}"

    def to_dict(self) -> dict:
        return dict(id=self.id, name=self.name, age=self.age, notes=self.notes,
                    keywords=self.keywords, seat=self.seat, is_alt=self.is_alt,
                    status=self.status, rating=self.rating, panel=self.panel)

    @classmethod
    def from_dict(cls, d: dict) -> "Juror":
        j = cls(d["name"], d.get("age", ""), d.get("notes", ""), d.get("keywords", ""), jid=d["id"])
        j.seat    = d.get("seat")
        j.is_alt  = d.get("is_alt", False)
        j.status  = d.get("status", "pool")
        j.rating  = d.get("rating", 0)
        j.panel   = d.get("panel", 0)
        Juror._next = max(Juror._next, j.id + 1)
        return j


# ── Notes format helpers ──────────────────────────────────────────────────────

def _notes_to_runs(notes: str) -> list:
    """Parse a notes string (JSON runs or plain text) into a list of run dicts."""
    if not notes:
        return []
    if notes.startswith("["):
        try:
            runs = json.loads(notes)
            if isinstance(runs, list):
                return runs
        except (json.JSONDecodeError, ValueError):
            pass
    return [{"text": notes}]


def _notes_plain(notes: str) -> str:
    """Extract plain text from a notes string, stripping rich-text markup."""
    return "".join(r.get("text", "") for r in _notes_to_runs(notes))


_RL_FONT_MAP = {
    "Helvetica": "Helvetica", "Arial": "Helvetica",
    "Times New Roman": "Times-Roman", "Georgia": "Times-Roman",
    "Courier New": "Courier",
    "Verdana": "Helvetica", "Calibri": "Helvetica",
}


def _notes_to_rl_markup(notes: str) -> str:
    """Convert notes runs to ReportLab Paragraph inline XML markup."""
    parts = []
    for run in _notes_to_runs(notes):
        text = html.escape(run.get("text", "")).replace("\n", "<br/>")
        if not text:
            continue
        bold      = run.get("bold",      False)
        italic    = run.get("italic",    False)
        underline = run.get("underline", False)
        color     = run.get("color",     None)
        font      = run.get("font",      None)

        if underline:
            text = f"<u>{text}</u>"
        if italic:
            text = f"<i>{text}</i>"
        if bold:
            text = f"<b>{text}</b>"
        attrs = []
        if color:
            attrs.append(f'color="{color}"')
        if font:
            attrs.append(f'name="{_RL_FONT_MAP.get(font, "Helvetica")}"')
        if attrs:
            text = f'<font {" ".join(attrs)}>{text}</font>'
        parts.append(text)
    return "".join(parts)


def _load_rich_into_text(widget: tk.Text, notes: str) -> None:
    """Render notes (plain or JSON runs) into a read-only tk.Text widget."""
    widget.delete("1.0", "end")
    for t in list(widget.tag_names()):
        if t.startswith("rdisp_"):
            try:
                widget.tag_delete(t)
            except tk.TclError:
                pass
    for run in _notes_to_runs(notes):
        text = run.get("text", "")
        if not text:
            continue
        start = widget.index("end-1c")
        widget.insert("end", text)
        ep = widget.index("end-1c")
        if any(k in run for k in ("bold", "italic", "underline", "font")):
            bold  = run.get("bold",  False)
            ital  = run.get("italic", False)
            ul    = run.get("underline", False)
            color = run.get("color", C["input_fg"])
            fam   = run.get("font",  "Helvetica")
            size  = SETTINGS["font_size"]
            tname = f"rdisp_{abs(hash((bold, ital, ul, color, fam)))}"
            widget.tag_configure(tname,
                font=(fam, size, "bold" if bold else "normal",
                      "italic" if ital else "roman"),
                foreground=color, underline=int(ul))
            if widget.compare(start, "<", ep):
                widget.tag_add(tname, start, ep)


# ── Rich text editor widget ───────────────────────────────────────────────────

class RichTextEditor(tk.Frame):
    """A tk.Text with a formatting toolbar (bold, italic, underline, font family)."""

    _FAMILIES = ("Helvetica", "Arial", "Times New Roman", "Courier New",
                 "Georgia", "Verdana", "Calibri")

    def __init__(self, parent, height: int = 6):
        super().__init__(parent, bg=C["bg"])
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._bold      = SETTINGS.get("rte_bold",      False)
        self._italic    = SETTINGS.get("rte_italic",   False)
        self._underline = SETTINGS.get("rte_underline", False)
        self._family    = SETTINGS.get("rte_font",     "Helvetica")
        self._tb_updating = False

        self._fmt_queue: list = []
        self._flush_pending = False

        self._tag_cache: dict[str, str] = {}
        self._rev_cache: dict[str, str] = {}  # tag name → fmt key (inverse of _tag_cache)

        self._build_toolbar()
        self._build_text(height)

    # ── Tag management ────────────────────────────────────────────────────────

    def _fmt_key(self, bold, italic, underline, family):
        return f"b{int(bold)}_i{int(italic)}_u{int(underline)}_f{family}"

    def _parse_key(self, key: str) -> dict:
        parts = key.split("_", 3)
        return dict(
            bold      = parts[0][1:] == "1",
            italic    = parts[1][1:] == "1",
            underline = parts[2][1:] == "1",
            font      = parts[3][1:] if len(parts) > 3 else "Helvetica",
        )

    def _get_tag(self, bold, italic, underline, family) -> str:
        key = self._fmt_key(bold, italic, underline, family)
        if key not in self._tag_cache:
            name = f"rte_{len(self._tag_cache)}"
            self._text.tag_configure(name,
                font=(family, SETTINGS["font_size"],
                      "bold" if bold else "normal",
                      "italic" if italic else "roman"),
                underline=int(underline))
            self._tag_cache[key] = name
            self._rev_cache[name] = key
        return self._tag_cache[key]

    def _fmt_at(self, pos: str) -> dict:
        for t in self._text.tag_names(pos):
            if t in self._rev_cache:
                return self._parse_key(self._rev_cache[t])
        return dict(bold=False, italic=False, underline=False, font=self._family)

    def refresh_fonts(self):
        size = SETTINGS["font_size"]
        for key, tag_name in self._tag_cache.items():
            fmt = self._parse_key(key)
            self._text.tag_configure(tag_name,
                font=(fmt["font"], size,
                      "bold" if fmt["bold"] else "normal",
                      "italic" if fmt["italic"] else "roman"))
        self._text.configure(font=FONTS["md"])

    def _next_tag_start(self, pos: str, end: str) -> str:
        """Return the earliest start of any known RTE tag in [pos, end), or end."""
        result = end
        for tag_name in self._tag_cache.values():
            nxt = self._text.tag_nextrange(tag_name, pos, end)
            if nxt and self._text.compare(str(nxt[0]), "<", result):
                result = str(nxt[0])
        return result

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        self._tb = tk.Frame(self, bg=C["btn_bg"],
                            highlightthickness=1, highlightbackground=C["divider"])
        self._tb.grid(row=0, column=0, sticky="ew")

        bk = dict(bg=C["btn_bg"], fg=C["btn_fg"], relief="flat", bd=0,
                  highlightthickness=0, padx=6, pady=2, cursor="hand2",
                  activebackground=C["btn_hover"], activeforeground=C["txt_light"])

        self._fam_var = tk.StringVar(value=self._family)
        fam = tk.OptionMenu(self._tb, self._fam_var, *self._FAMILIES,
                            command=self._apply_family)
        fam.configure(bg=C["btn_bg"], fg=C["btn_fg"], relief="flat",
                      highlightthickness=0, padx=2, pady=1, width=16,
                      activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                      font=FONTS["sm"], anchor="w")
        fam["menu"].configure(bg=C["input_bg"], fg=C["input_fg"],
                              activebackground=C["pool_sel"],
                              activeforeground=C["txt_light"],
                              font=FONTS["sm"])
        fam.pack(side="left", padx=(2, 0))

        self._tsep()

        self._btn_b = tk.Button(self._tb, text="B",
                                font=FONTS["md_bold"],
                                command=self._toggle_bold, **bk)
        self._btn_b.pack(side="left")
        self._btn_i = tk.Button(self._tb, text="I",
                                font=FONTS["md_italic"],
                                command=self._toggle_italic, **bk)
        self._btn_i.pack(side="left")
        self._btn_u = tk.Button(self._tb, text="U",
                                font=FONTS["md"],
                                command=self._toggle_underline, **bk)
        self._btn_u.pack(side="left")

        self._tsep()

        self._btn_bullet = tk.Button(self._tb, text="•",
                                     font=FONTS["md"],
                                     command=self._toggle_bullet, **bk)
        self._btn_bullet.pack(side="left")

        self._tsep()

        tk.Button(self._tb, text="Clear fmt", font=FONTS["xs"],
                  command=self._clear_fmt, **bk).pack(side="left")

    def _tsep(self):
        tk.Frame(self._tb, bg=C["divider"], width=1).pack(
            side="left", fill="y", padx=3, pady=2)

    # ── Text widget ───────────────────────────────────────────────────────────

    def _build_text(self, height: int):
        self._text = tk.Text(self, wrap="word", height=height,
                             bg=C["input_bg"], fg=C["input_fg"],
                             insertbackground=C["input_fg"],
                             relief="solid", bd=1,
                             font=FONTS["md"],
                             selectbackground=C["pool_sel"],
                             selectforeground=C["txt_light"],
                             undo=True, maxundo=50)
        self._text.tag_configure("bullet_line", lmargin1=4, lmargin2=20)
        self._text.grid(row=1, column=0, sticky="nsew")
        self._text.bind("<KeyPress>",    self._on_key_press)
        self._text.bind("<Return>",      self._on_return)
        self._text.bind("<<Paste>>",     self._on_paste)
        self._text.bind("<<Selection>>", self._on_selection)
        self._text.bind("<Control-b>",   lambda _: self._toggle_bold()      or "break")
        self._text.bind("<Control-i>",   lambda _: self._toggle_italic()    or "break")
        self._text.bind("<Control-u>",   lambda _: self._toggle_underline() or "break")

    # ── Toolbar state ─────────────────────────────────────────────────────────

    def _update_toolbar(self, bold, italic, underline, family):
        # None = mixed selection; only update internal state when unambiguous
        if bold      is not None: self._bold      = bold
        if italic    is not None: self._italic     = italic
        if underline is not None: self._underline  = underline
        if family    is not None: self._family     = family

        self._tb_updating = True
        try:
            self._fam_var.set(family if family is not None else "")
        finally:
            self._tb_updating = False

        def _bstate(btn, on):
            btn.configure(bg=C["btn_hover"] if on else C["btn_bg"],
                          relief="sunken" if on else "flat")
        _bstate(self._btn_b, bool(bold))
        _bstate(self._btn_i, bool(italic))
        _bstate(self._btn_u, bool(underline))

    def _formats_in_range(self, start: str, end: str) -> dict:
        """Walk the selection region-by-region and collect the set of values
        for each format property.  O(number-of-distinct-regions), not O(chars)."""
        seen: dict[str, set] = {
            "bold": set(), "italic": set(), "underline": set(), "font": set(),
        }
        default = dict(bold=False, italic=False, underline=False, font=self._family)
        pos = start
        while self._text.compare(pos, "<", end):
            cur_tag = next((t for t in self._text.tag_names(pos) if t in self._rev_cache), None)
            if cur_tag:
                fmt = self._parse_key(self._rev_cache[cur_tag])
                region_end = end
                for s, e in zip(*[iter(self._text.tag_ranges(cur_tag))] * 2):
                    s, e = str(s), str(e)
                    if (self._text.compare(s, "<=", pos) and
                            self._text.compare(pos, "<", e)):
                        region_end = e if self._text.compare(e, "<=", end) else end
                        break
            else:
                fmt = default
                region_end = self._next_tag_start(self._text.index(f"{pos}+1c"), end)
            for k in seen:
                seen[k].add(fmt.get(k))
            if self._text.compare(region_end, "<=", pos):
                break
            pos = region_end
        return seen

    def _on_selection(self, _=None):
        try:
            sel_start = self._text.index("sel.first")
            sel_end   = self._text.index("sel.last")
        except tk.TclError:
            pos = self._text.index("insert")
            fmt = self._fmt_at(pos)
            self._update_toolbar(fmt["bold"], fmt["italic"], fmt["underline"],
                                 fmt["font"])
            self._update_bullet_btn()
            return

        seen = self._formats_in_range(sel_start, sel_end)
        def _single(s):
            return next(iter(s)) if len(s) == 1 else None

        self._update_toolbar(
            _single(seen["bold"]),
            _single(seen["italic"]),
            _single(seen["underline"]),
            _single(seen["font"]),
        )
        self._update_bullet_btn()

    def _update_bullet_btn(self):
        cur = int(self._text.index("insert").split(".")[0])
        on  = self._is_bullet_line(cur)
        self._btn_bullet.configure(bg=C["btn_hover"] if on else C["btn_bg"],
                                   relief="sunken" if on else "flat")

    # ── Keystroke hooks ───────────────────────────────────────────────────────

    def _on_key_press(self, event):
        if event.char and ord(event.char) >= 32:
            self._fmt_queue.append((
                self._text.index("insert"),
                self._bold, self._italic, self._underline,
                self._family,
            ))
            if not self._flush_pending:
                self._flush_pending = True
                self.after_idle(self._flush_fmt_queue)

    def _flush_fmt_queue(self):
        self._flush_pending = False
        queue = self._fmt_queue[:]
        self._fmt_queue.clear()
        if not queue:
            return
        cur_end = self._text.index("insert")
        starts = [item[0] for item in queue]
        ends   = starts[1:] + [cur_end]
        for (pre, bold, italic, underline, family), end_pos in zip(queue, ends):
            if self._text.compare(pre, ">=", end_pos):
                continue
            tag = self._get_tag(bold, italic, underline, family)
            for t in set(self._tag_cache.values()):
                self._text.tag_remove(t, pre, end_pos)
            self._text.tag_add(tag, pre, end_pos)

    def _on_return(self, _=None):
        pre      = self._text.index("insert")
        cur_line = int(pre.split(".")[0])
        cur_col  = int(pre.split(".")[1])
        # Detect bullet: cursor on a bullet line and past the prefix
        continuing_bullet = self._is_bullet_line(cur_line) and cur_col >= 2
        # If cursor is right after "• " on an otherwise-empty line → remove bullet
        if (self._is_bullet_line(cur_line) and
                self._text.get(f"{cur_line}.0", f"{cur_line}.end") == "• "):
            self._text.delete(f"{cur_line}.0", f"{cur_line}.end")
            self._text.tag_remove("bullet_line", f"{cur_line}.0", f"{cur_line}.end+1c")
            self._btn_bullet.configure(bg=C["btn_bg"], relief="flat")
            return "break"

        self._text.insert("insert", "\n")
        end = self._text.index("insert")
        if self._text.compare(pre, "<", end):
            self._apply_fmt_direct(pre, end)

        if continuing_bullet:
            new_line = int(self._text.index("insert").split(".")[0])
            self._text.insert(f"{new_line}.0", "• ")
            self._text.tag_add("bullet_line", f"{new_line}.0", f"{new_line}.end+1c")

        return "break"

    def _on_paste(self, _=None):
        pre = self._text.index("insert")
        self.after_idle(lambda: self._post_paste(pre))

    def _post_paste(self, pre: str):
        end = self._text.index("insert")
        if self._text.compare(pre, "<", end):
            self._apply_fmt_direct(pre, end)

    def _apply_fmt_direct(self, start: str, end: str):
        tag = self._get_tag(self._bold, self._italic, self._underline, self._family)
        for t in set(self._tag_cache.values()):
            self._text.tag_remove(t, start, end)
        self._text.tag_add(tag, start, end)

    # ── Selection helpers ─────────────────────────────────────────────────────

    def _sel(self):
        try:
            return self._text.index("sel.first"), self._text.index("sel.last")
        except tk.TclError:
            return None

    def _all_have(self, sel, prop: str) -> bool:
        return self._formats_in_range(*sel).get(prop) == {True}

    # ── Apply formatting to a range ───────────────────────────────────────────

    def _apply_range(self, start: str, end: str, **overrides):
        pos = start
        while self._text.compare(pos, "<", end):
            cur_tag = next(
                (t for t in self._text.tag_names(pos) if t in self._rev_cache), None)
            if cur_tag:
                ranges = self._text.tag_ranges(cur_tag)
                region_end = end
                for i in range(0, len(ranges), 2):
                    s, e = str(ranges[i]), str(ranges[i + 1])
                    if (self._text.compare(s, "<=", pos) and
                            self._text.compare(pos, "<", e)):
                        region_end = (e if self._text.compare(e, "<=", end)
                                      else end)
                        break
                cur_fmt = self._parse_key(self._rev_cache[cur_tag])
            else:
                region_end = self._next_tag_start(self._text.index(f"{pos}+1c"), end)
                cur_fmt = dict(bold=False, italic=False, underline=False,
                               font=SETTINGS.get("rte_font", "Helvetica"))
            new_fmt = {**cur_fmt, **overrides}
            new_tag = self._get_tag(new_fmt["bold"], new_fmt["italic"],
                                    new_fmt["underline"], new_fmt["font"])
            if cur_tag:
                self._text.tag_remove(cur_tag, pos, region_end)
            self._text.tag_add(new_tag, pos, region_end)
            if self._text.compare(region_end, "<=", pos):
                break
            pos = region_end

    # ── Toggle / apply actions ────────────────────────────────────────────────

    def _toggle_prop(self, prop: str, btn: tk.Button):
        sel = self._sel()
        if sel:
            new_val = not self._all_have(sel, prop)
            self._apply_range(*sel, **{prop: new_val})
            fmt = self._fmt_at(sel[0])
            self._update_toolbar(fmt["bold"], fmt["italic"], fmt["underline"],
                                 fmt["font"])
        else:
            new_val = not getattr(self, f"_{prop}")
            setattr(self, f"_{prop}", new_val)
            btn.configure(bg=C["btn_hover"] if new_val else C["btn_bg"],
                          relief="sunken" if new_val else "flat")
        self._text.focus_set()

    def _toggle_bold(self):      self._toggle_prop("bold",      self._btn_b)
    def _toggle_italic(self):    self._toggle_prop("italic",    self._btn_i)
    def _toggle_underline(self): self._toggle_prop("underline", self._btn_u)

    def _apply_family(self, family: str):
        self._family = family
        sel = self._sel()
        if sel:
            self._apply_range(*sel, font=family)
        self._text.focus_set()

    def _clear_fmt(self):
        sel = self._sel()
        if not sel:
            return
        start, end = sel
        for t in self._tag_cache.values():
            self._text.tag_remove(t, start, end)
        # Remove bullets from every selected line
        first = int(start.split(".")[0])
        last  = int(end.split(".")[0])
        if end.split(".")[1] == "0" and last > first:
            last -= 1
        for ln in range(first, last + 1):
            self._text.tag_remove("bullet_line", f"{ln}.0", f"{ln}.end+1c")
            if self._is_bullet_line(ln):
                self._text.delete(f"{ln}.0", f"{ln}.2")
        self._update_toolbar(
            SETTINGS.get("rte_bold",      False),
            SETTINGS.get("rte_italic",    False),
            SETTINGS.get("rte_underline", False),
            SETTINGS.get("rte_font",      "Helvetica"),
        )
        self._btn_bullet.configure(bg=C["btn_bg"], relief="flat")
        self._text.focus_set()

    # ── Bullet points ─────────────────────────────────────────────────────────

    def _is_bullet_line(self, line: int) -> bool:
        return self._text.get(f"{line}.0", f"{line}.2") == "• "

    def _toggle_bullet(self):
        try:
            first = int(self._text.index("sel.first").split(".")[0])
            last  = int(self._text.index("sel.last").split(".")[0])
            if self._text.index("sel.last").split(".")[1] == "0" and last > first:
                last -= 1
        except tk.TclError:
            first = last = int(self._text.index("insert").split(".")[0])

        all_bulleted = all(self._is_bullet_line(ln) for ln in range(first, last + 1))

        for ln in range(first, last + 1):
            if all_bulleted:
                if self._is_bullet_line(ln):
                    self._text.delete(f"{ln}.0", f"{ln}.2")
                self._text.tag_remove("bullet_line", f"{ln}.0", f"{ln}.end+1c")
            else:
                if not self._is_bullet_line(ln):
                    self._text.insert(f"{ln}.0", "• ")
                self._text.tag_add("bullet_line", f"{ln}.0", f"{ln}.end+1c")

        # Update button state based on current line
        cur = int(self._text.index("insert").split(".")[0])
        on  = self._is_bullet_line(cur)
        self._btn_bullet.configure(bg=C["btn_hover"] if on else C["btn_bg"],
                                   relief="sunken" if on else "flat")
        self._text.focus_set()

    def _reapply_bullet_tags(self):
        self._text.tag_remove("bullet_line", "1.0", "end")
        last_line = int(self._text.index("end-1c").split(".")[0])
        for ln in range(1, last_line + 1):
            if self._is_bullet_line(ln):
                self._text.tag_add("bullet_line", f"{ln}.0", f"{ln}.end+1c")

    # ── Serialization ─────────────────────────────────────────────────────────

    def get_runs(self) -> list:
        if not self._text.get("1.0", "end-1c"):
            return []
        runs = []
        pos  = "1.0"
        end  = self._text.index("end-1c")
        while self._text.compare(pos, "<", end):
            cur_tag = next(
                (t for t in self._text.tag_names(pos) if t in self._rev_cache), None)
            if cur_tag:
                ranges = self._text.tag_ranges(cur_tag)
                region_end = end
                for i in range(0, len(ranges), 2):
                    s, e = str(ranges[i]), str(ranges[i + 1])
                    if (self._text.compare(s, "<=", pos) and
                            self._text.compare(pos, "<", e)):
                        region_end = (e if self._text.compare(e, "<=", end)
                                      else end)
                        break
                runs.append({"text": self._text.get(pos, region_end),
                             **self._parse_key(self._rev_cache[cur_tag])})
            else:
                region_end = self._next_tag_start(self._text.index(f"{pos}+1c"), end)
                text = self._text.get(pos, region_end)
                if text:
                    runs.append({"text": text})
            if self._text.compare(region_end, "<=", pos):
                break
            pos = region_end
        return runs

    def set_runs(self, runs: list):
        self._text.delete("1.0", "end")
        self._tag_cache.clear()
        self._rev_cache.clear()
        for run in runs:
            text = run.get("text", "")
            if not text:
                continue
            start = self._text.index("end-1c")
            self._text.insert("end", text)
            ep = self._text.index("end-1c")
            if any(k in run for k in
                   ("bold", "italic", "underline", "size", "font")):
                tag = self._get_tag(
                    run.get("bold",      False),
                    run.get("italic",    False),
                    run.get("underline", False),
                    run.get("font",      SETTINGS.get("rte_font", "Helvetica")),
                )
                if self._text.compare(start, "<", ep):
                    self._text.tag_add(tag, start, ep)
        self._reapply_bullet_tags()

    # ── Public helpers ────────────────────────────────────────────────────────

    def contains_widget(self, w) -> bool:
        try:
            ws = str(w)
            return ws == str(self) or ws.startswith(str(self) + ".")
        except Exception:
            return False

    def bind_text(self, sequence, func, add=""):
        return self._text.bind(sequence, func, add)

    def focus_set(self):
        self._text.focus_set()


# ── Add / Edit dialog ─────────────────────────────────────────────────────────

class JurorDialog(tk.Toplevel):
    _last_size: str | None = None  # persists across instances for the session

    def __init__(self, parent: tk.Misc, juror: Juror | None = None):
        super().__init__(parent)
        self.title("Add Juror" if juror is None else "Edit Juror")
        self.resizable(True, True)
        self.minsize(460, 380)
        self.grab_set()
        self.configure(bg=C["bg"])
        self.columnconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)
        self.result:       bool = False
        self.out_name:     str  = ""
        self.out_age:      str  = ""
        self.out_keywords: str  = ""
        self.out_notes:    str  = ""

        p = dict(padx=10, pady=6)
        tk.Label(self, text="Name:", bg=C["bg"], fg=C["txt_dark"], font=FONTS["lg"]).grid(row=0, column=0, sticky="e", **p)
        self._name_var = tk.StringVar(value=juror.name if juror else "")
        entry = tk.Entry(self, textvariable=self._name_var, width=39,
                         bg=C["input_bg"], fg=C["input_fg"], insertbackground=C["input_fg"],
                         relief="solid", bd=1, font=FONTS["lg"])
        entry.grid(row=0, column=1, sticky="ew", **p)
        entry.focus_set()

        tk.Label(self, text="Age:", bg=C["bg"], fg=C["txt_dark"], font=FONTS["lg"]).grid(row=1, column=0, sticky="e", **p)
        self._age_var = tk.StringVar(value=juror.age if juror else "")
        tk.Entry(self, textvariable=self._age_var, width=8,
                 bg=C["input_bg"], fg=C["input_fg"], insertbackground=C["input_fg"],
                 relief="solid", bd=1, font=FONTS["lg"]).grid(row=1, column=1, sticky="w", **p)

        tk.Label(self, text="Keywords:", bg=C["bg"], fg=C["txt_dark"], font=FONTS["lg"]).grid(row=2, column=0, sticky="e", **p)
        self._kw_var = tk.StringVar(value=juror.keywords if juror else "")
        tk.Entry(self, textvariable=self._kw_var, width=39,
                 bg=C["input_bg"], fg=C["input_fg"], insertbackground=C["input_fg"],
                 relief="solid", bd=1, font=FONTS["lg"]).grid(row=2, column=1, sticky="ew", **p)
        tk.Label(self, text="comma-separated", bg=C["bg"], fg=C["txt_muted"],
                 font=FONTS["sm"]).grid(row=2, column=1, sticky="se", padx=10)

        tk.Label(self, text="Notes:", bg=C["bg"], fg=C["txt_dark"], font=FONTS["lg"]).grid(row=3, column=0, sticky="ne", **p)
        self._notes_box = RichTextEditor(self, height=6)
        self._notes_box.grid(row=3, column=1, sticky="nsew", **p)
        if juror and juror.notes:
            self._notes_box.set_runs(_notes_to_runs(juror.notes))

        bf = tk.Frame(self, bg=C["bg"])
        bf.grid(row=4, column=0, columnspan=2, pady=8)
        tk.Button(bf, text="Save",   width=10, command=self._ok,
                  bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                  highlightthickness=0, highlightbackground=C["bg"],
                  activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                  padx=8, pady=4).pack(side="left", padx=4)
        tk.Button(bf, text="Cancel", width=10, command=self.destroy,
                  bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                  highlightthickness=0, highlightbackground=C["bg"],
                  activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                  padx=8, pady=4).pack(side="left", padx=4)

        self.bind("<Return>", lambda _: self._ok())
        self.bind("<Escape>", lambda _: self.destroy())
        self.after(10, self._center, parent)

    def destroy(self):
        try:
            JurorDialog._last_size = self.geometry().split("+")[0]
        except Exception:
            pass
        super().destroy()

    def _center(self, parent: tk.Misc):
        if JurorDialog._last_size:
            self.geometry(JurorDialog._last_size)
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _ok(self):
        name = self._name_var.get().strip()
        if not name:
            return
        self.out_name     = name
        self.out_age      = self._age_var.get().strip()
        self.out_keywords = self._kw_var.get().strip()
        runs = self._notes_box.get_runs()
        if runs and any(k in r for r in runs
                        for k in ("bold", "italic", "underline", "font")):
            self.out_notes = json.dumps(runs, ensure_ascii=False)
        elif runs:
            self.out_notes = "".join(r.get("text", "") for r in runs).strip()
        else:
            self.out_notes = ""
        self.result    = True
        self.destroy()


# ── Main application ──────────────────────────────────────────────────────────

class JuryApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Jury Selection Tool")
        self.minsize(820, 520)
        self.configure(bg=C["bg"])
        try:
            self.iconbitmap(_resource_path("icon.ico"))
        except Exception:
            pass
        self.jurors:      dict[int, Juror]        = {}
        self.panel_seats: list[dict]             = []  # one seats-dict per panel
        self._active_panel: int                  = 0
        self.final_jury:  list[int]              = []  # ordered jids selected for final jury
        self._fj_pos:     dict[int, int]         = {}  # jid → 1-based position in final_jury

        self._theme_name:     str               = SETTINGS["theme"]
        if SETTINGS["theme"] == "light":
            C.update(LIGHT)
            self.configure(bg=C["bg"])
        self._corner:         str               = SETTINGS["corner"]
        _init_fonts(SETTINGS["font_size"])

        self._autosave_id:    str | None        = None
        self._drag_id:        int | None        = None
        self._drag_source:    str | None        = None  # "pool" | "seat"
        self._drag_seat_info: tuple | None      = None  # (is_alt, seat#)
        self._drag_win:       tk.Toplevel | None = None
        self._hovered:        tuple | None       = None  # (is_alt, seat#)
        self._selected_jid:       int | None        = None  # pinned seat detail panel
        self._selected_final_jid: int | None        = None  # pinned final jury detail panel
        self._pool_ids:           list[int]          = []
        self._redraw_pending:     bool               = False
        self._det_notes_loaded:   str                = ""
        self._seat_geo:           dict | None        = None  # cached layout for hit-testing & per-seat redraw

        self._build_menu()
        self._build_ui()
        self.bind_all("<Button-1>", self._defocus_detail, "+")
        self._init_layout()
        self._schedule_autosave()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.withdraw()
        self._show_startup()
        self.deiconify()
        self.state("zoomed")
        self.after(200, lambda: self._apply_panel_positions(SETTINGS))

    # ── Close ─────────────────────────────────────────────────────────────────

    def _on_close(self):
        if messagebox.askyesno(
            "Exit",
            "Exit the Jury Selection Tool?\n\nAny unsaved data will be lost.",
            icon="warning",
            default="no",
        ):
            self.destroy()

    # ── Startup dialog ────────────────────────────────────────────────────────

    def _show_startup(self):
        dlg = tk.Toplevel(self)
        dlg.title("Jury Selection Tool")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(bg=C["bg"])
        dlg.protocol("WM_DELETE_WINDOW", self.destroy)

        tk.Label(dlg, text="Jury Selection Tool",
                 font=FONTS["xxl_bold"], bg=C["bg"], fg=C["txt_dark"]
                 ).pack(pady=(36, 6), padx=50)
        tk.Label(dlg, text="How would you like to begin?",
                 font=FONTS["xl_reg"], bg=C["bg"], fg=C["txt_secondary"]
                 ).pack(pady=(0, 28))

        btn_kw = dict(font=FONTS["xl_reg"], relief="solid", bd=1,
                      highlightthickness=0, highlightbackground=C["bg"],
                      padx=20, pady=10, cursor="hand2", width=18)

        def pick_new():
            dlg.destroy()

        def pick_load():
            dlg.destroy()
            self._open()

        tk.Button(dlg, text="Start New Jury", command=pick_new,
                  bg=C["seat_seated"], fg=C["txt_light"],
                  activebackground=C["primary_active"], activeforeground=C["txt_light"],
                  **btn_kw).pack(pady=(0, 10), padx=50)
        tk.Button(dlg, text="Load from File…", command=pick_load,
                  bg=C["btn_bg"], fg=C["btn_fg"],
                  activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                  **btn_kw).pack(pady=(0, 36), padx=50)

        dlg.update_idletasks()
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        w, h   = dlg.winfo_width(), dlg.winfo_height()
        dlg.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

        self.wait_window(dlg)

    # ── Menu ──────────────────────────────────────────────────────────────────

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

    # ── Settings dialog ───────────────────────────────────────────────────────

    def _open_settings(self):
        global SW, SH, SGAP

        dlg = tk.Toplevel(self)
        dlg.title("Preferences")
        dlg.resizable(True, True)
        dlg.minsize(380, 400)
        dlg.transient(self)
        dlg.configure(bg=C["bg"])
        dlg.withdraw()

        _orig_font_size      = SETTINGS["font_size"]
        _orig_seat_font_size = SETTINGS["seat_font_size"]
        _orig_rte_font       = SETTINGS["rte_font"]
        _orig_rte_bold       = SETTINGS["rte_bold"]
        _orig_rte_italic     = SETTINGS["rte_italic"]
        _orig_rte_underline  = SETTINGS["rte_underline"]
        _orig_zoom           = float(self._zoom_var.get())
        _panel_keys = ("pool_height", "exc_height", "def_height", "pro_height",
                       "lf_width", "fj_width", "vp_detail_height", "detail_height")
        _saved_panel_pos = [_load_settings()]  # list-box so inner functions can rebind

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

        # ── Custom tab bar ────────────────────────────────────────────────────
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
        _disabled_states: dict = {}   # widget → original state string

        def _lock_main():
            """Disable all interactive main-window widgets except PanedWindow sashes."""
            _disabled_states.clear()
            def _walk(w):
                if isinstance(w, tk.Toplevel):
                    return  # never walk into other windows (e.g. this dialog)
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
            """Restore all previously disabled widgets."""
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
                    b.configure(bg=C["seat_seated"], fg=C["txt_light"], relief="flat")
                else:
                    b.configure(bg=C["btn_bg"], fg=C["btn_fg"], relief="flat")
            if name == "Panels":
                dlg.grab_release()
                dlg.attributes("-topmost", True)
                _lock_main()
            else:
                _unlock_main()
                dlg.grab_set()
                dlg.attributes("-topmost", False)

        for tab_name in ("Grid", "Panels", "Appearance", "Notes", "Misc"):
            _make_scroll_page(tab_name)
            b = tk.Button(tab_bar, text=tab_name, relief="flat",
                          bg=C["btn_bg"], fg=C["btn_fg"],
                          activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                          font=_dlg_fonts["md"], padx=14, pady=5, cursor="hand2",
                          bd=0, highlightthickness=0,
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
                SETTINGS["pool_height"] = max(80, c0[1])
                SETTINGS["exc_height"]  = max(40, c1[1] - c0[1] - sw)
                SETTINGS["def_height"]  = max(40, c2[1] - c1[1] - sw)
                SETTINGS["pro_height"]  = max(40, self._pane_lv.winfo_height() - c2[1] - sw)
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
            for k in ("pool_height", "exc_height", "def_height", "pro_height",
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

        show_tab("Grid")

        # ── Button bar ────────────────────────────────────────────────────────
        bf = tk.Frame(dlg, bg=C["bg"])
        bf.pack(fill="x", padx=10, pady=(0, 10))

        _orig_autosave  = SETTINGS.get("autosave_interval", 15)
        _orig_work_dir  = SETTINGS.get("work_dir", "")

        def _on_cancel():
            _unlock_main()
            self._temp_zoom = None
            SETTINGS["zoom_default"]        = _orig_zoom
            SETTINGS["seat_font_size"]      = _orig_seat_font_size
            SETTINGS["rte_font"]            = _orig_rte_font
            SETTINGS["rte_bold"]            = _orig_rte_bold
            SETTINGS["rte_italic"]          = _orig_rte_italic
            SETTINGS["rte_underline"]       = _orig_rte_underline
            SETTINGS["autosave_interval"]   = _orig_autosave
            SETTINGS["work_dir"]            = _orig_work_dir
            if SETTINGS["font_size"] != _orig_font_size:
                self._rescale_fonts(_orig_font_size)  # also calls _redraw
            else:
                self._redraw()
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
            self._rescale_fonts(DEFAULT_SETTINGS["font_size"])  # also calls _redraw
            v_zoom.set(DEFAULT_SETTINGS["zoom_default"])
            _on_zoom(DEFAULT_SETTINGS["zoom_default"])
            v_rte_font.set(DEFAULT_SETTINGS["rte_font"])
            v_rte_bold.set(DEFAULT_SETTINGS["rte_bold"])
            v_rte_italic.set(DEFAULT_SETTINGS["rte_italic"])
            v_rte_underline.set(DEFAULT_SETTINGS["rte_underline"])
            v_autosave.set(DEFAULT_SETTINGS["autosave_interval"])
            v_work_dir.set(DEFAULT_SETTINGS["work_dir"])

        def _commit():
            global SW, SH, SGAP
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
            SETTINGS["work_dir"]            = v_work_dir.get().strip()
            self._schedule_autosave()
            SW   = SETTINGS["seat_width"]
            SH   = SETTINGS["seat_height"]
            SGAP = SETTINGS["seat_gap"]

            # Sync live toolbar vars so _redraw / _layout_changed see new values
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

        # centre dialog over main window now that all widgets exist
        dlg.update_idletasks()
        dw = dlg.winfo_reqwidth()
        dh = int(dlg.winfo_reqheight() * 1.5)
        x = self.winfo_rootx() + (self.winfo_width()  - dw) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dh) // 2
        dlg.geometry(f"{dw}x{dh}+{max(0, x)}+{max(0, y)}")
        dlg.protocol("WM_DELETE_WINDOW", _on_cancel)
        dlg.deiconify()

    # ── UI ────────────────────────────────────────────────────────────────────

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

        # ── Pool pane (top) ───────────────────────────────────────────────────
        pool_pane = tk.Frame(lv, bg=C["bg"])
        lv.add(pool_pane, minsize=80, height=SETTINGS["pool_height"], stretch="always")

        tk.Label(pool_pane, text="Preliminary Pool", font=FONTS["xl_bold"],
                 bg=C["bg"], fg=C["txt_dark"]).pack(anchor="w", pady=(2, 4))

        box = tk.Frame(pool_pane, bg=C["bg"])
        box.pack(fill="both", expand=True)
        sb = tk.Scrollbar(box)
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
        exc_sb = tk.Scrollbar(exc_box)
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
        def_sb = tk.Scrollbar(def_box)
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
        pro_sb = tk.Scrollbar(pro_box)
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
        fj_sb = tk.Scrollbar(fj_box)
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

        # Zoom slider — drag up to enlarge seats, down to shrink
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
        rf = tk.Frame(inner, bg=C["status_bg"])
        rf.grid(row=3, column=1, sticky="w", pady=(6, 0))
        self._rating_btns: dict[int, tk.Button] = {}
        btn_r = dict(relief="solid", bd=1, highlightthickness=0,
                     padx=7, pady=2, cursor="hand2", font=FONTS["md"])
        for val, label in [(3, "▲▲▲"), (2, "▲▲"), (1, "▲")]:
            b = tk.Button(rf, text=label, bg=C["btn_bg"], fg=C["btn_fg"],
                          activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                          command=lambda v=val: self._set_rating(v), **btn_r)
            b.pack(side="left", padx=(0, 3))
            self._rating_btns[val] = b
        tk.Frame(rf, bg=C["divider"], width=1).pack(side="left", fill="y", padx=(2, 5))
        for val, label in [(-1, "▼"), (-2, "▼▼"), (-3, "▼▼▼")]:
            b = tk.Button(rf, text=label, bg=C["btn_bg"], fg=C["btn_fg"],
                          activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                          command=lambda v=val: self._set_rating(v), **btn_r)
            b.pack(side="left", padx=(0, 3))
            self._rating_btns[val] = b

        self.status = tk.StringVar()
        self._update_theme_buttons()

    # ── Theming / scaling ─────────────────────────────────────────────────────

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
        C.update(DARK if name == "dark" else LIGHT)
        self._theme_name = name
        color_map = {old[k]: C[k] for k in C if old.get(k) != C.get(k)}
        self._retheme_widget(self, color_map)
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

    # ── Panel management ──────────────────────────────────────────────────────

    @property
    def seats(self) -> dict:
        return self.panel_seats[self._active_panel]

    @seats.setter
    def seats(self, value: dict):
        self.panel_seats[self._active_panel] = value

    def _update_panel_tabs(self):
        for w in self._panel_tab_frame.winfo_children():
            w.destroy()
        self._panel_tab_btns = []
        for i in range(len(self.panel_seats)):
            active = (i == self._active_panel)
            b = tk.Button(
                self._panel_tab_frame,
                text=f"Panel {i + 1}",
                command=lambda idx=i: self._switch_panel(idx),
                bg=C["seat_seated"] if active else C["btn_bg"],
                fg=C["txt_light"]   if active else C["btn_fg"],
                relief="solid", bd=1,
                highlightthickness=0,
                highlightbackground=C["divider"],
                font=FONTS["md_bold"] if active else FONTS["md"],
                padx=14, pady=5, cursor="hand2",
                activebackground=C["primary_active"], activeforeground=C["txt_light"],
            )
            b.pack(side="left", padx=(0, 3))
            self._panel_tab_btns.append(b)

    def _switch_panel(self, idx: int):
        if idx == self._active_panel:
            return
        self._save_detail()
        self._active_panel = idx
        if self._selected_jid is not None:
            self._selected_jid = None
            self._clear_detail()
        self._update_panel_tabs()
        self._redraw()

    def _resize_panels(self, n: int):
        rows = max(1, int(self.rows_var.get()))
        cols = max(1, int(self.cols_var.get()))
        while len(self.panel_seats) < n:
            self.panel_seats.append({i: None for i in range(1, rows * cols + 1)})
        while len(self.panel_seats) > n:
            removed = self.panel_seats.pop()
            for jid in removed.values():
                if jid is not None:
                    j = self.jurors.get(jid)
                    if j:
                        j.seat, j.is_alt, j.panel = None, False, 0
                        if j.status not in ("excused", "struck_def", "struck_pro"):
                            j.status = "pool"
        if self._active_panel >= len(self.panel_seats):
            self._active_panel = len(self.panel_seats) - 1
        self._update_panel_tabs()
        self._refresh()

    # ── Corner / seat numbering ───────────────────────────────────────────────

    def _seat_num(self, r: int, c: int, rows: int, cols: int, corner: str) -> int:
        if corner == "TL":
            return r * cols + c + 1
        elif corner == "TR":
            return r * cols + (cols - 1 - c) + 1
        elif corner == "BL":
            return (rows - 1 - r) * cols + c + 1
        else:  # BR
            return (rows - 1 - r) * cols + (cols - 1 - c) + 1

    def _seat_pos(self, sn: int, rows: int, cols: int, corner: str) -> tuple[int, int]:
        idx = sn - 1
        r_idx, c_idx = divmod(idx, cols)
        if corner == "TL":
            return (r_idx, c_idx)
        elif corner == "TR":
            return (r_idx, cols - 1 - c_idx)
        elif corner == "BL":
            return (rows - 1 - r_idx, c_idx)
        else:  # BR
            return (rows - 1 - r_idx, cols - 1 - c_idx)

    def _corner_changed(self):
        new_corner = self.corner_var.get()
        if new_corner == self._corner:
            return
        try:
            rows = max(1, int(self.rows_var.get()))
            cols = max(1, int(self.cols_var.get()))
        except (tk.TclError, ValueError):
            return

        for pi, old_seats in enumerate(self.panel_seats):
            pos_to_jid = {
                self._seat_pos(sn, rows, cols, self._corner): jid
                for sn, jid in old_seats.items()
                if jid is not None
            }
            new_seats = {i: None for i in range(1, rows * cols + 1)}
            for (r, c), jid in pos_to_jid.items():
                new_sn = self._seat_num(r, c, rows, cols, new_corner)
                new_seats[new_sn] = jid
                j = self.jurors.get(jid)
                if j:
                    j.seat = new_sn
            self.panel_seats[pi] = new_seats

        self._corner = new_corner
        self._refresh()

    # ── Layout management ─────────────────────────────────────────────────────

    def _init_layout(self, rows: int = 4, cols: int = 7):
        self.rows_var.set(rows)
        self.cols_var.set(cols)
        n = SETTINGS.get("num_panels", 3)
        self.panel_seats  = [{i: None for i in range(1, rows * cols + 1)} for _ in range(n)]
        self._active_panel = 0
        self.final_jury   = []
        self._update_panel_tabs()
        self._refresh()

    def _layout_changed(self, _=None):
        try:
            rows = max(1, int(self.rows_var.get()))
            cols = max(1, int(self.cols_var.get()))
        except (tk.TclError, ValueError):
            return

        for pi, old_seats in enumerate(self.panel_seats):
            for jid in old_seats.values():
                if jid is not None:
                    j = self.jurors.get(jid)
                    if j:
                        j.seat, j.is_alt, j.status, j.panel = None, False, "pool", 0

            new_seats = {i: None for i in range(1, rows * cols + 1)}
            for s, jid in old_seats.items():
                if jid and s in new_seats:
                    j = self.jurors[jid]
                    new_seats[s] = jid
                    j.seat, j.is_alt, j.status, j.panel = s, False, "seated", pi
            self.panel_seats[pi] = new_seats

        self.final_jury = [jid for jid in self.final_jury if jid in self.jurors]
        self._refresh()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _redraw(self):
        if not self._redraw_pending:
            self._redraw_pending = True
            self.after_idle(self._do_redraw)

    def _do_redraw(self):
        self._redraw_pending = False
        self._seat_geo = None
        self.canvas.delete("all")
        try:
            rows = max(1, int(self.rows_var.get()))
            cols = max(1, int(self.cols_var.get()))
        except (tk.TclError, ValueError):
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10:
            return

        pad = 40
        zoom = getattr(self, "_temp_zoom", None)
        if zoom is None:
            zoom_var = getattr(self, "_zoom_var", None)
            zoom = zoom_var.get() if zoom_var else 1.0
        scale = min(1.0,
                    (cw - pad) / (cols * SW + (cols - 1) * SGAP),
                    (ch - pad) / (rows * SH + (rows - 1) * SGAP))
        scale = max(0.1, scale * zoom)
        sw   = max(50, int(SW   * scale))
        sh   = max(36, int(SH   * scale))
        sgap = max(4,  int(SGAP * scale))

        gw = cols * sw + (cols - 1) * sgap
        gh = rows * sh + (rows - 1) * sgap
        ox = (cw - gw) // 2
        oy = max(10, (ch - gh) // 2)

        # Dark-gray backdrop: fills gaps between seats and draws outer grid border
        bdr = sgap
        self.canvas.create_rectangle(ox - bdr, oy - bdr, ox + gw + bdr, oy + gh + bdr,
                                     fill=C["border"], outline=C["border"], width=1,
                                     tags=("grid_bg",))

        # Precompute per-draw constants shared across all seats
        fscale    = SETTINGS["seat_font_size"] / 10.0
        f_sm      = max(6, int(8  * scale * fscale))
        f_md      = max(7, int(11 * scale * fscale))
        f_empty   = max(6, int(9  * scale * fscale))
        spad      = max(3, int(7  * scale))
        js        = max(1, int(self.jury_size_var.get()))
        fj_pos    = {jid: pos for pos, jid in enumerate(self.final_jury, 1)}

        xywh: dict[int, tuple] = {}
        for r in range(rows):
            for c in range(cols):
                sn = self._seat_num(r, c, rows, cols, self._corner)
                x  = ox + c * (sw + sgap)
                y  = oy + r * (sh + sgap)
                xywh[sn] = (x, y)
                self._draw_seat(sn, x, y, sw, sh, scale,
                                f_sm, f_md, f_empty, spad, js, fj_pos)

        self._seat_geo = dict(sw=sw, sh=sh, sgap=sgap, ox=ox, oy=oy,
                              rows=rows, cols=cols, scale=scale,
                              f_sm=f_sm, f_md=f_md, f_empty=f_empty,
                              spad=spad, js=js, fj_pos=fj_pos, xywh=xywh)

    def _draw_seat(self, num: int, x: int, y: int, sw: int, sh: int, scale: float,
                   f_sm: int, f_md: int, f_empty: int, spad: int, js: int,
                   fj_pos: dict):
        jid   = self.seats.get(num)
        juror = self.jurors.get(jid) if jid else None
        tag   = f"seat_{num}"
        hover = self._hovered == (False, num)

        if juror:
            final_pos = fj_pos.get(jid, 0)
            if final_pos and final_pos <= js:
                fill = C["seat_final"]
            elif final_pos:
                fill = C["seat_alt_fin"]
            else:
                fill = {
                    "seated":    C["seat_seated"],
                    "excused":   C["seat_excused"],
                    "struck_def": C["seat_struck"],
                    "struck_pro": C["seat_struck"],
                }.get(juror.status, C["seat_seated"])
            tc = C["txt_light"]
        else:
            fill = C["seat_hover"] if hover else C["seat_empty"]
            tc   = C["txt_light"]
            final_pos = 0

        selected = (jid is not None and jid == self._selected_jid)
        self._rrect(x, y, x + sw, y + sh, max(3, int(7 * scale)),
                    fill=fill,
                    outline="#ffffff" if selected else C["border"],
                    width=3 if selected else 1,
                    tags=(tag, "seats"))

        self.canvas.create_text(x + spad, y + spad, anchor="nw",
                                text=str(num),
                                font=("Helvetica", f_sm), fill=tc, tags=(tag,))

        if juror:
            self.canvas.create_text(x + sw - spad, y + spad, anchor="ne",
                                    text=f"Juror #{juror.id}",
                                    font=("Helvetica", f_sm), fill=tc, tags=(tag,))

            self.canvas.create_text(x + sw // 2, y + int(sh * 0.36), anchor="center",
                                    text=juror.name,
                                    width=sw - spad * 2 - 4,
                                    font=("Helvetica", f_md, "bold"),
                                    fill=tc, tags=(tag,))

            if juror.age:
                self.canvas.create_text(x + sw // 2, y + int(sh * 0.64), anchor="center",
                                        text=f"Age {juror.age}",
                                        font=("Helvetica", f_sm),
                                        fill=tc, tags=(tag,))

            if final_pos and final_pos <= js:
                bottom = f"Final Juror #{final_pos}"
            elif final_pos:
                bottom = f"Alt #{final_pos - js}"
            elif juror.status in STATUS_DISPLAY:
                bottom = f"({STATUS_DISPLAY[juror.status]})"
            elif juror.keywords:
                kw = juror.keywords if len(juror.keywords) <= 20 else juror.keywords[:18] + "…"
                bottom = kw
            else:
                bottom = None
            if bottom:
                self.canvas.create_text(x + sw // 2, y + sh - spad - 2, anchor="center",
                                        text=bottom,
                                        font=("Helvetica", f_sm, "italic"),
                                        fill=tc, tags=(tag,))

            if juror.rating != 0:
                r_sym = ("▲" if juror.rating > 0 else "▼") * abs(juror.rating)
                r_col = "#5adc8a" if juror.rating > 0 else "#ff7070"
                self.canvas.create_text(x + sw - spad, y + spad + f_sm + 2, anchor="ne",
                                        text=r_sym, font=("Helvetica", f_sm, "bold"),
                                        fill=r_col, tags=(tag,))
        else:
            self.canvas.create_text(x + sw // 2, y + sh // 2, anchor="center",
                                    text="empty",
                                    font=("Helvetica", f_empty, "italic"),
                                    fill=C["seat_empty_txt"], tags=(tag,))

    def _rrect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1+r, y1,  x2-r, y1,  x2, y1,  x2, y1+r,
               x2, y2-r,  x2, y2,  x2-r, y2,  x1+r, y2,
               x1, y2,  x1, y2-r,  x1, y1+r,  x1, y1]
        return self.canvas.create_polygon(pts, smooth=True, **kw)

    # ── Pool list ─────────────────────────────────────────────────────────────

    def _refresh_pool(self):
        pool, excused, def_struck, pro_struck = [], [], [], []
        for j in sorted(self.jurors.values(), key=lambda j: j.id):
            s = j.status
            if s == "pool":
                pool.append(j)
            elif s == "excused":
                excused.append(j)
            elif s == "struck_def":
                def_struck.append(j)
            elif s == "struck_pro":
                pro_struck.append(j)

        self._pool_ids        = [j.id for j in pool]
        self._excused_ids     = [j.id for j in excused]
        self._def_struck_ids  = [j.id for j in def_struck]
        self._pro_struck_ids  = [j.id for j in pro_struck]

        self.pool_lb.delete(0, "end")
        if pool:
            self.pool_lb.insert("end", *[j.label for j in pool])

        self.excused_lb.delete(0, "end")
        if excused:
            self.excused_lb.insert("end", *[j.label for j in excused])

        self.def_struck_lb.delete(0, "end")
        if def_struck:
            self.def_struck_lb.insert("end", *[j.label for j in def_struck])

        self.pro_struck_lb.delete(0, "end")
        if pro_struck:
            self.pro_struck_lb.insert("end", *[j.label for j in pro_struck])

    def _refresh(self):
        self._refresh_pool()
        self._refresh_final_jury()
        self._redraw()

    def _refresh_final_jury(self):
        self.final_lb.delete(0, "end")
        self._final_lb_ids = []
        self._fj_pos = {}
        js = max(1, int(self.jury_size_var.get()))
        labels = []
        colors = []
        for pos, jid in enumerate(self.final_jury, 1):
            j = self.jurors.get(jid)
            if not j:
                continue
            self._fj_pos[jid] = pos
            if pos <= js:
                labels.append(f"{pos}.  #{j.id} {j.name}")
                colors.append(C["seat_final"])
            else:
                labels.append(f"Alt {pos - js}.  #{j.id} {j.name}")
                colors.append(C["seat_alt_fin"])
            self._final_lb_ids.append(jid)

        if labels:
            self.final_lb.insert("end", *labels)
            for i, fg in enumerate(colors):
                self.final_lb.itemconfig(i, fg=fg)

        if self._selected_final_jid in self._final_lb_ids:
            idx = self._final_lb_ids.index(self._selected_final_jid)
            self.final_lb.selection_set(idx)
            j = self.jurors.get(self._selected_final_jid)
            if j:
                self._show_fj_detail(j)
        else:
            self._selected_final_jid = None
            self._clear_fj_detail()

    def _toggle_final(self, jid: int):
        if jid in self.final_jury:
            self.final_jury.remove(jid)
        else:
            self.final_jury.append(jid)
            j = self.jurors.get(jid)
            if j and j.status in ("excused", "struck_def", "struck_pro"):
                j.status = "seated"
        self._refresh()

    def _pool_juror(self, idx: int) -> Juror | None:
        if 0 <= idx < len(self._pool_ids):
            return self.jurors.get(self._pool_ids[idx])
        return None

    # ── Pool right-click ──────────────────────────────────────────────────────

    def _pool_rclick(self, event):
        idx = self.pool_lb.nearest(event.y)
        if idx < 0:
            return
        self.pool_lb.selection_clear(0, "end")
        self.pool_lb.selection_set(idx)
        j = self._pool_juror(idx)
        if j is None:
            return
        rating_sym = ("▲" * j.rating if j.rating > 0
                      else "▼" * abs(j.rating) if j.rating < 0 else "")
        header = f"{j.name}  {rating_sym}" if rating_sym else j.name
        m = tk.Menu(self, tearoff=0)
        m.add_command(label=header, state="disabled", font=FONTS["md_bold"])
        m.add_separator()
        m.add_cascade(label="Priority", menu=self._priority_submenu(m, j.id))
        m.add_separator()
        m.add_command(label="Excuse  (for cause)",
                      command=lambda: self._dismiss_pool_juror(j.id, "excused"))
        m.add_command(label="Strike — Defense",
                      command=lambda: self._dismiss_pool_juror(j.id, "struck_def"))
        m.add_command(label="Strike — Prosecution",
                      command=lambda: self._dismiss_pool_juror(j.id, "struck_pro"))
        m.add_separator()
        m.add_command(label="Edit…", command=lambda: self._edit_by_id(j.id))
        m.post(event.x_root, event.y_root)

    def _dismiss_pool_juror(self, jid: int, status: str):
        j = self.jurors.get(jid)
        if j:
            j.status = status
            self.status.set(f"{j.name} {status}.")
        self._refresh_pool()

    def _dismissed_rclick(self, event):
        lb = event.widget
        idx = lb.nearest(event.y)
        if idx < 0:
            return
        lb.selection_clear(0, "end")
        lb.selection_set(idx)
        if lb is self.def_struck_lb:
            id_list = self._def_struck_ids
        elif lb is self.pro_struck_lb:
            id_list = self._pro_struck_ids
        else:
            id_list = self._excused_ids
        if idx >= len(id_list):
            return
        j = self.jurors.get(id_list[idx])
        if j is None:
            return
        restore_label = "Return to Seat" if j.seat is not None else "Return to Pool"
        m = tk.Menu(self, tearoff=0)
        m.add_command(label=j.name, state="disabled", font=FONTS["md_bold"])
        m.add_separator()
        m.add_command(label=restore_label,
                      command=lambda: self._return_dismissed(j.id))
        m.add_command(label="Edit…", command=lambda: self._edit_by_id(j.id))
        m.post(event.x_root, event.y_root)

    def _final_rclick(self, event):
        idx = self.final_lb.nearest(event.y)
        if idx < 0 or idx >= len(self._final_lb_ids):
            return
        self.final_lb.selection_clear(0, "end")
        self.final_lb.selection_set(idx)
        jid = self._final_lb_ids[idx]
        j = self.jurors.get(jid)
        if j is None:
            return
        self._selected_final_jid = jid
        self._show_fj_detail(j)
        m = tk.Menu(self, tearoff=0)
        m.add_command(label=j.name, state="disabled", font=FONTS["md_bold"])
        m.add_separator()
        m.add_command(label="Edit…", command=lambda: self._edit_by_id(jid))
        m.add_separator()
        m.add_command(label="Return to Seat",
                      command=lambda: self._toggle_final(jid))
        m.post(event.x_root, event.y_root)

    def _return_dismissed(self, jid: int):
        j = self.jurors.get(jid)
        if not j:
            return
        if j.seat is not None:
            j.status = "seated"
            self.status.set(f"{j.name} returned to seat {j.seat}.")
        else:
            j.status = "pool"
            self.status.set(f"{j.name} returned to pool.")
        self._refresh()

    # ── Drag from pool ────────────────────────────────────────────────────────

    def _lb_press(self, event):
        idx = self.pool_lb.nearest(event.y)
        self.pool_lb.selection_clear(0, "end")
        self.pool_lb.selection_set(idx)
        j = self._pool_juror(idx)
        self._drag_id     = j.id    if j else None
        self._drag_text   = j.label if j else ""
        self._drag_source = "pool"

    def _lb_drag(self, event):
        if self._drag_id is None:
            return
        rx = self.pool_lb.winfo_rootx() + event.x
        ry = self.pool_lb.winfo_rooty() + event.y
        if self._drag_win is None:
            self._drag_win = tk.Toplevel(self)
            self._drag_win.overrideredirect(True)
            self._drag_win.attributes("-alpha", 0.80)
            tk.Label(self._drag_win, text=self._drag_text,
                     bg=C["seat_seated"], fg="white",
                     font=FONTS["md_bold"],
                     padx=10, pady=5, relief="raised").pack()
        self._drag_win.geometry(f"+{rx + 14}+{ry + 4}")

    def _lb_release(self, event):
        self._kill_drag_win()
        if self._drag_id is None or self._drag_source != "pool":
            return
        rx = self.pool_lb.winfo_rootx() + event.x
        ry = self.pool_lb.winfo_rooty() + event.y
        cx, cy = self.canvas.winfo_rootx(), self.canvas.winfo_rooty()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cx <= rx < cx + cw and cy <= ry < cy + ch:
            self._assign(rx - cx, ry - cy)
        elif self._widget_contains(self.final_lb, rx, ry):
            self._toggle_final(self._drag_id)
        self._drag_id     = None
        self._drag_source = None

    def _kill_drag_win(self):
        if self._drag_win:
            self._drag_win.destroy()
            self._drag_win = None

    # ── Canvas press / seat drag ──────────────────────────────────────────────

    def _defocus_detail(self, event: tk.Event):
        rte = self._det_notes_text
        if (event.widget is not self._det_kw_entry and
                not rte.contains_widget(event.widget)):
            focused = self.focus_get()
            if focused is self._det_kw_entry or rte.contains_widget(focused):
                self.focus_set()

    def _cv_press(self, event):
        info = self._seat_at(event.x, event.y)
        if not info:
            self._save_detail()
            if self._selected_jid is not None:
                self._selected_jid = None
                self._clear_detail()
                self._redraw()
            return
        _, num = info
        jid = self.seats.get(num)
        if jid is None:
            self._save_detail()
            if self._selected_jid is not None:
                self._selected_jid = None
                self._clear_detail()
                self._redraw()
            return
        self._save_detail(redraw=False)  # save old selection; redraw happens below
        j = self.jurors[jid]
        self._selected_jid = jid
        self._show_juror_detail(j, seat_label=f"Panel {self._active_panel + 1}  ·  Seat {num}")
        self._drag_id        = jid
        self._drag_text      = j.label
        self._drag_source    = "seat"
        self._drag_seat_info = (False, num)
        self._redraw()

    def _cv_seat_drag(self, event):
        if self._drag_id is None or self._drag_source != "seat":
            return
        rx = self.canvas.winfo_rootx() + event.x
        ry = self.canvas.winfo_rooty() + event.y
        if self._drag_win is None:
            self._drag_win = tk.Toplevel(self)
            self._drag_win.overrideredirect(True)
            self._drag_win.attributes("-alpha", 0.80)
            tk.Label(self._drag_win, text=self._drag_text,
                     bg=C["seat_seated"], fg="white",
                     font=FONTS["md_bold"],
                     padx=10, pady=5, relief="raised").pack()
        self._drag_win.geometry(f"+{rx + 14}+{ry + 4}")

    def _vacate_seat(self, num: int):
        jid = self.seats.get(num)
        if jid is not None:
            j = self.jurors.get(jid)
            if j:
                j.seat, j.is_alt, j.panel = None, False, 0
            self.seats[num] = None
            if jid in self.final_jury:
                self.final_jury.remove(jid)

    def _widget_contains(self, widget: tk.Widget, rx: int, ry: int) -> bool:
        wx, wy = widget.winfo_rootx(), widget.winfo_rooty()
        return wx <= rx < wx + widget.winfo_width() and wy <= ry < wy + widget.winfo_height()

    # ── Canvas events ─────────────────────────────────────────────────────────

    def _cv_drop(self, event):
        if self._drag_id is None:
            return

        was_dragging = self._drag_win is not None
        self._kill_drag_win()

        if self._drag_source == "seat":
            if was_dragging:
                self._handle_seat_drop(event)
            else:
                self._drag_id = None
                self._drag_source = None
                self._drag_seat_info = None
        else:
            # Pool → canvas
            self._assign(event.x, event.y)
            self._drag_id = None

    def _handle_seat_drop(self, event):
        jid              = self._drag_id
        _, src_num       = self._drag_seat_info
        self._drag_id    = None
        self._drag_source = None

        rx = self.canvas.winfo_rootx() + event.x
        ry = self.canvas.winfo_rooty() + event.y

        # Drop on another seat?
        target = self._seat_at(event.x, event.y)
        if target and target != (False, src_num):
            _, dst_num = target
            dst_jid = self.seats.get(dst_num)
            if dst_jid is not None:
                # Both seats occupied — swap them
                src_j = self.jurors[jid]
                dst_j = self.jurors[dst_jid]
                self.seats[src_num] = dst_jid
                self.seats[dst_num] = jid
                src_j.seat, src_j.panel = dst_num, self._active_panel
                dst_j.seat, dst_j.panel = src_num, self._active_panel
                self._drag_seat_info = None
                self._refresh()
            else:
                # Target empty — move normally
                self._vacate_seat(src_num)
                self._drag_id = jid
                self._assign(event.x, event.y)
                self._drag_id = None
            return

        # Drop on pool?
        if self._widget_contains(self.pool_lb, rx, ry):
            self._vacate_seat(src_num)
            j = self.jurors.get(jid)
            if j:
                j.status = "pool"
            self._refresh()
            return

        # Drop on final jury?
        if self._widget_contains(self.final_lb, rx, ry):
            self._toggle_final(jid)
            self._drag_seat_info = None
            return

        # Dropped nowhere useful — leave juror in place

    def _cv_motion(self, event):
        if self._drag_source == "seat":
            return
        info = self._seat_at(event.x, event.y)
        if info != self._hovered:
            old = self._hovered
            self._hovered = info
            if old:
                self._redraw_seat(old[1])
            if info:
                self._redraw_seat(info[1])

    def _cv_leave(self, _=None):
        if self._hovered:
            old = self._hovered
            self._hovered = None
            self._redraw_seat(old[1])

    def _clear_detail(self):
        self._det_name.set("")
        self._det_kw_entry.config(state="normal")
        self._det_kw_entry.delete(0, "end")
        self._det_kw_entry.config(state="readonly")
        self._det_notes_text._text.config(state="normal")
        self._det_notes_text.set_runs([])
        self._det_notes_text._text.config(state="disabled")
        self._det_notes_loaded = ""
        self._update_rating_buttons(0)

    def _save_detail(self, *, redraw: bool = True):
        if self._selected_jid is None:
            return
        j = self.jurors.get(self._selected_jid)
        if not j:
            return
        new_kw = self._det_kw_entry.get().strip()
        runs   = self._det_notes_text.get_runs()
        if runs and any(k in r for r in runs
                        for k in ("bold", "italic", "underline", "font")):
            new_notes = json.dumps(runs, ensure_ascii=False)
        elif runs:
            new_notes = "".join(r.get("text", "") for r in runs).strip()
        else:
            new_notes = ""
        changed = (new_kw != j.keywords or new_notes != self._det_notes_loaded)
        j.keywords = new_kw
        j.notes    = new_notes
        self._det_notes_loaded = new_notes
        if changed and self._selected_final_jid == self._selected_jid:
            self._fj_det_kw_entry.config(state="normal")
            self._fj_det_kw_entry.delete(0, "end")
            self._fj_det_kw_entry.insert(0, j.keywords)
            self._fj_det_kw_entry.config(state="readonly")
            self._fj_det_notes_text.config(state="normal")
            _load_rich_into_text(self._fj_det_notes_text, j.notes)
            self._fj_det_notes_text.config(state="disabled")
        if redraw and changed:
            self._redraw()

    def _set_rating(self, value: int):
        if self._selected_jid is None:
            return
        j = self.jurors.get(self._selected_jid)
        if not j:
            return
        j.rating = 0 if j.rating == value else value
        self._update_rating_buttons(j.rating)
        self._redraw()

    def _apply_rating(self, jid: int, value: int):
        j = self.jurors.get(jid)
        if not j:
            return
        j.rating = value
        if self._selected_jid == jid:
            self._update_rating_buttons(value)
        self._redraw()

    def _priority_submenu(self, parent: tk.Menu, jid: int) -> tk.Menu:
        cur = (self.jurors[jid].rating if jid in self.jurors else 0)
        sub = tk.Menu(parent, tearoff=0)
        for val, sym, desc in [(3, "▲▲▲", "Strongly favor"),
                                (2, "▲▲",  "Favor"),
                                (1, "▲",   "Lean favor")]:
            mark = "●  " if cur == val else "    "
            sub.add_command(label=f"{mark}{sym}  {desc}",
                            command=lambda v=val: self._apply_rating(jid, v))
        sub.add_separator()
        sub.add_command(label=("●  " if cur == 0 else "    ") + "Clear",
                        command=lambda: self._apply_rating(jid, 0))
        sub.add_separator()
        for val, sym, desc in [(-1, "▼",   "Lean against"),
                                (-2, "▼▼",  "Against"),
                                (-3, "▼▼▼", "Strongly against")]:
            mark = "●  " if cur == val else "    "
            sub.add_command(label=f"{mark}{sym}  {desc}",
                            command=lambda v=val: self._apply_rating(jid, v))
        return sub

    def _update_rating_buttons(self, rating: int):
        btns = getattr(self, "_rating_btns", {})
        for val, btn in btns.items():
            active = (val == rating)
            if active and val > 0:
                btn.configure(bg=C["seat_final"],  fg=C["txt_light"])
            elif active and val < 0:
                btn.configure(bg=C["seat_struck"], fg=C["txt_light"])
            else:
                btn.configure(bg=C["btn_bg"], fg=C["btn_fg"])

    def _show_juror_detail(self, j: Juror, seat_label: str = ""):
        parts = []
        if seat_label:
            parts.append(seat_label)
        elif j.seat is not None:
            parts.append(f"Panel {j.panel + 1}  ·  Seat {j.seat}")
        id_part = f"Juror #{j.id}  {j.name}"
        if j.age:
            id_part += f"  ·  Age {j.age}"
        parts.append(id_part)
        if j.status not in ("pool", "seated"):
            parts.append(STATUS_DISPLAY.get(j.status, j.status.capitalize()))
        self._det_name.set("  —  ".join(parts))
        self._det_kw_entry.config(state="normal")
        self._det_kw_entry.delete(0, "end")
        self._det_kw_entry.insert(0, j.keywords)
        self._det_notes_text._text.config(state="normal")
        self._det_notes_text.set_runs(_notes_to_runs(j.notes))
        self._det_notes_loaded = j.notes
        self._update_rating_buttons(j.rating)

    def _fj_nav(self, delta: int):
        n = self.final_lb.size()
        if n == 0:
            return
        sel = self.final_lb.curselection()
        idx = (sel[0] + delta) if sel else (0 if delta > 0 else n - 1)
        idx = max(0, min(n - 1, idx))
        self.final_lb.selection_clear(0, "end")
        self.final_lb.selection_set(idx)
        self.final_lb.see(idx)
        self._fj_lb_selection_changed()

    def _fj_lb_selection_changed(self, _event=None):
        sel = self.final_lb.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._final_lb_ids):
            return
        jid = self._final_lb_ids[idx]
        j = self.jurors.get(jid)
        if not j:
            return
        self._save_detail(redraw=False)
        self._selected_final_jid = jid
        self._show_fj_detail(j)

    def _show_fj_detail(self, j: Juror):
        js = max(1, int(self.jury_size_var.get()))
        pos = self._fj_pos.get(j.id, 0)
        parts = []
        if pos and pos <= js:
            parts.append(f"Final #{pos}")
        elif pos:
            parts.append(f"Alt #{pos - js}")
        id_part = f"#{j.id}  {j.name}"
        if j.age:
            id_part += f"  ·  Age {j.age}"
        parts.append(id_part)
        self._fj_det_name.set("  —  ".join(parts))
        self._fj_det_kw_entry.config(state="normal")
        self._fj_det_kw_entry.delete(0, "end")
        self._fj_det_kw_entry.insert(0, j.keywords)
        self._fj_det_kw_entry.config(state="readonly")
        self._fj_det_notes_text.config(state="normal")
        _load_rich_into_text(self._fj_det_notes_text, j.notes)
        self._fj_det_notes_text.config(state="disabled")

    def _clear_fj_detail(self):
        self._fj_det_name.set("")
        self._fj_det_kw_entry.config(state="normal")
        self._fj_det_kw_entry.delete(0, "end")
        self._fj_det_kw_entry.config(state="readonly")
        self._fj_det_notes_text.config(state="normal")
        _load_rich_into_text(self._fj_det_notes_text, "")
        self._fj_det_notes_text.config(state="disabled")

    def _lb_selection_changed(self, event):
        lb = event.widget
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        if lb is self.pool_lb:
            j = self._pool_juror(idx)
        elif lb is self.excused_lb:
            j = self.jurors.get(self._excused_ids[idx]) if idx < len(self._excused_ids) else None
        elif lb is self.def_struck_lb:
            j = self.jurors.get(self._def_struck_ids[idx]) if idx < len(self._def_struck_ids) else None
        elif lb is self.pro_struck_lb:
            j = self.jurors.get(self._pro_struck_ids[idx]) if idx < len(self._pro_struck_ids) else None
        else:
            return
        if j:
            self._save_detail(redraw=False)
            self._selected_jid = j.id
            self._show_juror_detail(j)

    def _cv_rclick(self, event):
        info = self._seat_at(event.x, event.y)
        if not info:
            return
        _, num = info
        jid = self.seats.get(num)
        if jid is None:
            return
        j = self.jurors[jid]
        in_final = jid in self._fj_pos

        rating_sym = ("▲" * j.rating if j.rating > 0
                      else "▼" * abs(j.rating) if j.rating < 0 else "")
        header = f"{j.name}  {rating_sym}" if rating_sym else j.name
        m = tk.Menu(self, tearoff=0)
        m.add_command(label=header, state="disabled",
                      font=FONTS["md_bold"])
        m.add_separator()
        m.add_cascade(label="Priority", menu=self._priority_submenu(m, jid))
        m.add_separator()
        m.add_command(
            label="Remove from Final Jury" if in_final else "Add to Final Jury",
            command=lambda: self._toggle_final(jid),
        )
        dismissed = j.status in ("excused", "struck_def", "struck_pro")
        m.add_separator()
        if dismissed:
            m.add_command(label="Return to Seat",
                          command=lambda: self._return_dismissed(jid))
        else:
            m.add_command(label="Return to Pool",
                          command=lambda: self._return_to_pool(jid, num))
        m.add_command(label="Excuse  (for cause)",
                      state="disabled" if j.status == "excused" else "normal",
                      command=lambda: self._set_status(jid, "excused"))
        m.add_command(label="Strike — Defense",
                      state="disabled" if j.status == "struck_def" else "normal",
                      command=lambda: self._set_status(jid, "struck_def"))
        m.add_command(label="Strike — Prosecution",
                      state="disabled" if j.status == "struck_pro" else "normal",
                      command=lambda: self._set_status(jid, "struck_pro"))
        m.add_separator()
        m.add_command(label="Edit Notes…",
                      command=lambda: self._edit_by_id(jid))
        m.post(event.x_root, event.y_root)

    # ── Seat helpers ──────────────────────────────────────────────────────────

    def _seat_at(self, x: int, y: int) -> tuple | None:
        g = self._seat_geo
        if g is None:
            return None
        cx = x - g['ox']
        cy = y - g['oy']
        if cx < 0 or cy < 0:
            return None
        sw_g = g['sw'] + g['sgap']
        sh_g = g['sh'] + g['sgap']
        col = cx // sw_g
        row = cy // sh_g
        if col >= g['cols'] or row >= g['rows']:
            return None
        if cx % sw_g >= g['sw'] or cy % sh_g >= g['sh']:
            return None  # click landed in the gap between seats
        sn = self._seat_num(row, col, g['rows'], g['cols'], self._corner)
        return (False, sn)

    def _redraw_seat(self, sn: int):
        g = self._seat_geo
        if g is None or sn not in g['xywh']:
            return
        self.canvas.delete(f"seat_{sn}")
        x, y = g['xywh'][sn]
        self._draw_seat(sn, x, y, g['sw'], g['sh'], g['scale'],
                        g['f_sm'], g['f_md'], g['f_empty'], g['spad'],
                        g['js'], g['fj_pos'])

    def _assign(self, cx: int, cy: int):
        info = self._seat_at(cx, cy)
        if not info or self._drag_id is None:
            return
        _, num = info

        old_jid = self.seats.get(num)
        if old_jid is not None:
            oj = self.jurors.get(old_jid)
            if oj:
                oj.seat, oj.is_alt = None, False
                if oj.status not in ("excused", "struck_def", "struck_pro", "struck"):
                    oj.status = "pool"

        j              = self.jurors[self._drag_id]
        self.seats[num] = self._drag_id
        j.seat, j.is_alt, j.status, j.panel = num, False, "seated", self._active_panel
        self.status.set(f"Seated {j.name} in seat {num}.")
        self._selected_jid = self._drag_id
        self._show_juror_detail(j, seat_label=f"Panel {self._active_panel + 1}  ·  Seat {num}")
        self._refresh()

    def _return_to_pool(self, jid: int, num: int):
        self.seats[num] = None
        j = self.jurors.get(jid)
        if j:
            j.seat, j.is_alt, j.status, j.panel = None, False, "pool", 0
        if jid in self.final_jury:
            self.final_jury.remove(jid)
        self._refresh()

    def _set_status(self, jid: int, status: str):
        j = self.jurors.get(jid)
        if not j:
            return
        if jid in self.final_jury:
            self.final_jury.remove(jid)
        j.status = status
        self.status.set(f"{j.name} marked {status}.")
        self._refresh()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _upload_csv(self):
        path = filedialog.askopenfilename(
            title="Select Juror CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=self._work_dir(),
        )
        if not path:
            return

        def parse_dob(raw):
            for fmt in DATE_FMTS:
                try:
                    return datetime.strptime(raw.strip(), fmt).date()
                except ValueError:
                    pass
            return None

        def calc_age(dob):
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))
        except Exception as e:
            messagebox.showerror("CSV Error", f"Could not read file:\n{e}")
            return

        if not rows:
            messagebox.showerror("CSV Error", "The file is empty.")
            return

        # Auto-detect header: skip first row if its second cell isn't a valid date
        start = 0
        if len(rows[0]) >= 2 and parse_dob(rows[0][1]) is None:
            start = 1

        errors, added = [], 0
        for i, row in enumerate(rows[start:], start + 1):
            if not row or not any(c.strip() for c in row):
                continue
            if len(row) < 2:
                errors.append(f"Row {i}: expected at least 2 columns (name, DOB)")
                continue
            name = row[0].strip()
            dob_raw = row[1].strip()
            if not name:
                errors.append(f"Row {i}: name is empty")
                continue
            dob = parse_dob(dob_raw)
            if dob is None:
                errors.append(f"Row {i}: unrecognized date \"{dob_raw}\"")
                continue
            j = Juror(name, str(calc_age(dob)))
            self.jurors[j.id] = j
            added += 1

        self._refresh()

        if errors:
            preview = "\n".join(errors[:10])
            if len(errors) > 10:
                preview += f"\n…and {len(errors) - 10} more"
            messagebox.showwarning(
                "CSV Import",
                f"Added {added} juror(s) to the pool.\n\nRows with issues:\n{preview}",
            )
        else:
            messagebox.showinfo("CSV Import", f"Added {added} juror(s) to the pool.")

    def _auto_seat(self):
        pool_jids = [jid for jid in self._pool_ids
                     if self.jurors.get(jid) and self.jurors[jid].status == "pool"]
        empty_seats = sorted(sn for sn, jid in self.seats.items() if jid is None)

        if not pool_jids:
            messagebox.showinfo("Auto Seat", "No jurors in the preliminary pool.")
            return
        if not empty_seats:
            messagebox.showinfo("Auto Seat", "No empty seats available.")
            return

        for jid, seat_num in zip(pool_jids, empty_seats):
            j = self.jurors[jid]
            j.seat, j.status, j.panel = seat_num, "seated", self._active_panel
            self.seats[seat_num] = jid

        seated = min(len(pool_jids), len(empty_seats))
        self._refresh()
        self.status.set(f"Auto-seated {seated} juror(s).")

    def _add(self):
        dlg = JurorDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            j = Juror(dlg.out_name, dlg.out_age, dlg.out_notes, dlg.out_keywords)
            self.jurors[j.id] = j
            self._refresh_pool()
            self.status.set(f"Added {j.name}.")

    def _edit_selected(self, _=None):
        sel = self.pool_lb.curselection()
        if not sel:
            return
        j = self._pool_juror(sel[0])
        if j:
            self._edit_by_id(j.id)

    def _edit_by_id(self, jid: int):
        j = self.jurors.get(jid)
        if not j:
            return
        dlg = JurorDialog(self, j)
        self.wait_window(dlg)
        if dlg.result:
            j.name, j.age, j.notes, j.keywords = dlg.out_name, dlg.out_age, dlg.out_notes, dlg.out_keywords
            self._refresh()

    def _remove(self):
        sel = self.pool_lb.curselection()
        if not sel:
            messagebox.showinfo("Remove", "Select a juror in the pool first.")
            return
        j = self._pool_juror(sel[0])
        if j and messagebox.askyesno("Remove", f"Remove {j.name} from this case?"):
            del self.jurors[j.id]
            self._refresh_pool()

    # ── File I/O ──────────────────────────────────────────────────────────────

    def _test_populate(self):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "test_populate", _resource_path("test_populate.py")
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.populate(self)
        except FileNotFoundError:
            messagebox.showerror("Test Data", "test_populate.py not found.")
        except Exception as e:
            messagebox.showerror("Test Data Error", str(e))

    def _new(self):
        if messagebox.askyesno(
            "Reset",
            "Reset to default?\n\nAll unsaved data will be permanently lost.",
            icon="warning",
        ):
            self.jurors.clear()
            Juror._next = 1
            self._selected_jid = None
            self._clear_detail()
            self._selected_final_jid = None
            self._clear_fj_detail()
            self._init_layout(int(self.rows_var.get()), int(self.cols_var.get()))

    def _export_pdf(self):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                Table, TableStyle, HRFlowable, KeepTogether,
            )
            from reportlab.lib.enums import TA_CENTER
        except ImportError:
            messagebox.showerror(
                "Missing Library",
                "PDF export requires the 'reportlab' package.\n\n"
                "Install it with:  pip install reportlab\n\nThen restart.",
            )
            return

        from tkinter.simpledialog import askstring

        report_title = askstring(
            "Report Title",
            "Enter a title for this report:",
            initialvalue="Jury Selection Report",
            parent=self,
        )
        if report_title is None:
            return
        report_title = report_title.strip() or "Jury Selection Report"

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialdir=self._work_dir(),
            initialfile="jury_report.pdf",
        )
        if not path:
            return

        rows_n = max(1, int(self.rows_var.get()))
        cols_n = max(1, int(self.cols_var.get()))

        # ── Colours ──────────────────────────────────────────────────────────
        BLUE   = colors.HexColor("#2d6dce")
        GREEN  = colors.HexColor("#2e7d4f")
        AGREEN = colors.HexColor("#6aab82")
        GREY   = colors.HexColor("#909090")
        RED    = colors.HexColor("#cc4444")
        DARK   = colors.HexColor("#111111")
        MID    = colors.HexColor("#555555")
        LIGHT  = colors.HexColor("#aaaaaa")
        BKGD   = colors.HexColor("#f2f3f7")
        DIV    = colors.HexColor("#c4cad8")

        # ── Paragraph styles ─────────────────────────────────────────────────
        _sss = getSampleStyleSheet()
        def ps(name, **kw):
            return ParagraphStyle(name, parent=_sss['Normal'], **kw)

        s_title  = ps('t',  fontName='Helvetica-Bold', fontSize=20, textColor=DARK,
                      spaceAfter=10, leading=24)
        s_sub    = ps('su', fontSize=9,  textColor=MID,   spaceAfter=10)
        s_sect   = ps('sc', fontName='Helvetica-Bold', fontSize=13, textColor=BLUE,
                      spaceBefore=12, spaceAfter=12)
        s_seat   = ps('sh', fontName='Helvetica-Bold', fontSize=10, textColor=DARK)
        s_badge  = ps('bd', fontName='Helvetica-Bold', fontSize=9,  textColor=colors.white,
                      alignment=TA_CENTER)
        s_detail = ps('dt', fontSize=10, textColor=DARK)
        s_kw     = ps('kw', fontSize=10, textColor=DARK)
        s_note   = ps('nt', fontSize=10, textColor=DARK)
        s_empty  = ps('em', fontSize=10, textColor=LIGHT)
        s_li     = ps('li', fontSize=10, textColor=DARK, leftIndent=14, spaceAfter=1)


        def esc(t):
            return html.escape(str(t))

        js = max(1, int(self.jury_size_var.get()))

        def status_of(j, jid):
            fp = self._fj_pos.get(jid, 0)
            if fp and fp <= js:      return f"Final Juror #{fp}",    GREEN
            if fp:                   return f"Alternate #{fp - js}", AGREEN
            if j.status == "excused":    return "Excused",            GREY
            if j.status == "struck_def": return "Defense Strike",     RED
            if j.status == "struck_pro": return "Prosecution Strike", RED
            return "Seated", BLUE

        W  = 6.5 * inch
        CW = [W - 1.45*inch, 1.45*inch]

        s_panel  = ps('pn', fontName='Helvetica-Bold', fontSize=12, textColor=BLUE,
                      spaceBefore=14, spaceAfter=4)

        def seat_block(sn, j, jid, panel_idx):
            stat, col = status_of(j, jid)
            trows = [
                [Paragraph(f"Panel {panel_idx + 1}  ·  Seat {sn}  —  {esc(j.name)},  Juror #{j.id}", s_seat),
                 Paragraph(stat, s_badge)],
                [Paragraph(f"Age: {esc(j.age)}" if j.age else "", s_detail), ""],
            ]
            if j.keywords:
                trows.append([Paragraph(f"Keywords:  {esc(j.keywords)}", s_kw), ""])
            notes_markup = _notes_to_rl_markup(j.notes)
            if notes_markup:
                trows.append([Paragraph(f"Notes:  {notes_markup}", s_note), ""])

            nr = len(trows)
            t = Table(trows, colWidths=CW)
            t.setStyle(TableStyle([
                ('BOX',           (0, 0), (-1, -1), 0.5, DIV),
                ('LINEBELOW',     (0, 0), (-1,  0), 0.5, DIV),
                ('BACKGROUND',    (0, 0), (-1,  0), BKGD),
                ('BACKGROUND',    (1, 0), ( 1,  0), col),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',    (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
                *[('SPAN', (0, i), (1, i)) for i in range(1, nr)],
            ]))
            return KeepTogether([t, Spacer(1, 6)])

        # ── Collect summary data ─────────────────────────────────────────────
        fj, alt, exc, sdef, spro, pool = [], [], [], [], [], []
        for pos, jid in enumerate(self.final_jury, 1):
            j = self.jurors.get(jid)
            if not j:
                continue
            if j.seat:
                loc = f"Panel {j.panel + 1}, Seat {j.seat}"
            else:
                loc = "unseated"
            line = f"{esc(j.name)}  (Juror #{j.id}, {loc})"
            (fj if pos <= js else alt).append(
                f"{pos}.  {line}" if pos <= js else f"Alt {pos - js}.  {line}"
            )

        for j in sorted(self.jurors.values(), key=lambda x: x.id):
            if j.seat:
                loc = f"Panel {j.panel + 1}, Seat {j.seat}"
            else:
                loc = "unseated"
            line = f"{esc(j.name)}  (Juror #{j.id}, {loc})"
            if j.status == "excused":      exc.append(line)
            elif j.status == "struck_def": sdef.append(line)
            elif j.status == "struck_pro": spro.append(line)
            elif j.status == "pool":
                pool.append(f"{esc(j.name)}  (Juror #{j.id})")

        # ── Build story ──────────────────────────────────────────────────────
        story = []

        # Page 1 — header + summary
        story.append(Paragraph(esc(report_title), s_title))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y  ·  %I:%M %p')}",
            s_sub,
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=10))

        story.append(Paragraph("Summary", s_sect))

        def summ(title, items, col):
            story.append(Paragraph(title, ps(f'h{title[:4]}', fontName='Helvetica-Bold',
                                             fontSize=11, textColor=col,
                                             spaceBefore=8, spaceAfter=3)))
            for it in items:
                story.append(Paragraph(f"• {it}", s_li))
            if not items:
                story.append(Paragraph("None", s_note))

        summ("Final Jury",         fj,   GREEN)
        summ("Alternates",         alt,  AGREEN)
        summ("Excused",            exc,  GREY)
        summ("Defense Struck",     sdef, RED)
        summ("Prosecution Struck", spro, RED)
        summ("Preliminary Pool",   pool, BLUE)

        # Page 2+ — seat-by-seat details by panel
        story.append(PageBreak())
        story.append(Paragraph(esc(report_title), s_title))
        story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=10))
        story.append(Paragraph("Juror Pool — By Panel & Seat", s_sect))
        for pi, panel in enumerate(self.panel_seats):
            story.append(Paragraph(f"Panel {pi + 1}", s_panel))
            story.append(HRFlowable(width="100%", thickness=0.5, color=DIV, spaceAfter=6))
            for sn in range(1, rows_n * cols_n + 1):
                jid = panel.get(sn)
                j   = self.jurors.get(jid) if jid else None
                if j:
                    story.append(seat_block(sn, j, jid, pi))
                else:
                    story.append(Paragraph(f"Seat {sn}  —  empty", s_empty))
                    story.append(Spacer(1, 4))
            story.append(Spacer(1, 8))

        try:
            doc = SimpleDocTemplate(
                path, pagesize=letter,
                leftMargin=0.75*inch, rightMargin=0.75*inch,
                topMargin=0.75*inch, bottomMargin=0.75*inch,
                title=report_title,
            )
            doc.build(story)
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not write PDF:\n{e}")
            return

        messagebox.showinfo("Exported", f"PDF saved to:\n{path}")

    def _apply_panel_positions(self, src: dict):
        sw = 6
        snap = dict(src)
        def _do():
            try:
                exc_h  = snap["exc_height"]
                def_h  = snap["def_height"]
                pro_h  = snap["pro_height"]
                total  = self._pane_lv.winfo_height()
                y0     = max(80, total - exc_h - def_h - pro_h - 3 * sw)
                self._pane_lv.sash_place(0, 0, y0)
                self._pane_lv.sash_place(1, 0, y0 + sw + exc_h)
                self._pane_lv.sash_place(2, 0, y0 + sw + exc_h + sw + def_h)
            except Exception:
                pass
            try:
                self._pane_outer.sash_place(0, max(140, snap["lf_width"]), 0)
            except Exception:
                pass
            try:
                fj_w    = snap["fj_width"]
                total_w = self._pane_outer.winfo_width()
                self._pane_outer.sash_place(1, max(0, total_w - fj_w - sw), 0)
            except Exception:
                pass
            try:
                vp_h    = snap["vp_detail_height"]
                total_h = self._pane_vp.winfo_height()
                self._pane_vp.sash_place(0, 0, max(0, total_h - vp_h - sw))
            except Exception:
                pass
            try:
                detail_h = snap["detail_height"]
                total_h  = self._pane_fj.winfo_height()
                self._pane_fj.sash_place(0, 0, max(0, total_h - detail_h - sw))
            except Exception:
                pass
        self.after(50, _do)

    @staticmethod
    def _sash_coords(pane, n: int) -> list:
        out = []
        for i in range(n):
            try:    out.append(list(pane.sash_coord(i)))
            except Exception: out.append(None)
        return out

    def _work_dir(self) -> str:
        d = SETTINGS.get("work_dir", "")
        if d and os.path.isdir(d):
            return d
        return os.path.dirname(os.path.abspath(__file__))

    def _build_save_data(self) -> dict:
        return dict(rows=int(self.rows_var.get()),
                    cols=int(self.cols_var.get()),
                    jury_size=int(self.jury_size_var.get()),
                    corner=self._corner,
                    num_panels=len(self.panel_seats),
                    active_panel=self._active_panel,
                    final_jury=self.final_jury,
                    jurors=[j.to_dict() for j in self.jurors.values()],
                    theme=self._theme_name,
                    zoom=self._zoom_var.get(),
                    seat_width=SW,
                    seat_height=SH,
                    seat_gap=SGAP,
                    font_size=SETTINGS["font_size"],
                    seat_font_size=SETTINGS["seat_font_size"],
                    rte_font=SETTINGS["rte_font"],
                    rte_bold=SETTINGS["rte_bold"],
                    rte_italic=SETTINGS["rte_italic"],
                    rte_underline=SETTINGS["rte_underline"],
                    window_geometry=self.geometry(),
                    sash_outer=self._sash_coords(self._pane_outer, 2),
                    sash_lv=self._sash_coords(self._pane_lv, 3),
                    sash_vp=self._sash_coords(self._pane_vp, 1),
                    sash_fj=self._sash_coords(self._pane_fj, 1))

    def _schedule_autosave(self):
        if self._autosave_id is not None:
            self.after_cancel(self._autosave_id)
            self._autosave_id = None
        interval = SETTINGS.get("autosave_interval", 15)
        if interval > 0:
            self._autosave_id = self.after(interval * 60_000, self._autosave)

    def _autosave(self):
        self._autosave_id = None
        if self.jurors:
            path = os.path.join(self._work_dir(), "autosave.json")
            try:
                with open(path, "w") as f:
                    json.dump(self._build_save_data(), f, indent=2)
                self.status.set(f"Autosaved → {os.path.basename(path)}")
            except OSError:
                pass
        self._schedule_autosave()

    def _save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self._work_dir(),
            initialfile="jury.json",
        )
        if not path:
            return
        with open(path, "w") as f:
            json.dump(self._build_save_data(), f, indent=2)
        self.status.set(f"Saved → {os.path.basename(path)}")

    def _open(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self._work_dir(),
        )
        if not path:
            return
        with open(path) as f:
            data = json.load(f)

        self._selected_jid = None
        self._clear_detail()
        self._selected_final_jid = None
        self._clear_fj_detail()
        self.jurors.clear()
        Juror._next = 1
        for d in data.get("jurors", []):
            j = Juror.from_dict(d)
            if j.status == "struck":  # migrate old saves
                j.status = "struck_def"
            self.jurors[j.id] = j

        rows = data.get("rows", 4)
        cols = data.get("cols", 7)
        self.jury_size_var.set(data.get("jury_size", 12))
        self._corner = data.get("corner", "TL")
        self.corner_var.set(self._corner)

        num_panels = max(1, data.get("num_panels", 1))
        SETTINGS["num_panels"] = num_panels
        empty = {i: None for i in range(1, rows * cols + 1)}
        self.panel_seats   = [dict(empty) for _ in range(num_panels)]
        self._active_panel = min(data.get("active_panel", 0), num_panels - 1)
        self.final_jury    = [jid for jid in data.get("final_jury", [])
                              if jid in self.jurors]
        self.rows_var.set(rows)
        self.cols_var.set(cols)

        for j in self.jurors.values():
            if j.status != "pool" and j.seat is not None:
                pi = max(0, min(j.panel, num_panels - 1))
                j.panel = pi
                if j.seat in self.panel_seats[pi]:
                    self.panel_seats[pi][j.seat] = j.id

        self._update_panel_tabs()

        global SW, SH, SGAP
        if "seat_width" in data:
            SW = SETTINGS["seat_width"] = int(data["seat_width"])
        if "seat_height" in data:
            SH = SETTINGS["seat_height"] = int(data["seat_height"])
        if "seat_gap" in data:
            SGAP = SETTINGS["seat_gap"] = int(data["seat_gap"])
        if "seat_font_size" in data:
            SETTINGS["seat_font_size"] = int(data["seat_font_size"])
        if "font_size" in data:
            self._rescale_fonts(int(data["font_size"]))
        if "rte_font" in data:
            SETTINGS["rte_font"]      = data["rte_font"]
        if "rte_bold" in data:
            SETTINGS["rte_bold"]      = bool(data["rte_bold"])
        if "rte_italic" in data:
            SETTINGS["rte_italic"]    = bool(data["rte_italic"])
        if "rte_underline" in data:
            SETTINGS["rte_underline"] = bool(data["rte_underline"])

        self._refresh()

        if "theme" in data:
            self._apply_theme(data["theme"])
        if "zoom" in data:
            self._zoom_var.set(data["zoom"])
            self._redraw()
        if "window_geometry" in data:
            try:
                self.geometry(data["window_geometry"])
            except Exception:
                pass

        def _restore_sashes():
            self.update_idletasks()
            for i, coord in enumerate(data.get("sash_outer", [])):
                if coord:
                    try: self._pane_outer.sash_place(i, coord[0], coord[1])
                    except Exception: pass
            for i, coord in enumerate(data.get("sash_lv", [])):
                if coord:
                    try: self._pane_lv.sash_place(i, coord[0], coord[1])
                    except Exception: pass
            for i, coord in enumerate(data.get("sash_vp", [])):
                if coord:
                    try: self._pane_vp.sash_place(i, coord[0], coord[1])
                    except Exception: pass
            for i, coord in enumerate(data.get("sash_fj", [])):
                if coord:
                    try: self._pane_fj.sash_place(i, coord[0], coord[1])
                    except Exception: pass
            self._redraw()

        self.after(80, _restore_sashes)
        self.status.set(f"Opened {os.path.basename(path)}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = JuryApp()
    app.mainloop()
