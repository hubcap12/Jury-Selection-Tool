from __future__ import annotations
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from .config import SETTINGS
from .fonts import _resource_path
from .models import Juror
from .pdf_export import export_pdf


class FileIOMixin:

    def _export_pdf(self):
        export_pdf(
            parent=self,
            rows_n=int(self.rows_var.get()),
            cols_n=int(self.cols_var.get()),
            jury_size=int(self.jury_size_var.get()),
            jurors=self.jurors,
            panel_seats=self.panel_seats,
            final_jury=self.final_jury,
            fj_pos=self._fj_pos,
            work_dir=self._work_dir(),
        )

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
            self._kill_drag_win()
            self._drag_id = None
            self._drag_source = None
            self._drag_seat_info = None
            self.jurors.clear()
            Juror._next = 1
            self._selected_jid = None
            self._clear_detail()
            self._selected_final_jid = None
            self._clear_fj_detail()
            self._init_layout(int(self.rows_var.get()), int(self.cols_var.get()))

    def _save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self._work_dir(),
            initialfile="jury.json",
        )
        if not path:
            return
        try:
            with open(path, "w") as f:
                json.dump(self._build_save_data(), f, indent=2)
        except OSError as e:
            messagebox.showerror("Save Failed", f"Could not write file:\n{e}")
            return
        self.status.set(f"Saved → {os.path.basename(path)}")

    def _open(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self._work_dir(),
        )
        if not path:
            return
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, ValueError) as e:
            messagebox.showerror("Open Failed", f"Could not read file:\n{e}")
            return
        if not isinstance(data, dict):
            messagebox.showerror("Open Failed", "File does not contain valid jury data.")
            return

        self._selected_jid = None
        self._clear_detail()
        self._selected_final_jid = None
        self._clear_fj_detail()
        self.jurors.clear()
        Juror._next = 1
        for d in data.get("jurors", []):
            j = Juror.from_dict(d)
            if j.status == "struck":
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

        if "seat_width" in data:
            self.SW = SETTINGS["seat_width"] = int(data["seat_width"])
        if "seat_height" in data:
            self.SH = SETTINGS["seat_height"] = int(data["seat_height"])
        if "seat_gap" in data:
            self.SGAP = SETTINGS["seat_gap"] = int(data["seat_gap"])
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

        if "theme" in data:
            self._apply_theme(data["theme"])
        if "zoom" in data:
            self._zoom_var.set(data["zoom"])

        self._refresh()
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

    def _autosave(self):
        self._autosave_id = None
        if self.jurors:
            d    = self._work_dir()
            keep = max(1, SETTINGS.get("autosave_keep", 3))
            try:
                oldest = os.path.join(d, f"autosave_{keep}.json")
                if os.path.exists(oldest):
                    os.remove(oldest)
                for i in range(keep - 1, 0, -1):
                    src = os.path.join(d, f"autosave_{i}.json")
                    dst = os.path.join(d, f"autosave_{i + 1}.json")
                    if os.path.exists(src):
                        os.replace(src, dst)
                path = os.path.join(d, "autosave_1.json")
                with open(path, "w") as f:
                    json.dump(self._build_save_data(), f, indent=2)
                self.status.set("Autosaved → autosave_1.json")
            except OSError:
                pass
        self._schedule_autosave()

    def _schedule_autosave(self):
        if self._autosave_id is not None:
            self.after_cancel(self._autosave_id)
            self._autosave_id = None
        interval = SETTINGS.get("autosave_interval", 15)
        if interval > 0:
            self._autosave_id = self.after(interval * 60_000, self._autosave)

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
                    seat_width=self.SW,
                    seat_height=self.SH,
                    seat_gap=self.SGAP,
                    font_size=SETTINGS["font_size"],
                    seat_font_size=SETTINGS["seat_font_size"],
                    rte_font=SETTINGS["rte_font"],
                    rte_bold=SETTINGS["rte_bold"],
                    rte_italic=SETTINGS["rte_italic"],
                    rte_underline=SETTINGS["rte_underline"],
                    window_geometry=self.geometry(),
                    sash_outer=self._sash_coords(self._pane_outer, 2),
                    sash_lv=self._sash_coords(self._pane_lv, 4),
                    sash_vp=self._sash_coords(self._pane_vp, 1),
                    sash_fj=self._sash_coords(self._pane_fj, 1))

    def _apply_panel_positions(self, src: dict):
        from .config import DEFAULT_SETTINGS
        sw = 6
        snap = dict(src)
        def _do():
            try:
                exc_h  = snap["exc_height"]
                def_h  = snap["def_height"]
                pro_h  = snap["pro_height"]
                both_h = snap.get("both_height", DEFAULT_SETTINGS["both_height"])
                total  = self._pane_lv.winfo_height()
                y0     = max(80, total - exc_h - def_h - pro_h - both_h - 4 * sw)
                self._pane_lv.sash_place(0, 0, y0)
                self._pane_lv.sash_place(1, 0, y0 + sw + exc_h)
                self._pane_lv.sash_place(2, 0, y0 + sw + exc_h + sw + def_h)
                self._pane_lv.sash_place(3, 0, y0 + sw + exc_h + sw + def_h + sw + pro_h)
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
        docs = os.path.expanduser("~/Documents")
        return docs if os.path.isdir(docs) else os.path.expanduser("~")
