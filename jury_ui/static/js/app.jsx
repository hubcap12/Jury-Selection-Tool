/* Main JuryApp — wires everything together.
   In pywebview mode: state comes from Python via window.pywebview.api.
   In browser mode (file://): falls back to sample data in data.js. */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "accent": "#4f8cff",
  "density": "cozy",
  "radius": 8,
  "fontStack": "segoe"
}/*EDITMODE-END*/;

const ACCENTS = [
  "#4f8cff",
  "#7a5cff",
  "#c46a3a",
  "#3f8a73",
];

const FONT_STACKS = {
  segoe:    `"Segoe UI Variable Display","Segoe UI Variable","Segoe UI",system-ui,sans-serif`,
  inter:    `"Inter Tight","Inter",system-ui,sans-serif`,
  georgia:  `"Georgia","Times New Roman",serif`,
};

/* ── Python bridge -------------------------------------------------------- */

const py = {
  ready: new Promise((resolve) => {
    if (window.pywebview && window.pywebview.api) {
      resolve(window.pywebview.api);
    } else {
      window.addEventListener("pywebviewready", () => resolve(window.pywebview.api));
      // After a short window, give up and resolve null — pywebview isn't here.
      setTimeout(() => { if (!window.pywebview) resolve(null); }, 300);
    }
  }),
};

async function loadInitialState() {
  const api = await py.ready;
  if (api) {
    try { return await api.get_state(); } catch (e) { console.warn("get_state failed", e); }
  }
  // Browser fallback — sample data from data.js
  return {
    jurors: window.JURORS,
    grid:   window.SEAT_GRID,
    active_panel: 1,
    selected_seat: window.SELECTED_SEAT_ID,
    selected_final: 7,
  };
}

async function pyCall(method, ...args) {
  const api = await py.ready;
  if (!api || typeof api[method] !== "function") return null;
  try { return await api[method](...args); } catch (e) { console.warn(method, "failed", e); return null; }
}

/* ── App ------------------------------------------------------------------ */

