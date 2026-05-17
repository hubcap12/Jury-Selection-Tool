"""Rich-text editing widget, juror dialog, and notes serialisation helpers."""
from __future__ import annotations
import html
import json
import tkinter as tk

from .colors import C
from .config import SETTINGS
from .fonts import FONTS
from .models import Juror


# ── Notes serialisation helpers ───────────────────────────────────────────────

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
        if underline: text = f"<u>{text}</u>"
        if italic:    text = f"<i>{text}</i>"
        if bold:      text = f"<b>{text}</b>"
        attrs = []
        if color: attrs.append(f'color="{color}"')
        if font:  attrs.append(f'name="{_RL_FONT_MAP.get(font, "Helvetica")}"')
        if attrs: text = f'<font {" ".join(attrs)}>{text}</font>'
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
            bold  = run.get("bold",      False)
            ital  = run.get("italic",    False)
            ul    = run.get("underline", False)
            color = run.get("color",     C["input_fg"])
            fam   = run.get("font",      "Helvetica")
            size  = SETTINGS["font_size"]
            tname = f"rdisp_{abs(hash((bool(bold), bool(ital), bool(ul), color, fam)))}"
            widget.tag_configure(tname,
                font=(fam, size, "bold" if bold else "normal",
                      "italic" if ital else "roman"),
                foreground=color, underline=int(ul))
            if widget.compare(start, "<", ep):
                widget.tag_add(tname, start, ep)


# ── RichTextEditor ────────────────────────────────────────────────────────────

