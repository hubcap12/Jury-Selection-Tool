from __future__ import annotations
import tkinter as tk

from .colors import C
from .config import SETTINGS
from .models import STATUS_DISPLAY


class DrawMixin:

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
                    (cw - pad) / (cols * self.SW + (cols - 1) * self.SGAP),
                    (ch - pad) / (rows * self.SH + (rows - 1) * self.SGAP))
        scale = max(0.1, scale * zoom)
        sw   = max(50, int(self.SW   * scale))
        sh   = max(36, int(self.SH   * scale))
        sgap = max(4,  int(self.SGAP * scale))

        gw = cols * sw + (cols - 1) * sgap
        gh = rows * sh + (rows - 1) * sgap
        ox = (cw - gw) // 2
        oy = max(10, (ch - gh) // 2)

        bdr = sgap
        self.canvas.create_rectangle(ox - bdr, oy - bdr, ox + gw + bdr, oy + gh + bdr,
                                     fill=C["border"], outline=C["border"], width=1,
                                     tags=("grid_bg",))

        fscale    = SETTINGS["seat_font_size"] / 10.0
        f_sm      = max(6, int(8  * scale * fscale))
        f_md      = max(7, int(11 * scale * fscale))
        f_empty   = max(6, int(9  * scale * fscale))
        spad      = max(3, int(7  * scale))
        js        = max(1, int(self.jury_size_var.get()))
        fj_pos    = self._fj_pos

        cur_seats = self.seats  # cache property lookup for the entire redraw
        xywh: dict[int, tuple] = {}
        for r in range(rows):
            for c in range(cols):
                sn = self._seat_num(r, c, rows, cols, self._corner)
                x  = ox + c * (sw + sgap)
                y  = oy + r * (sh + sgap)
                xywh[sn] = (x, y)
                self._draw_seat(sn, x, y, sw, sh, scale,
                                f_sm, f_md, f_empty, spad, js, fj_pos, cur_seats)

        self._seat_geo = dict(sw=sw, sh=sh, sgap=sgap, ox=ox, oy=oy,
                              rows=rows, cols=cols, scale=scale,
                              f_sm=f_sm, f_md=f_md, f_empty=f_empty,
                              spad=spad, js=js, fj_pos=fj_pos, xywh=xywh)

    def _draw_seat(self, num: int, x: int, y: int, sw: int, sh: int, scale: float,
                   f_sm: int, f_md: int, f_empty: int, spad: int, js: int,
                   fj_pos: dict, cur_seats: dict | None = None):
        jid   = (cur_seats if cur_seats is not None else self.seats).get(num)
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
                    "seated":      C["seat_seated"],
                    "excused":     C["seat_excused"],
                    "struck_def":  C["seat_struck"],
                    "struck_pro":  C["seat_struck"],
                    "struck_both": C["seat_struck"],
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
            return None
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
                if oj.status not in ("excused", "struck_def", "struck_pro", "struck_both"):
                    oj.status = "pool"

        j = self.jurors.get(self._drag_id)
        if not j:
            return
        self.seats[num] = self._drag_id
        j.seat, j.is_alt, j.status, j.panel = num, False, "seated", self._active_panel
        self.status.set(f"Seated {j.name} in seat {num}.")
        self._selected_jid = self._drag_id
        self._show_juror_detail(j, seat_label=f"Panel {self._active_panel + 1}  ·  Seat {num}")
        self._refresh()
