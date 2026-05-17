"""JavaScript-facing API.

Every public method here is callable from the UI as
``window.pywebview.api.method_name(...)`` and returns a JSON-serialisable
result.  Keep return shapes stable — the JS side ships these as state.

In Stage 1, only ``get_state`` / ``set_active_panel`` / ``set_theme`` /
``select_seat`` are wired through.  The rest are stubs that return a
friendly "coming soon" payload so the toolbar feels alive.
"""
from __future__ import annotations

from typing import Any


class JuryAPI:
    def __init__(self) -> None:
        # In-memory state.  Real persistence comes back in Stage 3 once the
        # existing app/_fileio.py is wired in.
        self.jurors: list[dict[str, Any]] = []
        self.grid: dict[str, Any] = {"rows": 4, "cols": 7, "jury_size": 12, "corner": "TL"}
        self.active_panel: int = 1
        self.selected_seat: int | None = None
        self.selected_final: int | None = None
        self.theme: str = "dark"
        self._window = None  # set by app.run()

    def _bind_window(self, window) -> None:
        self._window = window

    # ── State -------------------------------------------------------------

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

    # ── Window controls (called from the faux title bar) ----------------

    def minimize(self) -> None:
        if self._window is not None:
            self._window.minimize()

    def toggle_maximize(self) -> None:
        if self._window is not None:
            self._window.toggle_fullscreen()

    def exit_app(self) -> None:
        if self._window is not None:
            self._window.destroy()

    # ── File menu (Stage 2+ stubs) --------------------------------------

    def open_file(self) -> dict[str, str]:
        return {"ok": False, "msg": "Open — wiring up in Stage 3"}

    def save(self) -> dict[str, str]:
        return {"ok": False, "msg": "Save — wiring up in Stage 3"}

    def export_pdf(self) -> dict[str, str]:
        return {"ok": False, "msg": "Export PDF — wiring up in Stage 3"}
