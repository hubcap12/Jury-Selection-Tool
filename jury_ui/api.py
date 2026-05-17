"""JavaScript-facing API.

Every public method here is callable from the UI as
``window.pywebview.api.method_name(...)`` and returns a JSON-serialisable
result.

Mutating methods return ``{"ok": True, "state": <full state>}`` so the
UI can replace its local state in one shot — keeps the bridge contract
trivial and idempotent.
"""
from __future__ import annotations

import os
from typing import Any


VALID_STATUSES = {"pool", "seated", "excused",
                  "struck_def", "struck_pro", "struck_both", "final"}


class JuryAPI:
    def __init__(self) -> None:
        self.jurors: list[dict[str, Any]] = []
        self.grid: dict[str, Any] = {"rows": 4, "cols": 7, "jury_size": 12, "corner": "TL"}
        self.active_panel: int = 1
        self.selected_seat: int | None = None
        self.selected_final: int | None = None
        self.theme: str = "dark"
        self._window = None
        self._last_save_path: str | None = None
        self._work_dir: str = os.path.expanduser("~")
        self._autosaver = None  # set by app.run() if autosave is enabled

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def _bind_window(self, window) -> None:
        self._window = window

    def set_work_dir(self, path: str) -> None:
        """Set the directory used for file dialogs and autosave snapshots."""
        if path and os.path.isdir(path):
            self._work_dir = path

    def _set_autosaver(self, autosaver) -> None:
        self._autosaver = autosaver

    # ── Helpers ────────────────────────────────────────────────────────────

    def _by_id(self, jid: int) -> dict[str, Any] | None:
        for j in self.jurors:
            if j["id"] == int(jid):
                return j
        return None

    def _next_id(self) -> int:
        return max((j["id"] for j in self.jurors), default=0) + 1

    def _state_ok(self) -> dict[str, Any]:
        return {"ok": True, "state": self.get_state()}

    def _renumber_finals(self) -> None:
        """Compact the finalNo values so they're 1..N in current order."""
        finals = [j for j in self.jurors if j.get("status") == "final"]
        finals.sort(key=lambda j: j.get("finalNo", 999))
        for i, j in enumerate(finals, start=1):
            j["finalNo"] = i

    # ── State ──────────────────────────────────────────────────────────────

    def get_state(self) -> dict[str, Any]:
        from app.config import SETTINGS
        return {
            "jurors":          self.jurors,
            "grid":            self.grid,
            "active_panel":    self.active_panel,
            "num_panels":      int(SETTINGS.get("num_panels", 3)),
            "left_col_width":  int(SETTINGS.get("left_col_width", 280)),
            "right_col_width": int(SETTINGS.get("right_col_width", 280)),
            "selected_seat":   self.selected_seat,
            "selected_final":  self.selected_final,
            "theme":           self.theme,
            "last_save_path":  self._last_save_path,
        }

    def save_layout(self, left_width: int, right_width: int) -> dict[str, Any]:
        """Persist current sidebar widths as the startup default."""
        from app.config import SETTINGS
        from jury_ui.settings import _persist
        SETTINGS["left_col_width"]  = max(160, int(left_width))
        SETTINGS["right_col_width"] = max(160, int(right_width))
        _persist()
        return {"ok": True}

    def set_active_panel(self, n: int) -> bool:
        self.active_panel = int(n)
        return True

    def set_theme(self, name: str) -> bool:
        self.theme = str(name)
        return True

    def select_seat(self, panel: int, seat: int) -> bool:
        self.selected_seat = int(seat)
        return True

    def set_grid(self, rows: int, cols: int, jury_size: int, corner: str | None = None) -> dict[str, Any]:
        self.grid["rows"] = int(rows)
        self.grid["cols"] = int(cols)
        self.grid["jury_size"] = int(jury_size)
        if corner is not None:
            self.grid["corner"] = corner
        return self._state_ok()

    # ── Juror CRUD ────────────────────────────────────────────────────────

    def add_juror(self, name: str, age="",
                  notes: str = "", keywords: str = "") -> dict[str, Any]:
        name = (name or "").strip()
        if not name:
            return {"ok": False, "msg": "Name is required"}
        try:
            age_i = int(age) if str(age).strip() else 0
        except (TypeError, ValueError):
            age_i = 0
        juror = {
            "id":       self._next_id(),
            "name":     name,
            "age":      age_i,
            "notes":    notes or "",
            "keywords": keywords or "",
            "status":   "pool",
            "panel":    0,
            "rating":   0,
        }
        self.jurors.append(juror)
        return self._state_ok()

    def edit_juror(self, jid: int, fields: dict[str, Any]) -> dict[str, Any]:
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        for k in ("name", "age", "notes", "keywords"):
            if k in fields:
                v = fields[k]
                if k == "age":
                    try:
                        v = int(v) if str(v).strip() else 0
                    except (TypeError, ValueError):
                        continue
                j[k] = v
        return self._state_ok()

    def remove_juror(self, jid: int) -> dict[str, Any]:
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        was_final = (j.get("status") == "final")
        self.jurors = [x for x in self.jurors if x["id"] != int(jid)]
        if was_final:
            self._renumber_finals()
        return self._state_ok()

    def reset(self) -> dict[str, Any]:
        self.jurors = []
        self.selected_seat = None
        self.selected_final = None
        return self._state_ok()

    # ── Seating ───────────────────────────────────────────────────────────

    def assign_seat(self, jid: int, panel: int, seat: int) -> dict[str, Any]:
        """Place ``jid`` in (panel, seat).

        • If the dragged juror came from another seat AND that target seat
          is already occupied, the two jurors **swap**.
        • If the dragged juror came from the pool / a status list (no
          previous seat), any existing occupant of the target gets bumped
          back to the pool.
        """
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        panel, seat = int(panel), int(seat)

        prev_seat = j.get("seat")
        prev_panel = j.get("panel")

        occupant = next(
            (o for o in self.jurors
             if o["id"] != jid
             and o.get("panel") == panel
             and o.get("seat") == seat),
            None,
        )

        if occupant is not None:
            if prev_seat is not None:
                # Swap — occupant takes the dragged juror's previous spot.
                occupant["seat"] = prev_seat
                occupant["panel"] = prev_panel
            else:
                # No prior seat — bump occupant back to the pool.
                occupant["seat"] = None
                occupant["panel"] = 0
                if occupant.get("status") == "seated":
                    occupant["status"] = "pool"

        j["seat"] = seat
        j["panel"] = panel
        if j.get("status") in ("pool", None):
            j["status"] = "seated"
        return self._state_ok()

    def unseat(self, jid: int) -> dict[str, Any]:
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        j["seat"] = None
        j["panel"] = 0
        if j.get("status") == "seated":
            j["status"] = "pool"
        if j.get("status") == "final":
            # Removing a seat shouldn't normally happen for a final juror,
            # but if it does, drop final status to avoid orphaned final-no.
            j["status"] = "pool"
            j.pop("finalNo", None)
            self._renumber_finals()
        return self._state_ok()

    def auto_seat(self) -> dict[str, Any]:
        """Place every pool juror into the first available seat on the
        currently-active panel.  Walk seat numbers 1..rows*cols, fill the
        first empty one with a pool juror, repeat until pool empty or
        seats full."""
        panel = self.active_panel
        capacity = self.grid["rows"] * self.grid["cols"]
        taken = {j["seat"] for j in self.jurors if j.get("panel") == panel and j.get("seat")}
        pool = [j for j in self.jurors if j.get("status") == "pool"]
        seat_no = 1
        for j in pool:
            while seat_no <= capacity and seat_no in taken:
                seat_no += 1
            if seat_no > capacity:
                break
            j["seat"] = seat_no
            j["panel"] = panel
            j["status"] = "seated"
            taken.add(seat_no)
            seat_no += 1
        return self._state_ok()

    # ── Status changes ────────────────────────────────────────────────────

    def set_status(self, jid: int, status: str) -> dict[str, Any]:
        """Set a non-final, non-seated status (excused / struck_*).  Setting
        to 'pool' or 'seated' goes through assign_seat/unseat instead."""
        if status not in {"excused", "struck_def", "struck_pro", "struck_both", "pool", "seated"}:
            return {"ok": False, "msg": f"Bad status {status!r}"}
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        was_final = (j.get("status") == "final")
        j["status"] = status
        if was_final:
            j.pop("finalNo", None)
            self._renumber_finals()
        if status == "pool":
            j["seat"] = None
            j["panel"] = 0
        return self._state_ok()

    def mark_final(self, jid: int) -> dict[str, Any]:
        """Mark a juror as a final-jury member.  Auto-assigns the next
        available final number."""
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        if j.get("status") == "final":
            return self._state_ok()
        finals = [x for x in self.jurors if x.get("status") == "final"]
        j["status"] = "final"
        j["finalNo"] = len(finals) + 1
        return self._state_ok()

    def unmark_final(self, jid: int) -> dict[str, Any]:
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        if j.get("status") != "final":
            return self._state_ok()
        j["status"] = "seated" if j.get("seat") else "pool"
        j.pop("finalNo", None)
        self._renumber_finals()
        return self._state_ok()

    def set_rating(self, jid: int, rating: int) -> dict[str, Any]:
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        try:
            r = int(rating)
        except (TypeError, ValueError):
            r = 0
        j["rating"] = max(-3, min(3, r))
        return self._state_ok()

    def set_keywords(self, jid: int, keywords: str) -> dict[str, Any]:
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        j["keywords"] = keywords or ""
        return self._state_ok()

    def set_notes(self, jid: int, notes: str) -> dict[str, Any]:
        j = self._by_id(jid)
        if not j:
            return {"ok": False, "msg": f"Juror #{jid} not found"}
        j["notes"] = notes or ""
        return self._state_ok()

    # ── Window controls ───────────────────────────────────────────────────

    def minimize(self) -> None:
        if self._window is not None:
            self._window.minimize()

    def toggle_maximize(self) -> None:
        if self._window is not None:
            self._window.toggle_fullscreen()

    def exit_app(self) -> None:
        if self._window is not None:
            self._window.destroy()

    # ── File menu ────────────────────────────────────────────────────────

    def open_file(self) -> dict[str, Any]:
        from .fileio import load_state
        path = self._file_dialog(
            save=False,
            file_types=("JSON files (*.json)", "All files (*.*)"),
        )
        if not path:
            return {"ok": False, "msg": "Cancelled"}
        try:
            load_state(self, path)
        except (OSError, ValueError) as e:
            return {"ok": False, "msg": f"Could not read file: {e}"}
        self._last_save_path = path
        return {"ok": True, "msg": f"Opened {os.path.basename(path)}",
                "state": self.get_state()}

    def save(self, save_as: bool = False) -> dict[str, Any]:
        from .fileio import save_state
        path = self._last_save_path if (not save_as and self._last_save_path) else None
        if path is None:
            path = self._file_dialog(
                save=True,
                default_name="jury.json",
                file_types=("JSON files (*.json)", "All files (*.*)"),
            )
        if not path:
            return {"ok": False, "msg": "Cancelled"}
        try:
            save_state(self, path)
        except OSError as e:
            return {"ok": False, "msg": f"Could not write file: {e}"}
        self._last_save_path = path
        return {"ok": True, "msg": f"Saved → {os.path.basename(path)}",
                "state": self.get_state()}

    def save_as(self) -> dict[str, Any]:
        return self.save(save_as=True)

    def upload_csv(self) -> dict[str, Any]:
        from .fileio import import_csv
        path = self._file_dialog(
            save=False,
            file_types=("CSV files (*.csv)", "All files (*.*)"),
        )
        if not path:
            return {"ok": False, "msg": "Cancelled"}
        try:
            added = import_csv(self, path)
        except (OSError, ValueError) as e:
            return {"ok": False, "msg": f"Could not import CSV: {e}"}
        return {"ok": True,
                "msg": f"Imported {added} juror{'s' if added != 1 else ''} from {os.path.basename(path)}",
                "state": self.get_state()}

    def export_pdf(self, title: str = "Jury Selection Report") -> dict[str, Any]:
        from . import pdf as _pdf
        path = self._file_dialog(
            save=True,
            default_name="jury_report.pdf",
            file_types=("PDF files (*.pdf)", "All files (*.*)"),
        )
        if not path:
            return {"ok": False, "msg": "Cancelled"}
        try:
            _pdf.export(self, path, title or "Jury Selection Report")
        except ImportError:
            return {"ok": False, "msg":
                    "PDF export needs the 'reportlab' package. "
                    "Install with: pip install reportlab, then restart."}
        except Exception as e:
            return {"ok": False, "msg": f"PDF export failed: {e}"}
        return {"ok": True, "msg": f"Exported PDF → {os.path.basename(path)}"}

    def _file_dialog(self, *, save: bool, default_name: str = "",
                     file_types: tuple[str, ...] = ()) -> str | None:
        """Open a pywebview file dialog; return the chosen path or None."""
        if self._window is None:
            return None
        import webview as pywebview
        kind = pywebview.SAVE_DIALOG if save else pywebview.OPEN_DIALOG
        kw: dict[str, Any] = {"directory": self._work_dir}
        if save and default_name:
            kw["save_filename"] = default_name
        if file_types:
            kw["file_types"] = file_types
        result = self._window.create_file_dialog(kind, **kw)
        if not result:
            return None
        path = result if isinstance(result, str) else result[0]
        try:
            self._work_dir = os.path.dirname(path) or self._work_dir
        except Exception:
            pass
        return path

    # ── Preferences ───────────────────────────────────────────────────────

    def get_settings(self) -> dict[str, Any]:
        """Return the current editable settings plus the choice-list
        constants the UI needs to render dropdowns."""
        from . import settings as _s
        return {
            "values":      _s.snapshot(),
            "page_sizes":  list(_s.PAGE_SIZE_CHOICES),
            "pdf_fonts":   list(_s.PDF_FONT_CHOICES),
            "rte_fonts":   list(_s.RTE_FONT_CHOICES),
            "corners":     list(_s.CORNER_CHOICES),
        }

    def update_settings(self, patch: dict[str, Any]) -> dict[str, Any]:
        """Persist a patch dict.  If autosave-related keys changed, the
        autosaver is restarted with the new interval."""
        from . import settings as _s
        from .fileio import Autosaver

        prev_interval = _s.autosave_interval_min()
        prev_keep     = _s.autosave_keep()
        prev_workdir  = _s.work_dir()

        values = _s.update(patch)

        # If work_dir changed, follow it.
        new_workdir = _s.work_dir()
        if new_workdir != prev_workdir:
            self.set_work_dir(new_workdir)

        # Restart autosave if interval / keep / workdir changed.
        new_interval = _s.autosave_interval_min()
        new_keep     = _s.autosave_keep()
        autosave_dirty = (new_interval != prev_interval or
                          new_keep != prev_keep or
                          new_workdir != prev_workdir)
        if autosave_dirty:
            if self._autosaver is not None:
                try:
                    self._autosaver.stop()
                except Exception:
                    pass
                self._autosaver = None
            if new_interval > 0:
                a = Autosaver(self, work_dir=new_workdir,
                              interval_min=new_interval, keep=new_keep)
                a.start()
                self._autosaver = a

        return {"ok": True, "values": values}

    def pick_work_dir(self) -> dict[str, Any]:
        """Native folder picker for the working directory setting."""
        if self._window is None:
            return {"ok": False, "msg": "No window"}
        import webview as pywebview
        result = self._window.create_file_dialog(
            pywebview.FOLDER_DIALOG,
            directory=self._work_dir,
        )
        if not result:
            return {"ok": False, "msg": "Cancelled"}
        path = result if isinstance(result, str) else result[0]
        return {"ok": True, "path": path}
