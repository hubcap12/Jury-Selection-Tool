from __future__ import annotations
import tkinter as tk

from .colors import C
from .fonts import FONTS


class DragMixin:

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
        self._save_detail(redraw=False)
        j = self.jurors.get(jid)
        if not j:
            return
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
                if j.status == "seated":
                    j.status = "pool"
                j.seat, j.is_alt, j.panel = None, False, 0
            self.seats[num] = None
            if jid in self.final_jury:
                self.final_jury.remove(jid)

    def _cv_drop(self, event):
        was_dragging = self._drag_win is not None
        self._kill_drag_win()
        if self._drag_id is None:
            return

        if self._drag_source == "seat":
            if was_dragging:
                self._handle_seat_drop(event)
            else:
                self._drag_id = None
                self._drag_source = None
                self._drag_seat_info = None
        else:
            self._assign(event.x, event.y)
            self._drag_id = None
            self._drag_seat_info = None

    def _handle_seat_drop(self, event):
        jid              = self._drag_id
        _, src_num       = self._drag_seat_info
        self._drag_id    = None
        self._drag_source = None

        rx = self.canvas.winfo_rootx() + event.x
        ry = self.canvas.winfo_rooty() + event.y

        target = self._seat_at(event.x, event.y)
        if target and target != (False, src_num):
            _, dst_num = target
            dst_jid = self.seats.get(dst_num)
            if dst_jid is not None:
                src_j = self.jurors.get(jid)
                dst_j = self.jurors.get(dst_jid)
                if not src_j or not dst_j:
                    return
                self.seats[src_num] = dst_jid
                self.seats[dst_num] = jid
                src_j.seat, src_j.panel = dst_num, self._active_panel
                dst_j.seat, dst_j.panel = src_num, self._active_panel
                self._drag_seat_info = None
                self._redraw()  # swap changes no pool/final lists — canvas only
            else:
                self._vacate_seat(src_num)
                self._drag_id = jid
                self._assign(event.x, event.y)
                self._drag_id = None
            return

        if self._widget_contains(self.pool_lb, rx, ry):
            self._vacate_seat(src_num)
            j = self.jurors.get(jid)
            if j:
                j.status = "pool"
            self._refresh()
            return

        if self._widget_contains(self.final_lb, rx, ry):
            self._toggle_final(jid)
            self._drag_seat_info = None
            return

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

    def _widget_contains(self, widget: tk.Widget, rx: int, ry: int) -> bool:
        wx, wy = widget.winfo_rootx(), widget.winfo_rooty()
        return wx <= rx < wx + widget.winfo_width() and wy <= ry < wy + widget.winfo_height()
