"""JSON save/load + CSV import + autosave for the webview UI.

Stays bit-for-bit compatible with the original Tkinter app's
``.json`` format (see ``app/_fileio.py``), so files round-trip between
both UIs.  Two conversions are needed because the webview API uses a
slightly different in-memory shape:

  • Panels — Tk app is 0-indexed; webview API is 1-indexed.  We
    convert on save/load.
  • Final-jury order — Tk app stores an ordered ``final_jury`` list
    of juror IDs; webview API stores ``finalNo`` on each juror dict.
    We translate both directions.
"""
from __future__ import annotations

import csv
import json
import os
import threading
from typing import Any


# ── JSON save/load ────────────────────────────────────────────────────────────

def build_save_data(api) -> dict[str, Any]:
    """Produce the Tk-compatible dict.  Mirrors
    ``app/_fileio.FileIOMixin._build_save_data``."""
    num_panels = max(
        (j.get("panel", 0) for j in api.jurors),
        default=api.active_panel,
    )
    num_panels = max(1, num_panels)

    # Build ordered final-jury list from finalNo.
    finals = [j for j in api.jurors if j.get("status") == "final"]
    finals.sort(key=lambda j: j.get("finalNo", 999))
    final_jury = [j["id"] for j in finals]

    jurors_out = []
    for j in api.jurors:
        jurors_out.append({
            "id":       j["id"],
            "name":     j["name"],
            "age":      str(j.get("age", "")),   # Tk app stores age as string
            "notes":    j.get("notes", ""),
            "keywords": j.get("keywords", ""),
            "seat":     j.get("seat"),
            "is_alt":   False,
            "status":   j.get("status", "pool"),
            "rating":   j.get("rating", 0),
            "panel":    max(0, (j.get("panel") or 1) - 1),  # 1→0 indexed
        })

    return {
        "rows":         api.grid["rows"],
        "cols":         api.grid["cols"],
        "jury_size":    api.grid["jury_size"],
        "corner":       api.grid.get("corner", "TL"),
        "num_panels":   num_panels,
        "active_panel": max(0, api.active_panel - 1),  # 1→0 indexed
        "final_jury":   final_jury,
        "jurors":       jurors_out,
        "theme":        api.theme,
        "zoom":         1.0,
    }


def save_state(api, path: str) -> None:
    """Write current api state to ``path``.  Raises OSError on failure."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(build_save_data(api), f, indent=2)


def load_state(api, path: str) -> None:
    """Read ``path`` and replace api state.  Raises on failure."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Not a valid jury file (root must be a JSON object)")

    api.grid = {
        "rows":      int(data.get("rows", 4)),
        "cols":      int(data.get("cols", 7)),
        "jury_size": int(data.get("jury_size", 12)),
        "corner":    data.get("corner", "TL"),
    }
    api.active_panel = max(1, int(data.get("active_panel", 0)) + 1)  # 0→1 indexed
    api.theme = data.get("theme", api.theme)

    raw_jurors = data.get("jurors", [])
    final_jury = data.get("final_jury", []) or []

    # finalNo lookup so we can re-attach order on loaded jurors.
    final_pos = {jid: i + 1 for i, jid in enumerate(final_jury)}

    new_jurors: list[dict[str, Any]] = []
    for d in raw_jurors:
        if not isinstance(d, dict) or "id" not in d:
            continue
        jid = int(d["id"])
        # Coerce age — accept either string or int from disk.
        age = d.get("age", "")
        try:
            age = int(age) if str(age).strip() else 0
        except (TypeError, ValueError):
            age = 0
        status = d.get("status", "pool")
        # Old format may have used 'struck' as a status; normalise.
        if status == "struck":
            status = "struck_def"

        juror = {
            "id":       jid,
            "name":     d.get("name", ""),
            "age":      age,
            "notes":    d.get("notes", ""),
            "keywords": d.get("keywords", ""),
            "status":   status,
            "rating":   int(d.get("rating", 0) or 0),
            "panel":    int(d.get("panel", 0)) + 1,  # 0→1 indexed
            "seat":     d.get("seat"),
        }
        if jid in final_pos:
            juror["status"] = "final"
            juror["finalNo"] = final_pos[jid]
        new_jurors.append(juror)

    api.jurors = new_jurors
    api.selected_seat = None
    api.selected_final = None


