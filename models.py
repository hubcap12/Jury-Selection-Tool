from __future__ import annotations
import json

STATUS_DISPLAY = {
    "excused":     "Excused",
    "struck_def":  "Def. Strike",
    "struck_pro":  "Pro. Strike",
    "struck_both": "Both Struck",
}

DATE_FMTS = (
    "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%Y/%m/%d",
    "%m/%d/%y", "%m-%d-%y", "%B %d, %Y", "%b %d, %Y",
    "%d/%m/%Y", "%d-%m-%Y",
)


class Juror:
    _next = 1

    def __init__(self, name: str, age: str = "", notes: str = "",
                 keywords: str = "", jid: int | None = None):
        if jid is None:
            jid = Juror._next
            Juror._next += 1
        self.id       = jid
        self.name     = name
        self.age      = age
        self.notes    = notes
        self.keywords = keywords
        self.seat:    int | None = None
        self.is_alt:  bool       = False
        self.status:  str        = "pool"
        self.rating:  int        = 0
        self.panel:   int        = 0

    @property
    def label(self) -> str:
        return f"#{self.id}  {self.name}"

    def to_dict(self) -> dict:
        return dict(id=self.id, name=self.name, age=self.age, notes=self.notes,
                    keywords=self.keywords, seat=self.seat, is_alt=self.is_alt,
                    status=self.status, rating=self.rating, panel=self.panel)

    @classmethod
    def from_dict(cls, d: dict) -> "Juror":
        j = cls(d["name"], d.get("age", ""), d.get("notes", ""),
                d.get("keywords", ""), jid=d["id"])
        j.seat   = d.get("seat")
        j.is_alt = d.get("is_alt", False)
        j.status = d.get("status", "pool")
        j.rating = d.get("rating", 0)
        j.panel  = d.get("panel", 0)
        Juror._next = max(Juror._next, j.id + 1)
        return j