class RichTextEditor(tk.Frame):
    """tk.Text with a formatting toolbar (bold, italic, underline, font family)."""

    _FAMILIES = ("Helvetica", "Arial", "Times New Roman", "Courier New",
                 "Georgia", "Verdana", "Calibri")

    def __init__(self, parent, height: int = 6):
        super().__init__(parent, bg=C["bg"])
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._bold      = SETTINGS.get("rte_bold",      False)
        self._italic    = SETTINGS.get("rte_italic",    False)
        self._underline = SETTINGS.get("rte_underline", False)
        self._family    = SETTINGS.get("rte_font",      "Helvetica")
        self._tb_updating = False
        self._fmt_queue:   list = []
        self._flush_pending = False
        self._tag_cache: dict[str, str] = {}
        self._rev_cache: dict[str, str] = {}

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
        result = end
        for tag_name in self._tag_cache.values():
            nxt = self._text.tag_nextrange(tag_name, pos, end)
            if nxt and self._text.compare(str(nxt[0]), "<", result):
                result = str(nxt[0])
        return result

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        self._tb = tk.Frame(self, bg=C["btn_bg"],
                            highlightthickness=1,
                            highlightbackground=C["divider"])
        self._tb.grid(row=0, column=0, sticky="ew")

        bk = dict(bg=C["btn_bg"], fg=C["btn_fg"], relief="flat", bd=0,
                  highlightthickness=0, padx=6, pady=2, cursor="hand2",
                  activebackground=C["btn_hover"],
                  activeforeground=C["txt_light"])

        self._fam_var = tk.StringVar(value=self._family)
        fam = tk.OptionMenu(self._tb, self._fam_var, *self._FAMILIES,
                            command=self._apply_family)
        fam.configure(bg=C["btn_bg"], fg=C["btn_fg"], relief="flat",
                      highlightthickness=0, padx=2, pady=1, width=16,
                      activebackground=C["btn_hover"],
                      activeforeground=C["txt_light"],
                      font=FONTS["sm"], anchor="w")
        fam["menu"].configure(bg=C["input_bg"], fg=C["input_fg"],
                              activebackground=C["pool_sel"],
                              activeforeground=C["txt_light"],
                              font=FONTS["sm"])
        fam.pack(side="left", padx=(2, 0))
        self._tsep()

        self._btn_b = tk.Button(self._tb, text="B", font=FONTS["md_bold"],
                                command=self._toggle_bold, **bk)
        self._btn_b.pack(side="left")
        self._btn_i = tk.Button(self._tb, text="I", font=FONTS["md_italic"],
                                command=self._toggle_italic, **bk)
        self._btn_i.pack(side="left")
        self._btn_u = tk.Button(self._tb, text="U", font=FONTS["md"],
                                command=self._toggle_underline, **bk)
        self._btn_u.pack(side="left")
        self._tsep()

        self._btn_bullet = tk.Button(self._tb, text="•", font=FONTS["md"],
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
        self._text.bind("<Control-b>", lambda _: self._toggle_bold()      or "break")
        self._text.bind("<Control-i>", lambda _: self._toggle_italic()    or "break")
        self._text.bind("<Control-u>", lambda _: self._toggle_underline() or "break")

    # ── Toolbar state ─────────────────────────────────────────────────────────

    def _update_toolbar(self, bold, italic, underline, family):
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
        seen: dict[str, set] = {
            "bold": set(), "italic": set(), "underline": set(), "font": set(),
        }
        default = dict(bold=False, italic=False, underline=False,
                       font=self._family)
        pos = start
        while self._text.compare(pos, "<", end):
            cur_tag = next(
                (t for t in self._text.tag_names(pos) if t in self._rev_cache),
                None)
            if cur_tag:
                fmt = self._parse_key(self._rev_cache[cur_tag])
                region_end = end
                for s, e in zip(*[iter(self._text.tag_ranges(cur_tag))] * 2):
                    s, e = str(s), str(e)
                    if (self._text.compare(s, "<=", pos) and
                            self._text.compare(pos, "<", e)):
                        region_end = (e if self._text.compare(e, "<=", end)
                                      else end)
                        break
            else:
                fmt = default
                region_end = self._next_tag_start(
                    self._text.index(f"{pos}+1c"), end)
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
            self._update_toolbar(fmt["bold"], fmt["italic"],
                                 fmt["underline"], fmt["font"])
            self._update_bullet_btn()
            return

        seen = self._formats_in_range(sel_start, sel_end)
        def _single(s):
            return next(iter(s)) if len(s) == 1 else None

        self._update_toolbar(
            _single(seen["bold"]), _single(seen["italic"]),
            _single(seen["underline"]), _single(seen["font"]),
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
                self._bold, self._italic, self._underline, self._family,
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
        continuing_bullet = self._is_bullet_line(cur_line) and cur_col >= 2
        if (self._is_bullet_line(cur_line) and
                self._text.get(f"{cur_line}.0", f"{cur_line}.end") == "• "):
            self._text.delete(f"{cur_line}.0", f"{cur_line}.end")
            self._text.tag_remove("bullet_line",
                                  f"{cur_line}.0", f"{cur_line}.end+1c")
            self._btn_bullet.configure(bg=C["btn_bg"], relief="flat")
            return "break"
        self._text.insert("insert", "\n")
        end = self._text.index("insert")
        if self._text.compare(pre, "<", end):
            self._apply_fmt_direct(pre, end)
        if continuing_bullet:
            new_line = int(self._text.index("insert").split(".")[0])
            self._text.insert(f"{new_line}.0", "• ")
            self._text.tag_add("bullet_line",
                               f"{new_line}.0", f"{new_line}.end+1c")
        return "break"

    def _on_paste(self, _=None):
        pre = self._text.index("insert")
        self.after_idle(lambda: self._post_paste(pre))

    def _post_paste(self, pre: str):
        end = self._text.index("insert")
        if self._text.compare(pre, "<", end):
            self._apply_fmt_direct(pre, end)

    def _apply_fmt_direct(self, start: str, end: str):
        tag = self._get_tag(self._bold, self._italic,
                            self._underline, self._family)
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
                (t for t in self._text.tag_names(pos) if t in self._rev_cache),
                None)
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
                region_end = self._next_tag_start(
                    self._text.index(f"{pos}+1c"), end)
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
            self._update_toolbar(fmt["bold"], fmt["italic"],
                                 fmt["underline"], fmt["font"])
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
        first = int(start.split(".")[0])
        last  = int(end.split(".")[0])
        if end.split(".")[1] == "0" and last > first:
            last -= 1
        for ln in range(first, last + 1):
            self._text.tag_remove("bullet_line",
                                  f"{ln}.0", f"{ln}.end+1c")
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

        all_bulleted = all(self._is_bullet_line(ln)
                          for ln in range(first, last + 1))
        for ln in range(first, last + 1):
            if all_bulleted:
                if self._is_bullet_line(ln):
                    self._text.delete(f"{ln}.0", f"{ln}.2")
                self._text.tag_remove("bullet_line",
                                      f"{ln}.0", f"{ln}.end+1c")
            else:
                if not self._is_bullet_line(ln):
                    self._text.insert(f"{ln}.0", "• ")
                self._text.tag_add("bullet_line",
                                   f"{ln}.0", f"{ln}.end+1c")

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
                self._text.tag_add("bullet_line",
                                   f"{ln}.0", f"{ln}.end+1c")

    # ── Serialisation ─────────────────────────────────────────────────────────

    def get_runs(self) -> list:
        if not self._text.get("1.0", "end-1c"):
            return []
        runs = []
        pos  = "1.0"
        end  = self._text.index("end-1c")
        while self._text.compare(pos, "<", end):
            cur_tag = next(
                (t for t in self._text.tag_names(pos) if t in self._rev_cache),
                None)
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
                region_end = self._next_tag_start(
                    self._text.index(f"{pos}+1c"), end)
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

    # ── Public API ────────────────────────────────────────────────────────────

    def contains_widget(self, widget: tk.Widget) -> bool:
        if widget is self:
            return True
        try:
            while widget:
                if widget is self:
                    return True
                widget = widget.master  # type: ignore[assignment]
        except Exception:
            pass
        return False

    def bind_text(self, sequence: str, func):
        self._text.bind(sequence, func)

    def focus_set(self):
        self._text.focus_set()


# ── Juror dialog ──────────────────────────────────────────────────────────────

class JurorDialog(tk.Toplevel):
    _last_size: str | None = None

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
        tk.Label(self, text="Name:", bg=C["bg"], fg=C["txt_dark"],
                 font=FONTS["lg"]).grid(row=0, column=0, sticky="e", **p)
        self._name_var = tk.StringVar(value=juror.name if juror else "")
        entry = tk.Entry(self, textvariable=self._name_var, width=39,
                         bg=C["input_bg"], fg=C["input_fg"],
                         insertbackground=C["input_fg"],
                         relief="solid", bd=1, font=FONTS["lg"])
        entry.grid(row=0, column=1, sticky="ew", **p)
        entry.focus_set()

        tk.Label(self, text="Age:", bg=C["bg"], fg=C["txt_dark"],
                 font=FONTS["lg"]).grid(row=1, column=0, sticky="e", **p)
        self._age_var = tk.StringVar(value=juror.age if juror else "")
        tk.Entry(self, textvariable=self._age_var, width=8,
                 bg=C["input_bg"], fg=C["input_fg"],
                 insertbackground=C["input_fg"],
                 relief="solid", bd=1, font=FONTS["lg"]
                 ).grid(row=1, column=1, sticky="w", **p)

        tk.Label(self, text="Keywords:", bg=C["bg"], fg=C["txt_dark"],
                 font=FONTS["lg"]).grid(row=2, column=0, sticky="e", **p)
        self._kw_var = tk.StringVar(value=juror.keywords if juror else "")
        tk.Entry(self, textvariable=self._kw_var, width=39,
                 bg=C["input_bg"], fg=C["input_fg"],
                 insertbackground=C["input_fg"],
                 relief="solid", bd=1, font=FONTS["lg"]
                 ).grid(row=2, column=1, sticky="ew", **p)
        tk.Label(self, text="comma-separated", bg=C["bg"], fg=C["txt_muted"],
                 font=FONTS["sm"]).grid(row=2, column=1, sticky="se", padx=10)

        tk.Label(self, text="Notes:", bg=C["bg"], fg=C["txt_dark"],
                 font=FONTS["lg"]).grid(row=3, column=0, sticky="ne", **p)
        self._notes_box = RichTextEditor(self, height=6)
        self._notes_box.grid(row=3, column=1, sticky="nsew", **p)
        if juror and juror.notes:
            self._notes_box.set_runs(_notes_to_runs(juror.notes))

        bf = tk.Frame(self, bg=C["bg"])
        bf.grid(row=4, column=0, columnspan=2, pady=8)
        _bk = dict(bg=C["btn_bg"], fg=C["btn_fg"], relief="solid", bd=1,
                   highlightthickness=0, highlightbackground=C["bg"],
                   activebackground=C["btn_hover"],
                   activeforeground=C["txt_light"],
                   padx=8, pady=4)
        tk.Button(bf, text="Save",   width=10, command=self._ok,   **_bk
                  ).pack(side="left", padx=4)
        tk.Button(bf, text="Cancel", width=10, command=self.destroy, **_bk
                  ).pack(side="left", padx=4)

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
        self.result = True
        self.destroy()