function JuryApp() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  const [jurors, setJurors]                = React.useState([]);
  const [rows, setRows]                    = React.useState(4);
  const [cols, setCols]                    = React.useState(7);
  const [jurySize, setJurySize]            = React.useState(12);
  const [corner, setCorner]                = React.useState("TL");
  const [activePanel, setActivePanel]      = React.useState(1);
  const [numPanels, setNumPanels]          = React.useState(3);
  const [selectedSeat, setSelectedSeat]    = React.useState(null);
  const [selectedJid, setSelectedJid]      = React.useState(null);
  const [selectedFinal, setSelectedFinal]  = React.useState(null);
  const [toast, setToast]                  = React.useState(null);
  const [modal, setModal]                  = React.useState(null); // {kind: 'add'|'edit'|'confirmRemove', juror?}
  const [ctxMenu, setCtxMenu]              = React.useState(null); // {juror, x, y}
  const [leftWidth, setLeftWidth]          = React.useState(280);
  const [rightWidth, setRightWidth]        = React.useState(280);
  const [detailHeight, setDetailHeight]    = React.useState(340);
  const [leftFracs, setLeftFracs]          = React.useState([1.4, 0.7, 0.7, 0.7, 0.5]);
  const [rightFracs, setRightFracs]        = React.useState([1.3, 1.0]);

  // Initial state from Python (or sample fallback).
  React.useEffect(() => {
    loadInitialState().then(s => {
      if (!s) return;
      setJurors(s.jurors || []);
      if (s.grid) {
        setRows(s.grid.rows || 4);
        setCols(s.grid.cols || 7);
        setJurySize(s.grid.jurySize || s.grid.jury_size || 12);
        if (s.grid.corner) setCorner(s.grid.corner);
      }
      if (s.active_panel)    setActivePanel(s.active_panel);
      if (s.num_panels)      setNumPanels(s.num_panels);
      if (s.left_col_width)  setLeftWidth(s.left_col_width);
      if (s.right_col_width) setRightWidth(s.right_col_width);
      if (s.detail_height)   setDetailHeight(s.detail_height);
      if (Array.isArray(s.left_fracs)  && s.left_fracs.length)  setLeftFracs(s.left_fracs);
      if (Array.isArray(s.right_fracs) && s.right_fracs.length) setRightFracs(s.right_fracs);
      if (s.selected_seat) setSelectedSeat(s.selected_seat);
      if (s.selected_final) setSelectedFinal(s.selected_final);
    });
  }, []);

  const selectedJuror = React.useMemo(() => {
    if (selectedJid != null) return jurors.find(j => j.id === selectedJid);
    return jurors.find(j => j.seat === selectedSeat && j.panel === activePanel);
  }, [jurors, selectedJid, selectedSeat, activePanel]);

  // Derived indices — computed once per `jurors` change so the sidebars,
  // status bar, and seat grid don't each re-scan the full list on every
  // render.  `byStatus` buckets the array; `byPanelSeat` indexes seated
  // jurors by (panel, seat) so SeatGrid doesn't rebuild its lookup each
  // render either.
  const byStatus = React.useMemo(() => {
    const m = {
      pool: [], seated: [], excused: [],
      struck_def: [], struck_pro: [], struck_both: [], final: [],
    };
    for (const j of jurors) {
      const bucket = m[j.status];
      if (bucket) bucket.push(j);
    }
    m.final.sort((a, b) => (a.finalNo || 999) - (b.finalNo || 999));
    return m;
  }, [jurors]);

  // Tile lookup for the active panel.  Keys are seat numbers; values are the
  // juror occupying that seat.
  const activePanelBySeat = React.useMemo(() => {
    const m = {};
    for (const j of jurors) {
      if (j.seat && j.panel === activePanel) m[j.seat] = j;
    }
    return m;
  }, [jurors, activePanel]);

  const struckCount =
    byStatus.struck_def.length +
    byStatus.struck_pro.length +
    byStatus.struck_both.length;

  // Apply mutation results from Python.  Fast path: if the server returned
  // a `jurors_patch` (the changed juror records only), splice them into the
  // local array by id.  Falls back to full-state replacement when the server
  // sent `state` instead (used for actions that touch many jurors — load,
  // reset, auto_seat, unmark_final, etc.).
  //
  // useCallback([]) is safe here because every value we touch is either a
  // stable state setter or a property of `r` (the argument).
  const applyResult = React.useCallback((r) => {
    if (!r) return;
    if (r.jurors_patch && r.jurors_patch.length) {
      const patch = new Map();
      for (const j of r.jurors_patch) patch.set(j.id, j);
      setJurors(prev => prev.map(j => patch.get(j.id) || j));
    }
    if (r.state) {
      setJurors(r.state.jurors || []);
      if (r.state.grid) {
        setRows(r.state.grid.rows || 4);
        setCols(r.state.grid.cols || 7);
        setJurySize(r.state.grid.jury_size || r.state.grid.jurySize || 12);
        if (r.state.grid.corner) setCorner(r.state.grid.corner);
      }
      if (r.state.active_panel) setActivePanel(r.state.active_panel);
    }
    // showToast captures setToast (stable) but is itself stable below too.
    if (r.msg) showToastRef.current(r.msg);
  }, []);

  // Stable ref to showToast so applyResult can call it without depending on
  // a fresh closure each render.  showToast itself is defined below.
  const showToastRef = React.useRef(null);

  // Handlers — all wrapped in useCallback so memoized children (Seat,
  // SeatGrid, LeftColumn, etc.) actually bail out of re-rendering when
  // their props are referentially stable.
  const handleSelectSeat = React.useCallback((seatNo) => {
    setSelectedSeat(seatNo);
    setSelectedJid(null);
    pyCall("select_seat", activePanel, seatNo);
  }, [activePanel]);

  const handleSelectJid = React.useCallback((jid) => {
    setSelectedJid(jid);
    // Read jurors via functional setter to avoid depending on the array
    // reference itself (which changes on every patch).
    setJurors(prev => {
      const j = prev.find(x => x.id === jid);
      if (j && j.seat) setSelectedSeat(j.seat);
      return prev;
    });
  }, []);

  // Drag a juror onto a seat — assigns or swaps.
  const handleDropOnSeat = React.useCallback(async (jid, seatNo) => {
    const r = await pyCall("assign_seat", jid, activePanel, seatNo);
    applyResult(r);
    setSelectedSeat(seatNo);
    setSelectedJid(null);
  }, [activePanel, applyResult]);

  // Drag a juror onto the Preliminary Pool pane — unseat.
  const handleUnseatDrop = React.useCallback(async (jid) => {
    applyResult(await pyCall("unseat", jid));
  }, [applyResult]);

  // Detail-panel handlers.
  const handleSetStatus = React.useCallback(async (jid, status) => {
    applyResult(await pyCall("set_status", jid, status));
  }, [applyResult]);
  const handleSetRating = React.useCallback(async (jid, rating) => {
    applyResult(await pyCall("set_rating", jid, rating));
  }, [applyResult]);
  const handleMarkFinal = React.useCallback(async (jid) => {
    applyResult(await pyCall("mark_final", jid));
  }, [applyResult]);
  const handleUnmarkFinal = React.useCallback(async (jid) => {
    applyResult(await pyCall("unmark_final", jid));
  }, [applyResult]);
  const handleSaveKeywords = React.useCallback(async (jid, kw) => {
    applyResult(await pyCall("set_keywords", jid, kw));
  }, [applyResult]);
  const handleSaveNotes = React.useCallback(async (jid, n) => {
    applyResult(await pyCall("set_notes", jid, n));
  }, [applyResult]);
  const handleUnseat = React.useCallback(async (jid) => {
    applyResult(await pyCall("unseat", jid));
  }, [applyResult]);

  const handleContextMenu = React.useCallback((juror, x, y) => {
    setCtxMenu({ juror, x, y });
  }, []);

  // Vertical drag for the detail (info) panel sash.
  const startDetailDrag = (e) => {
    e.preventDefault();
    const y0 = e.clientY;
    const h0 = detailHeight;
    const onMove = (ev) => {
      setDetailHeight(Math.max(120, Math.min(700, h0 - (ev.clientY - y0))));
    };
    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup",  onUp);
      document.body.style.cursor     = "";
      document.body.style.userSelect = "";
    };
    document.body.style.cursor     = "ns-resize";
    document.body.style.userSelect = "none";
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup",  onUp);
  };

  const startHDrag = (side, e) => {
    e.preventDefault();
    const x0 = e.clientX;
    const w0 = side === "left" ? leftWidth : rightWidth;
    const setter = side === "left" ? setLeftWidth : setRightWidth;
    const sign   = side === "left" ? 1 : -1;

    const onMove = (ev) => {
      setter(Math.max(160, Math.min(520, w0 + sign * (ev.clientX - x0))));
    };
    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup",  onUp);
      document.body.style.cursor     = "";
      document.body.style.userSelect = "";
    };
    document.body.style.cursor     = "ew-resize";
    document.body.style.userSelect = "none";
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup",  onUp);
  };

  // Left-column action buttons.  `selectedJuror` is referenced inside, so it
  // has to be a dep — accept the new identity when selection changes.  The
  // alternative would be a ref, but actions are rare enough that the cost
  // is negligible.
  const handleAction = React.useCallback(async (kind) => {
    switch (kind) {
      case "Add juror":
        setModal({ kind: "add" });
        return;
      case "Edit juror":
        if (!selectedJuror) { showToast("Select a juror first"); return; }
        setModal({ kind: "edit", juror: selectedJuror });
        return;
      case "Remove juror":
        if (!selectedJuror) { showToast("Select a juror first"); return; }
        setModal({ kind: "confirmRemove", juror: selectedJuror });
        return;
      case "Auto Seat": {
        const r = await pyCall("auto_seat");
        applyResult(r);
        showToast("Auto-seated pool jurors");
        return;
      }
      case "Reset":
        setModal({ kind: "confirmReset" });
        return;
      case "Save":
        applyResult(await pyCall("save"));
        return;
      case "Save As":
        applyResult(await pyCall("save_as"));
        return;
      case "Open":
        applyResult(await pyCall("open_file"));
        return;
      case "Upload CSV":
        applyResult(await pyCall("upload_csv"));
        return;
      case "Export PDF":
        setModal({ kind: "promptPdfTitle" });
        return;
      default:
        showToast(kind);
    }
  }, [selectedJuror, applyResult, showToast]);

  const handleSetPanel = React.useCallback((n) => {
    setActivePanel(n);
    pyCall("set_active_panel", n);
  }, []);

  // Suppress the browser's native context menu globally.
  React.useEffect(() => {
    const prevent = (e) => e.preventDefault();
    document.addEventListener("contextmenu", prevent);
    return () => document.removeEventListener("contextmenu", prevent);
  }, []);

  // Global keyboard shortcuts.
  React.useEffect(() => {
    const handler = (e) => {
      if (e.key === "F1") {
        e.preventDefault();
        setModal(m => m ? null : { kind: "help", tab: "quickstart" });
        return;
      }
      if (!e.ctrlKey && !e.metaKey) return;
      switch (e.key) {
        case "s": e.preventDefault(); e.shiftKey ? handleAction("Save As") : handleAction("Save"); break;
        case "o": e.preventDefault(); handleAction("Open"); break;
        case ",": e.preventDefault();
          pyCall("get_settings").then(s => { if (s) setModal({ kind: "prefs", initial: s }); });
          break;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Apply CSS vars from tweaks.  Theme is pushed to Python only when it
  // actually changes (was previously firing on every tweak edit — radius,
  // accent, density, etc. — which round-tripped the bridge for nothing).
  React.useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = t.theme;
    root.dataset.density = t.density;
    root.style.setProperty("--accent", t.accent);
    root.style.setProperty("--radius", t.radius + "px");
    root.style.setProperty("--radius-sm", Math.max(2, t.radius - 4) + "px");
    root.style.setProperty("--radius-lg", (t.radius + 4) + "px");
    root.style.setProperty("--font-ui", FONT_STACKS[t.fontStack] || FONT_STACKS.segoe);
  }, [t]);

  React.useEffect(() => {
    pyCall("set_theme", t.theme);
  }, [t.theme]);

  // Toast helper for "coming soon" actions in stage 1.
  const showToast = React.useCallback((msg) => {
    setToast(msg);
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => setToast(null), 2200);
  }, []);
  showToastRef.current = showToast;

  return (
    <div className="app-root">
      <MenuBar onCommand={(cmd) => {
        const handlers = {
          new:        () => setModal({ kind: "confirmReset" }),
          open:       () => handleAction("Open"),
          save:       () => handleAction("Save"),
          save_as:    () => handleAction("Save As"),
          export_pdf: () => handleAction("Export PDF"),
          upload_csv: () => handleAction("Upload CSV"),
          settings:   async () => {
                          const s = await pyCall("get_settings");
                          if (s) setModal({ kind: "prefs", initial: s });
                          else showToast("Preferences unavailable (no pywebview)");
                        },
          quickstart: () => setModal({ kind: "help", tab: "quickstart" }),
          shortcuts:  () => setModal({ kind: "help", tab: "shortcuts"  }),
          about:      () => setModal({ kind: "help", tab: "about"      }),
          exit:       () => pyCall("exit_app"),
        };
        (handlers[cmd] || (() => {}))();
      }}/>

      <div className="app-body">
        <LeftColumn
          byStatus={byStatus}
          selectedJid={selectedJuror?.id}
          onSelect={handleSelectJid}
          theme={t.theme}
          onToggleTheme={() => setTweak("theme", t.theme === "dark" ? "light" : "dark")}
          onAction={handleAction}
          onUnseatDrop={handleUnseatDrop}
          onJurorContextMenu={handleContextMenu}
          fracs={leftFracs} setFracs={setLeftFracs}
          style={{ width: leftWidth }}
        />

        <div className="hsash" onMouseDown={(e) => startHDrag("left", e)} />

        <main className="col col-center">
          <ControlBar
            rows={rows} cols={cols} jurySize={jurySize} corner={corner}
            setRows={(v) => { setRows(v); pyCall("set_grid", v, cols, jurySize, corner); }}
            setCols={(v) => { setCols(v); pyCall("set_grid", rows, v, jurySize, corner); }}
            setJurySize={(v) => { setJurySize(v); pyCall("set_grid", rows, cols, v, corner); }}
            setCorner={(v) => { setCorner(v); pyCall("set_grid", rows, cols, jurySize, v); }}
            activePanel={activePanel} setActivePanel={handleSetPanel}
            numPanels={numPanels}
            theme={t.theme} setTheme={v => setTweak("theme", v)}
          />

          <SeatGrid
            rows={rows}
            cols={cols}
            corner={corner}
            bySeat={activePanelBySeat}
            selectedSeat={selectedSeat}
            onSelectSeat={handleSelectSeat}
            onDropJuror={handleDropOnSeat}
            onJurorContextMenu={handleContextMenu}
          />

          <div className="sash sash-detail" onMouseDown={startDetailDrag} />

          <div className="detail-wrap" style={{ height: detailHeight }}>
            <DetailEditor
              juror={selectedJuror}
              panel={activePanel}
              onSaveKeywords={handleSaveKeywords}
              onSaveNotes={handleSaveNotes}
              onSetStatus={handleSetStatus}
              onSetRating={handleSetRating}
              onMarkFinal={handleMarkFinal}
              onUnmarkFinal={handleUnmarkFinal}
              onUnseat={handleUnseat}
            />
          </div>
        </main>

        <div className="hsash" onMouseDown={(e) => startHDrag("right", e)} />

        <RightColumn
          finals={byStatus.final}
          selectedFinalId={selectedFinal}
          onSelectFinal={setSelectedFinal}
          onJurorContextMenu={handleContextMenu}
          fracs={rightFracs} setFracs={setRightFracs}
          style={{ width: rightWidth }}
        />
      </div>

      <StatusBar byStatus={byStatus} struckCount={struckCount} activePanel={activePanel} numPanels={numPanels} selectedJid={selectedJuror?.id}/>

      <TweaksUI t={t} setTweak={setTweak}/>

      {toast && <div className="toast">{toast}</div>}

      {modal?.kind === "add" && (
        <JurorFormModal
          mode="add"
          onSubmit={async (fields) => {
            const r = await pyCall("add_juror", fields.name, fields.age, fields.notes, fields.keywords);
            applyResult(r);
            setModal(null);
            showToast("Added " + fields.name);
          }}
          onClose={() => setModal(null)}
        />
      )}
      {modal?.kind === "edit" && (
        <JurorFormModal
          mode="edit"
          initial={modal.juror}
          onSubmit={async (fields) => {
            const r = await pyCall("edit_juror", modal.juror.id, fields);
            applyResult(r);
            setModal(null);
          }}
          onClose={() => setModal(null)}
        />
      )}
      {modal?.kind === "confirmRemove" && (
        <ConfirmModal
          title="Remove juror"
          message={`Remove juror #${modal.juror.id} (${modal.juror.name}) from this jury? This cannot be undone.`}
          confirmLabel="Remove"
          danger
          onConfirm={async () => {
            const r = await pyCall("remove_juror", modal.juror.id);
            applyResult(r);
            setSelectedJid(null);
            showToast("Removed " + modal.juror.name);
          }}
          onClose={() => setModal(null)}
        />
      )}
      {modal?.kind === "confirmReset" && (
        <ConfirmModal
          title="Reset jury"
          message="Remove all jurors and clear seating? This cannot be undone."
          confirmLabel="Reset everything"
          danger
          onConfirm={async () => {
            const r = await pyCall("reset");
            applyResult(r);
            setSelectedSeat(null);
            setSelectedJid(null);
            showToast("Cleared all jurors");
          }}
          onClose={() => setModal(null)}
        />
      )}
      {modal?.kind === "promptPdfTitle" && (
        <PromptModal
          title="Export PDF"
          message="Report title:"
          defaultValue="Jury Selection Report"
          confirmLabel="Export…"
          placeholder="Jury Selection Report"
          onConfirm={async (val) => {
            applyResult(await pyCall("export_pdf", val));
          }}
          onClose={() => setModal(null)}
        />
      )}
      {modal?.kind === "help" && (
        <HelpModal
          initialTab={modal.tab}
          onClose={() => setModal(null)}
        />
      )}
      {modal?.kind === "prefs" && (
        <PreferencesModal
          initial={modal.initial}
          onSave={async (values) => {
            const r = await pyCall("update_settings", values);
            if (r?.ok) {
              showToast("Preferences saved");
              if (r.values?.num_panels != null) {
                const n = r.values.num_panels;
                setNumPanels(n);
                if (activePanel > n) setActivePanel(1);
              }
            } else {
              showToast(r?.msg || "Failed to save preferences");
            }
            setModal(null);
          }}
          onPickWorkDir={() => pyCall("pick_work_dir")}
          onSaveLayout={async () => {
            const r = await pyCall("save_layout", {
              left_col_width:  leftWidth,
              right_col_width: rightWidth,
              detail_height:   detailHeight,
              left_fracs:      leftFracs,
              right_fracs:     rightFracs,
            });
            if (r?.ok) showToast("Layout saved as default");
          }}
          onClose={() => setModal(null)}
        />
      )}

      {ctxMenu && (
        <ContextMenu
          juror={ctxMenu.juror}
          x={ctxMenu.x}
          y={ctxMenu.y}
          onClose={() => setCtxMenu(null)}
          onSetStatus={(jid, status) => { handleSetStatus(jid, status); }}
          onSetRating={(jid, rating) => { handleSetRating(jid, rating); }}
          onMarkFinal={(jid) => { handleMarkFinal(jid); }}
          onUnmarkFinal={(jid) => { handleUnmarkFinal(jid); }}
          onUnseat={(jid) => { handleUnseat(jid); }}
          onEdit={(j) => { setModal({ kind: "edit", juror: j }); }}
        />
      )}
    </div>
  );
}

