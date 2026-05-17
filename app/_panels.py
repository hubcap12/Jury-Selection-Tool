from __future__ import annotations
import tkinter as tk

from colors import C
from config import SETTINGS
from fonts import FONTS


class PanelsMixin:

    @property
    def seats(self) -> dict:
        if not self.panel_seats:
            return {}
        idx = max(0, min(self._active_panel, len(self.panel_seats) - 1))
        return self.panel_seats[idx]

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
                        if j.status not in ("excused", "struck_def", "struck_pro", "struck_both"):
                            j.status = "pool"
        if self._active_panel >= len(self.panel_seats):
            self._active_panel = len(self.panel_seats) - 1
        self._update_panel_tabs()
        self._refresh()

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
                        was_seated = j.status == "seated"
                        j.seat, j.is_alt, j.panel = None, False, 0
                        if was_seated:
                            j.status = "pool"

            new_seats = {i: None for i in range(1, rows * cols + 1)}
            for s, jid in old_seats.items():
                if jid and s in new_seats:
                    j = self.jurors.get(jid)
                    if not j:
                        continue
                    new_seats[s] = jid
                    j.seat, j.is_alt, j.status, j.panel = s, False, "seated", pi
            self.panel_seats[pi] = new_seats

        self.final_jury = [jid for jid in self.final_jury if jid in self.jurors]
        self._refresh()
