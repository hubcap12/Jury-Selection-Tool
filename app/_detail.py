from __future__ import annotations
import json
import tkinter as tk

from colors import C
from fonts import FONTS
from models import STATUS_DISPLAY
from richtext import _notes_to_runs, _load_rich_into_text


class DetailMixin:

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

    def _show_juror_detail(self, j, seat_label: str = ""):
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

    def _show_fj_detail(self, j):
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
        elif lb is self.both_struck_lb:
            j = self.jurors.get(self._both_struck_ids[idx]) if idx < len(self._both_struck_ids) else None
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
        j = self.jurors.get(jid)
        if not j:
            return
        in_final = jid in self.final_jury

        rating_sym = ("▲" * j.rating if j.rating > 0
                      else "▼" * abs(j.rating) if j.rating < 0 else "")
        header = f"{j.name}  {rating_sym}" if rating_sym else j.name
        m = tk.Menu(self, tearoff=0)
        m.add_command(label=header, state="disabled", font=FONTS["md_bold"])
        m.add_separator()
        m.add_cascade(label="Priority", menu=self._priority_submenu(m, jid))
        m.add_separator()
        m.add_command(
            label="Remove from Final Jury" if in_final else "Add to Final Jury",
            command=lambda: self._toggle_final(jid),
        )
        dismissed = j.status in ("excused", "struck_def", "struck_pro", "struck_both")
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
        m.add_command(label="Strike — Both",
                      state="disabled" if j.status == "struck_both" else "normal",
                      command=lambda: self._set_status(jid, "struck_both"))
        m.add_separator()
        m.add_command(label="Edit Notes…",
                      command=lambda: self._edit_by_id(jid))
        m.post(event.x_root, event.y_root)