/* Win11 title bar -------------------------------------------------------- */

function WindowChrome({ theme }) {
  return (
    <div className="winchrome">
      <div className="winchrome-title">
        <span className="winchrome-icon" aria-hidden="true">
          <svg viewBox="0 0 16 16" width="14" height="14">
            <rect x="1.5" y="1.5" width="13" height="13" rx="3"
              fill="var(--accent)" opacity="0.18"/>
            <text x="8" y="11.5" textAnchor="middle"
              fontFamily="var(--font-ui)" fontWeight="700" fontSize="9"
              fill="var(--accent)">JT</text>
          </svg>
        </span>
        <span>Jury Selection Tool</span>
        <span className="winchrome-doc">— untitled.json</span>
      </div>
      <div className="winchrome-btns" aria-hidden="true">
        <button className="winchrome-btn" tabIndex={-1} onClick={() => pyCall("minimize")}>
          <svg viewBox="0 0 10 10" width="10" height="10"><line x1="1" y1="5" x2="9" y2="5" stroke="currentColor" strokeWidth="1"/></svg>
        </button>
        <button className="winchrome-btn" tabIndex={-1} onClick={() => pyCall("toggle_maximize")}>
          <svg viewBox="0 0 10 10" width="10" height="10"><rect x="1.5" y="1.5" width="7" height="7" fill="none" stroke="currentColor" strokeWidth="1"/></svg>
        </button>
        <button className="winchrome-btn winchrome-close" tabIndex={-1} onClick={() => pyCall("exit_app")}>
          <svg viewBox="0 0 10 10" width="10" height="10">
            <line x1="1" y1="1" x2="9" y2="9" stroke="currentColor" strokeWidth="1"/>
            <line x1="9" y1="1" x2="1" y2="9" stroke="currentColor" strokeWidth="1"/>
          </svg>
        </button>
      </div>
    </div>
  );
}

