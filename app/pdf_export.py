"""Standalone PDF export — all app state is passed in as arguments."""
from __future__ import annotations
import html
from datetime import datetime
from tkinter import filedialog, messagebox
from tkinter.simpledialog import askstring
import tkinter as tk

from .config import SETTINGS
from .richtext import _notes_to_rl_markup


def export_pdf(
    parent:      tk.Tk,
    rows_n:      int,
    cols_n:      int,
    jury_size:   int,
    jurors:      dict,
    panel_seats: list,
    final_jury:  list,
    fj_pos:      dict,
    work_dir:    str,
) -> None:
    try:
        from reportlab.lib.pagesizes import letter, A4, legal
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, PageBreak,
            Table, TableStyle, HRFlowable, KeepTogether,
        )
        from reportlab.lib.enums import TA_CENTER
    except ImportError:
        messagebox.showerror(
            "Missing Library",
            "PDF export requires the 'reportlab' package.\n\n"
            "Install it with:  pip install reportlab\n\nThen restart.",
        )
        return

    _ps_map  = {"Letter": letter, "A4": A4, "Legal": legal}
    pagesize = _ps_map.get(SETTINGS.get("pdf_page_size", "Letter"), letter)
    margin   = SETTINGS.get("pdf_margin", 0.75) * inch
    _pdf_fnt = SETTINGS.get("pdf_font", "Helvetica")
    fn_reg   = {"Helvetica": "Helvetica",      "Times": "Times-Roman",
                "Courier": "Courier"}[_pdf_fnt]
    fn_bold  = {"Helvetica": "Helvetica-Bold", "Times": "Times-Bold",
                "Courier": "Courier-Bold"}[_pdf_fnt]

    report_title = askstring(
        "Report Title",
        "Enter a title for this report:",
        initialvalue=SETTINGS.get("pdf_title", "") or "Jury Selection Report",
        parent=parent,
    )
    if report_title is None:
        return
    report_title = report_title.strip() or "Jury Selection Report"

    path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        initialdir=work_dir,
        initialfile=SETTINGS.get("pdf_filename", "jury_report.pdf") or "jury_report.pdf",
    )
    if not path:
        return

    rows_n = max(1, rows_n)
    cols_n = max(1, cols_n)

    # ── PDF colours ───────────────────────────────────────────────────────────
    BLUE   = colors.HexColor("#2d6dce")
    GREEN  = colors.HexColor("#2e7d4f")
    AGREEN = colors.HexColor("#6aab82")
    GREY   = colors.HexColor("#909090")
    RED    = colors.HexColor("#cc4444")
    DARK   = colors.HexColor("#111111")
    MID    = colors.HexColor("#555555")
    LIGHT  = colors.HexColor("#aaaaaa")
    BKGD   = colors.HexColor("#f2f3f7")
    DIV    = colors.HexColor("#c4cad8")

    # ── Paragraph styles ──────────────────────────────────────────────────────
    _sss = getSampleStyleSheet()

    def ps(name, **kw):
        return ParagraphStyle(name, parent=_sss["Normal"], **kw)

    s_title  = ps("t",  fontName=fn_bold, fontSize=20, textColor=DARK,
                  spaceAfter=10, leading=24)
    s_sub    = ps("su", fontName=fn_reg,  fontSize=9,  textColor=MID,
                  spaceAfter=10)
    s_sect   = ps("sc", fontName=fn_bold, fontSize=13, textColor=BLUE,
                  spaceBefore=12, spaceAfter=12)
    s_seat   = ps("sh", fontName=fn_bold, fontSize=10, textColor=DARK)
    s_badge  = ps("bd", fontName=fn_bold, fontSize=9,  textColor=colors.white,
                  alignment=TA_CENTER)
    s_detail = ps("dt", fontName=fn_reg,  fontSize=10, textColor=DARK)
    s_kw     = ps("kw", fontName=fn_reg,  fontSize=10, textColor=DARK)
    s_note   = ps("nt", fontName=fn_reg,  fontSize=10, textColor=DARK)
    s_empty  = ps("em", fontName=fn_reg,  fontSize=10, textColor=LIGHT)
    s_li     = ps("li", fontName=fn_reg,  fontSize=10, textColor=DARK,
                  leftIndent=14, spaceAfter=1)

    def esc(t):
        return html.escape(str(t))

    js = max(1, jury_size)

    def status_of(j, jid):
        fp = fj_pos.get(jid, 0)
        if fp and fp <= js:           return f"Final Juror #{fp}",    GREEN
        if fp:                        return f"Alternate #{fp - js}", AGREEN
        if j.status == "excused":     return "Excused",               GREY
        if j.status == "struck_def":  return "Defense Strike",        RED
        if j.status == "struck_pro":  return "Prosecution Strike",    RED
        if j.status == "struck_both": return "Both Strike",           RED
        return "Seated", BLUE

    W  = pagesize[0] - 2 * margin
    CW = [W - 1.45 * inch, 1.45 * inch]

    s_panel = ps("pn", fontName=fn_bold, fontSize=12, textColor=BLUE,
                 spaceBefore=14, spaceAfter=4)

    def seat_block(sn, j, jid, panel_idx):
        stat, col = status_of(j, jid)
        trows = [
            [Paragraph(
                f"Panel {panel_idx + 1}  ·  Seat {sn}  —  "
                f"{esc(j.name)},  Juror #{j.id}", s_seat),
             Paragraph(stat, s_badge)],
            [Paragraph(f"Age: {esc(j.age)}" if j.age else "", s_detail), ""],
        ]
        if j.keywords:
            trows.append(
                [Paragraph(f"Keywords:  {esc(j.keywords)}", s_kw), ""])
        notes_markup = _notes_to_rl_markup(j.notes)
        if notes_markup:
            trows.append(
                [Paragraph(f"Notes:  {notes_markup}", s_note), ""])
        nr = len(trows)
        t = Table(trows, colWidths=CW)
        t.setStyle(TableStyle([
            ("BOX",           (0, 0), (-1, -1), 0.5, DIV),
            ("LINEBELOW",     (0, 0), (-1,  0), 0.5, DIV),
            ("BACKGROUND",    (0, 0), (-1,  0), BKGD),
            ("BACKGROUND",    (1, 0), ( 1,  0), col),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            *[("SPAN", (0, i), (1, i)) for i in range(1, nr)],
        ]))
        return KeepTogether([t, Spacer(1, 6)])

    # ── Collect summary data ──────────────────────────────────────────────────
    fj, alt, exc, sdef, spro, sboth, pool = [], [], [], [], [], [], []
    for pos, jid in enumerate(final_jury, 1):
        j = jurors.get(jid)
        if not j:
            continue
        loc  = (f"Panel {j.panel + 1}, Seat {j.seat}" if j.seat
                else "unseated")
        line = f"{esc(j.name)}  (Juror #{j.id}, {loc})"
        if pos <= js:
            fj.append(f"{pos}.  {line}")
        else:
            alt.append(f"Alt {pos - js}.  {line}")

    for j in sorted(jurors.values(), key=lambda x: x.id):
        loc  = (f"Panel {j.panel + 1}, Seat {j.seat}" if j.seat else "unseated")
        line = f"{esc(j.name)}  (Juror #{j.id}, {loc})"
        if j.status == "excused":       exc.append(line)
        elif j.status == "struck_def":  sdef.append(line)
        elif j.status == "struck_pro":  spro.append(line)
        elif j.status == "struck_both": sboth.append(line)
        elif j.status == "pool":
            pool.append(f"{esc(j.name)}  (Juror #{j.id})")

    # ── Build story ───────────────────────────────────────────────────────────
    story = []

    def summ(title, items, col):
        story.append(Paragraph(
            title, ps(f"h{title[:4]}", fontName=fn_bold, fontSize=11,
                      textColor=col, spaceBefore=8, spaceAfter=3)))
        for it in items:
            story.append(Paragraph(f"• {it}", s_li))
        if not items:
            story.append(Paragraph("None", s_note))

    if SETTINGS.get("pdf_summary", True):
        story.append(Paragraph(esc(report_title), s_title))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y  ·  %I:%M %p')}",
            s_sub))
        story.append(HRFlowable(width="100%", thickness=2,
                                color=BLUE, spaceAfter=10))
        story.append(Paragraph("Summary", s_sect))
        summ("Final Jury",         fj,    GREEN)
        summ("Alternates",         alt,   AGREEN)
        summ("Excused",            exc,   GREY)
        summ("Defense Struck",     sdef,  RED)
        summ("Prosecution Struck", spro,  RED)
        summ("Both Struck",        sboth, RED)
        summ("Preliminary Pool",   pool,  BLUE)
        story.append(PageBreak())

    story.append(Paragraph(esc(report_title), s_title))
    story.append(HRFlowable(width="100%", thickness=2,
                            color=BLUE, spaceAfter=10))
    story.append(Paragraph("Juror Pool — By Panel & Seat", s_sect))
    for pi, panel in enumerate(panel_seats):
        story.append(Paragraph(f"Panel {pi + 1}", s_panel))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=DIV, spaceAfter=6))
        for sn in range(1, rows_n * cols_n + 1):
            jid = panel.get(sn)
            j   = jurors.get(jid) if jid else None
            if j:
                story.append(seat_block(sn, j, jid, pi))
            elif not SETTINGS.get("pdf_hide_empty", False):
                story.append(Paragraph(f"Seat {sn}  —  empty", s_empty))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    try:
        doc = SimpleDocTemplate(
            path, pagesize=pagesize,
            leftMargin=margin, rightMargin=margin,
            topMargin=margin, bottomMargin=margin,
            title=report_title,
        )
        doc.build(story)
    except Exception as e:
        messagebox.showerror("Export Failed", f"Could not write PDF:\n{e}")
        return

    messagebox.showinfo("Exported", f"PDF saved to:\n{path}")
