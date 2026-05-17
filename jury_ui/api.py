"""JavaScript-facing API.

Every public method here is callable from the UI as
``window.pywebview.api.method_name(...)`` and returns a JSON-serialisable
result.

Mutating methods return ``{"ok": True, "state": <full state>}`` so the
UI can replace its local state in one shot — keeps the bridge contract
trivial and idempotent.
"""
from __future__ import annotations

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

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def _bind_window(self, window) -> None:
        self._window = window

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
        return {
            "jurors":         self.jurors,
            "grid":           self.grid,
            "active_panel":   self.active_panel,
            "selected_seat":  self.selected_seat,
            "selected_final": self.selected_final,
            "theme":          self.theme,
        }

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

    def add_juror(self, name: str, age: int | str = 0,
                  notes: str = "", keywords: str = "") -> dict[str, Any]:
        name = (name or "").strip()
        if not name:
            return {"ok": False, "msg": "Name is required"}
        try:
            age_i = int(age) if age != "" else 0
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
                        v = int(v) if v != "" else 0
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

    # ── Stage 3 stubs ─────────────────────────────────────────────────────

    def open_file(self) -> dict[str, str]:
        return {"ok": False, "msg": "Open — wiring up in Stage 3"}

    def save(self) -> dict[str, str]:
        return {"ok": False, "msg": "Save — wiring up in Stage 3"}

    def export_pdf(self) -> dict[str, str]:
        return {"ok": False, "msg": "Export PDF — wiring up in Stage 3"}