/* Menu bar with dropdown shells (visual stubs for Stage 1) -------------- */

function MenuBar({ onCommand }) {
  const [open, setOpen] = React.useState(null);
  const close = () => setOpen(null);

  React.useEffect(() => {
    if (!open) return;
    const fn = (e) => { if (!e.target.closest(".menu-item, .menu-dd")) close(); };
    document.addEventListener("click", fn);
    return () => document.removeEventListener("click", fn);
  }, [open]);

  const Drop = ({ items }) => (
    <div className="menu-dd">
      {items.map((it, i) =>
        it === "-"
          ? <div key={i} className="menu-dd-sep"></div>
          : <button key={i} className="menu-dd-item" onClick={() => { close(); onCommand(it.cmd); }}>
              <span>{it.label}</span>
              {it.shortcut && <span className="menu-dd-shortcut">{it.shortcut}</span>}
            </button>
      )}
    </div>
  );

  return (
    <div className="menu-bar">
      <div className="menu-wrap">
        <button className={"menu-item" + (open === "file" ? " is-open" : "")}
                onClick={() => setOpen(open === "file" ? null : "file")}>File</button>
        {open === "file" && <Drop items={[
          {label:"New jury",          cmd:"new"},
          {label:"Open…",             cmd:"open",       shortcut:"Ctrl+O"},
          {label:"Save",              cmd:"save",       shortcut:"Ctrl+S"},
          {label:"Save As…",          cmd:"save_as"},
          "-",
          {label:"Upload CSV…",       cmd:"upload_csv"},
          {label:"Export PDF…",       cmd:"export_pdf"},
          "-",
          {label:"Exit",              cmd:"exit"},
        ]}/>}
      </div>
      <div className="menu-wrap">
        <button className={"menu-item" + (open === "settings" ? " is-open" : "")}
                onClick={() => setOpen(open === "settings" ? null : "settings")}>Settings</button>
        {open === "settings" && <Drop items={[
          {label:"Preferences…",      cmd:"settings",   shortcut:"Ctrl+,"},
        ]}/>}
      </div>
      <div className="menu-wrap">
        <button className={"menu-item" + (open === "help" ? " is-open" : "")}
                onClick={() => setOpen(open === "help" ? null : "help")}>Help</button>
        {open === "help" && <Drop items={[
          {label:"Quick Start",        cmd:"quickstart"},
          {label:"Keyboard Shortcuts", cmd:"shortcuts"},
          "-",
          {label:"About",              cmd:"about"},
        ]}/>}
      </div>

      <div className="menu-spacer"></div>
      <div className="menu-lockup">
        <span className="menu-lockup-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="14" height="14">
            <path d="M4 5h16M6 5v9a6 6 0 0 0 12 0V5M9 19h6M12 19v3"
              fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
          </svg>
        </span>
        <span className="menu-lockup-text">Jury Selection Tool</span>
      </div>
    </div>
  );
}

