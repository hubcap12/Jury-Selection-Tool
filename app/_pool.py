from __future__ import annotations
import tkinter as tk

from .colors import C
from .fonts import FONTS


class PoolMixin:

    def _refresh_pool(self):
        pool, excused, def_struck, pro_struck, both_struck = [], [], [], [], []
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
            elif s == "struck_both":
                both_struck.append(j)

        self._pool_ids         = [j.id for j in pool]
        self._excused_ids      = [j.id for j in excused]
        self._def_struck_ids   = [j.id for j in def_struck]
        self._pro_struck_ids   = [j.id for j in pro_struck]
        self._both_struck_ids  = [j.id for j in both_struck]

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

        self.both_struck_lb.delete(0, "end")
        if both_struck:
            self.both_struck_lb.insert("end", *[j.label for j in both_struck])

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
            if j and j.status in ("excused", "struck_def", "struck_pro", "struck_both"):
                j.status = "seated"
        self._refresh()

    def _pool_juror(self, idx: int):
        if 0 <= idx < len(self._pool_ids):
            return self.jurors.get(self._pool_ids[idx])
        return None

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
        m.add_command(label="Strike — Both",
                      command=lambda: self._dismiss_pool_juror(j.id, "struck_both"))
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
        elif lb is self.both_struck_lb:
            id_list = self._both_struck_ids
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
