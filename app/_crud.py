from __future__ import annotations
import csv
from datetime import date, datetime
import tkinter as tk
from tkinter import filedialog, messagebox

from .models import Juror, DATE_FMTS
from .richtext import JurorDialog


class CrudMixin:

    def _upload_csv(self):
        path = filedialog.askopenfilename(
            title="Select Juror CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=self._work_dir(),
        )
        if not path:
            return

        def parse_dob(raw):
            for fmt in DATE_FMTS:
                try:
                    return datetime.strptime(raw.strip(), fmt).date()
                except ValueError:
                    pass
            return None

        def calc_age(dob):
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))
        except Exception as e:
            messagebox.showerror("CSV Error", f"Could not read file:\n{e}")
            return

        if not rows:
            messagebox.showerror("CSV Error", "The file is empty.")
            return

        start = 0
        if len(rows[0]) >= 2 and parse_dob(rows[0][1]) is None:
            start = 1

        errors, added = [], 0
        for i, row in enumerate(rows[start:], start + 1):
            if not row or not any(c.strip() for c in row):
                continue
            if len(row) < 2:
                errors.append(f"Row {i}: expected at least 2 columns (name, DOB)")
                continue
            name = row[0].strip()
            dob_raw = row[1].strip()
            if not name:
                errors.append(f"Row {i}: name is empty")
                continue
            dob = parse_dob(dob_raw)
            if dob is None:
                errors.append(f"Row {i}: unrecognized date \"{dob_raw}\"")
                continue
            j = Juror(name, str(calc_age(dob)))
            self.jurors[j.id] = j
            added += 1

        self._refresh()

        if errors:
            preview = "\n".join(errors[:10])
            if len(errors) > 10:
                preview += f"\n…and {len(errors) - 10} more"
            messagebox.showwarning(
                "CSV Import",
                f"Added {added} juror(s) to the pool.\n\nRows with issues:\n{preview}",
            )
        else:
            messagebox.showinfo("CSV Import", f"Added {added} juror(s) to the pool.")

    def _auto_seat(self):
        pool_jids = [jid for jid in self._pool_ids
                     if self.jurors.get(jid) and self.jurors[jid].status == "pool"]
        empty_seats = sorted(sn for sn, jid in self.seats.items() if jid is None)

        if not pool_jids:
            messagebox.showinfo("Auto Seat", "No jurors in the preliminary pool.")
            return
        if not empty_seats:
            messagebox.showinfo("Auto Seat", "No empty seats available.")
            return

        for jid, seat_num in zip(pool_jids, empty_seats):
            j = self.jurors[jid]
            j.seat, j.status, j.panel = seat_num, "seated", self._active_panel
            self.seats[seat_num] = jid

        seated = min(len(pool_jids), len(empty_seats))
        self._refresh()
        self.status.set(f"Auto-seated {seated} juror(s).")

    def _add(self):
        dlg = JurorDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            j = Juror(dlg.out_name, dlg.out_age, dlg.out_notes, dlg.out_keywords)
            self.jurors[j.id] = j
            self._refresh_pool()
            self.status.set(f"Added {j.name}.")

    def _edit_selected(self, _=None):
        sel = self.pool_lb.curselection()
        if not sel:
            return
        j = self._pool_juror(sel[0])
        if j:
            self._edit_by_id(j.id)

    def _edit_by_id(self, jid: int):
        j = self.jurors.get(jid)
        if not j:
            return
        dlg = JurorDialog(self, j)
        self.wait_window(dlg)
        if dlg.result:
            j.name, j.age, j.notes, j.keywords = dlg.out_name, dlg.out_age, dlg.out_notes, dlg.out_keywords
            self._refresh()

    def _remove(self):
        sel = self.pool_lb.curselection()
        if not sel:
            messagebox.showinfo("Remove", "Select a juror in the pool first.")
            return
        j = self._pool_juror(sel[0])
        if j and messagebox.askyesno("Remove", f"Remove {j.name} from this case?"):
            del self.jurors[j.id]
            self._refresh_pool()

    def _return_to_pool(self, jid: int, num: int):
        self.seats[num] = None
        j = self.jurors.get(jid)
        if j:
            j.seat, j.is_alt, j.status, j.panel = None, False, "pool", 0
        if jid in self.final_jury:
            self.final_jury.remove(jid)
        self._refresh()

    def _set_status(self, jid: int, status: str):
        j = self.jurors.get(jid)
        if not j:
            return
        if jid in self.final_jury:
            self.final_jury.remove(jid)
        j.status = status
        self.status.set(f"{j.name} marked {status}.")
        self._refresh()