/* Tweaks panel ---------------------------------------------------------- */

function TweaksUI({ t, setTweak }) {
  return (
    <TweaksPanel title="Tweaks">
      <TweakSection label="Theme">
        <TweakRadio
          label="Mode"
          value={t.theme}
          onChange={v => setTweak("theme", v)}
          options={[{value:"light",label:"Light"},{value:"dark",label:"Dark"}]}
        />
        <TweakColor
          label="Accent"
          value={t.accent}
          onChange={v => setTweak("accent", v)}
          options={ACCENTS}
        />
        <TweakSelect
          label="Type"
          value={t.fontStack}
          onChange={v => setTweak("fontStack", v)}
          options={[
            {value:"segoe",  label:"Segoe UI Variable (Win11)"},
            {value:"inter",  label:"Inter Tight"},
            {value:"georgia",label:"Georgia (editorial)"},
          ]}
        />
      </TweakSection>

      <TweakSection label="Layout">
        <TweakRadio
          label="Density"
          value={t.density}
          onChange={v => setTweak("density", v)}
          options={[{value:"compact",label:"Compact"},{value:"cozy",label:"Cozy"}]}
        />
        <TweakSlider
          label="Corner radius"
          value={t.radius}
          onChange={v => setTweak("radius", v)}
          min={0} max={16} step={1} unit="px"
        />
      </TweakSection>
    </TweaksPanel>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<JuryApp/>);
