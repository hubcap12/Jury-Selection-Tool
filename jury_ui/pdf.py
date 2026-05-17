"""Adapter that calls ``app.pdf_export._render_pdf`` with data converted
from the webview API's juror-dict format into the Tk app's Juror-model
format that the renderer expects."""
from __future__ import annotations

from typing import Any

from app.models import Juror
from app.pdf_export import _render_pdf


def export(api, path: str, title: str) -> None:
    """Render the current api state to ``path`` with ``title``.

    Raises whatever the underlying renderer raises (ImportError if
    reportlab is missing, OSError on write failure, etc.) — caller
    is responsible for surfacing the message to the user.
    """
    rows = int(api.grid["rows"])
    cols = int(api.grid["cols"])
    jury_size = int(api.grid["jury_size"])

    # Convert juror dicts → Juror model instances.
    jurors_model: dict[int, Juror] = {}
    for d in api.jurors:
        j = Juror(
            name=d.get("name", ""),
            age=str(d.get("age", "")),
            notes=d.get("notes", ""),
            keywords=d.get("keywords", ""),
            jid=int(d["id"]),
        )
        j.seat   = d.get("seat")
        j.is_alt = False
        j.status = d.get("status", "pool")
        j.rating = int(d.get("rating", 0) or 0)
        # Tk model uses 0-indexed panels; api uses 1-indexed.
        j.panel  = max(0, int(d.get("panel") or 1) - 1)
        jurors_model[j.id] = j

    # Build panel_seats: list of dict[seat_no, juror_id]
    num_panels = max(
        (j.panel for j in jurors_model.values()),
        default=max(0, api.active_panel - 1),
    ) + 1
    num_panels = max(1, num_panels)
    capacity = rows * cols
    empty_panel = {sn: None for sn in range(1, capacity + 1)}
    panel_seats: list[dict[int, int | None]] = [dict(empty_panel) for _ in range(num_panels)]
    for j in jurors_model.values():
        if j.seat is not None and 1 <= j.seat <= capacity:
            panel_seats[j.panel][j.seat] = j.id

    # Final jury list (ordered by finalNo on each juror dict).
    finals = [d for d in api.jurors if d.get("status") == "final"]
    finals.sort(key=lambda d: d.get("finalNo", 999))
    final_jury = [int(d["id"]) for d in finals]
    fj_pos: dict[int, int] = {int(d["id"]): i + 1 for i, d in enumerate(finals)}

    _render_pdf(
        path        = path,
        title       = title,
        rows_n      = rows,
        cols_n      = cols,
        jury_size   = jury_size,
        jurors      = jurors_model,
        panel_seats = panel_seats,
        final_jury  = final_jury,
        fj_pos      = fj_pos,
    )
