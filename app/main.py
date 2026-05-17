from __future__ import annotations
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

from .colors import C, LIGHT
from .config import SETTINGS
from .fonts import FONTS, _init_fonts, _resource_path
from .models import Juror

from ._build        import BuildMixin
from ._settings_dlg import SettingsDlgMixin
from ._theme        import ThemeMixin
from ._panels       import PanelsMixin
from ._draw         import DrawMixin
from ._pool         import PoolMixin
from ._drag         import DragMixin
from ._detail       import DetailMixin
from ._crud         import CrudMixin
from ._fileio       import FileIOMixin


class JuryApp(
    tk.Tk,
    BuildMixin,
    SettingsDlgMixin,
    ThemeMixin,
    PanelsMixin,
    DrawMixin,
    PoolMixin,
    DragMixin,
    DetailMixin,
    CrudMixin,
    FileIOMixin,
):

    def __init__(self):
        super().__init__()
        self.title("Jury Selection Tool")
        self.minsize(820, 520)
        self.configure(bg=C["bg"])
        try:
            self.iconbitmap(_resource_path("icon.ico"))
        except Exception:
            pass

        self.jurors:      dict[int, Juror]        = {}
        self.panel_seats: list[dict]             = []
        self._active_panel: int                  = 0
        self.final_jury:  list[int]              = []
        self._fj_pos:     dict[int, int]         = {}

        self._theme_name:     str               = SETTINGS["theme"]
        if SETTINGS["theme"] == "light":
            C.update(LIGHT)
            self.configure(bg=C["bg"])
        self._corner:         str               = SETTINGS["corner"]
        _init_fonts(SETTINGS["font_size"])

        self.SW:   int = SETTINGS["seat_width"]
        self.SH:   int = SETTINGS["seat_height"]
        self.SGAP: int = SETTINGS["seat_gap"]

        self._ttk_style = ttk.Style(self)
        self._ttk_style.theme_use("clam")
        self._configure_scrollbar_style()

        self._autosave_id:    str | None        = None
        self._drag_id:        int | None        = None
        self._drag_source:    str | None        = None
        self._drag_seat_info: tuple | None      = None
        self._drag_win:       tk.Toplevel | None = None
        self._hovered:        tuple | None       = None
        self._selected_jid:       int | None        = None
        self._selected_final_jid: int | None        = None
        self._pool_ids:           list[int]          = []
        self._redraw_pending:     bool               = False
        self._det_notes_loaded:   str                = ""
        self._seat_geo:           dict | None        = None
        self._temp_zoom:          float | None       = None

        self._build_menu()
        self._build_ui()
        self.bind_all("<Button-1>", self._defocus_detail, "+")
        self._init_layout()
        self._schedule_autosave()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.withdraw()
        self._show_startup()
        self.deiconify()
        self.state("zoomed")
        self.after(200, lambda: self._apply_panel_positions(SETTINGS))

    def _on_close(self):
        if messagebox.askyesno(
            "Exit",
            "Exit the Jury Selection Tool?\n\nAny unsaved data will be lost.",
            icon="warning",
            default="no",
        ):
            if self._autosave_id is not None:
                self.after_cancel(self._autosave_id)
            self.destroy()

    def _show_startup(self):
        dlg = tk.Toplevel(self)
        dlg.title("Jury Selection Tool")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(bg=C["bg"])
        dlg.protocol("WM_DELETE_WINDOW", self.destroy)

        tk.Label(dlg, text="Jury Selection Tool",
                 font=FONTS["xxl_bold"], bg=C["bg"], fg=C["txt_dark"]
                 ).pack(pady=(36, 6), padx=50)
        tk.Label(dlg, text="How would you like to begin?",
                 font=FONTS["xl_reg"], bg=C["bg"], fg=C["txt_secondary"]
                 ).pack(pady=(0, 28))

        btn_kw = dict(font=FONTS["xl_reg"], relief="solid", bd=1,
                      highlightthickness=0, highlightbackground=C["bg"],
                      padx=20, pady=10, cursor="hand2", width=18)

        def pick_new():
            dlg.destroy()

        def pick_load():
            dlg.destroy()
            self._open()

        tk.Button(dlg, text="Start New Jury", command=pick_new,
                  bg=C["seat_seated"], fg=C["txt_light"],
                  activebackground=C["primary_active"], activeforeground=C["txt_light"],
                  **btn_kw).pack(pady=(0, 10), padx=50)
        tk.Button(dlg, text="Load from File…", command=pick_load,
                  bg=C["btn_bg"], fg=C["btn_fg"],
                  activebackground=C["btn_hover"], activeforeground=C["txt_light"],
                  **btn_kw).pack(pady=(0, 36), padx=50)

        dlg.update_idletasks()
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        w, h   = dlg.winfo_width(), dlg.winfo_height()
        dlg.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

        self.wait_window(dlg)