# ── CSV import ────────────────────────────────────────────────────────────────

_DOB_HEADERS = {"dob", "date of birth", "birthdate", "birth date", "born",
                "birth", "date_of_birth", "dateofbirth"}
_DOB_FORMATS = ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y",
                "%m/%d/%y", "%d-%m-%Y", "%B %d, %Y", "%b %d, %Y")


def _age_from_dob(dob_str: str) -> int:
    """Return current age in whole years from a date-of-birth string."""
    from datetime import date, datetime
    dob_str = dob_str.strip()
    if not dob_str:
        return 0
    for fmt in _DOB_FORMATS:
        try:
            dob = datetime.strptime(dob_str, fmt).date()
            today = date.today()
            return max(0, today.year - dob.year
                       - ((today.month, today.day) < (dob.month, dob.day)))
        except ValueError:
            continue
    return 0


def import_csv(api, path: str) -> int:
    """Append jurors from a CSV file to the pool.  Returns the count added.

    Accepted column orderings (auto-detected from header row, if any):
      • ``name``                         — name only
      • ``name, age``                    — name + age (integer)
      • ``name, dob``                    — name + date of birth (calculated)
      • ``name, age, keywords``
      • ``name, age, keywords, notes``
    Lines starting with ``#`` are ignored as comments.
    """
    added = 0
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if r and r[0].strip() and not r[0].lstrip().startswith("#")]
    if not rows:
        return 0

    # Detect header and column roles.
    first = [c.strip().lower() for c in rows[0]]
    has_header = first and first[0] in ("name", "juror", "full name", "first")
    col2_is_dob = has_header and len(first) > 1 and first[1] in _DOB_HEADERS
    body = rows[1:] if has_header else rows

    for row in body:
        if not row:
            continue
        name = row[0].strip()
        if not name:
            continue
        raw2     = row[1].strip() if len(row) > 1 else ""
        age      = str(_age_from_dob(raw2)) if col2_is_dob else raw2
        keywords = row[2].strip() if len(row) > 2 else ""
        notes    = row[3].strip() if len(row) > 3 else ""
        api.add_juror(name=name, age=age, notes=notes, keywords=keywords)
        added += 1
    return added


# ── Autosave ──────────────────────────────────────────────────────────────────

class Autosaver:
    """Periodic rotating autosave.  Same scheme as
    ``app/_fileio.FileIOMixin._autosave``: every ``interval_min`` minutes,
    write ``autosave_1.json`` and shift older snapshots up to
    ``autosave_<keep>.json`` (deleting the oldest).
    """

    def __init__(self, api, work_dir: str,
                 interval_min: int = 15, keep: int = 3) -> None:
        self.api = api
        self.work_dir = work_dir
        self.interval = max(1, int(interval_min)) * 60
        self.keep = max(1, int(keep))
        self._timer: threading.Timer | None = None
        self._stopped = False

    def start(self) -> None:
        self._schedule()

    def stop(self) -> None:
        self._stopped = True
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _schedule(self) -> None:
        if self._stopped:
            return
        self._timer = threading.Timer(self.interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        if self._stopped:
            return
        try:
            if self.api.jurors:
                self._rotate_and_save()
        except Exception as e:
            # Never crash the timer thread — autosave failure is silent.
            print(f"[autosave] failed: {e}")
        self._schedule()

    def _rotate_and_save(self) -> None:
        d = self.work_dir
        os.makedirs(d, exist_ok=True)
        oldest = os.path.join(d, f"autosave_{self.keep}.json")
        if os.path.exists(oldest):
            os.remove(oldest)
        for i in range(self.keep - 1, 0, -1):
            src = os.path.join(d, f"autosave_{i}.json")
            dst = os.path.join(d, f"autosave_{i + 1}.json")
            if os.path.exists(src):
                os.replace(src, dst)
        save_state(self.api, os.path.join(d, "autosave_1.json"))
