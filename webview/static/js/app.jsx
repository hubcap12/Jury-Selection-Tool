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
  const [selectedSeat, setSelectedSeat]    = React.useState(null);
  const [selectedFinal, setSelectedFinal]  = React.useState(null);
  const [toast, setToast]                  = React.useState(null);

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
      if (s.active_panel) setActivePanel(s.active_panel);
      if (s.selected_seat) setSelectedSeat(s.selected_seat);
      if (s.selected_final) setSelectedFinal(s.selected_final);
    });
  }, []);

  const selectedJuror = React.useMemo(() => {
    return jurors.find(j => j.seat === selectedSeat && j.panel === activePanel);
  }, [jurors, selectedSeat, activePanel]);

  const handleSelectSeat = (seatNo) => {
    setSelectedSeat(seatNo);
    pyCall("select_seat", activePanel, seatNo);
  };

  const handleSelectJid = (jid) => {
    const j = jurors.find(x => x.id === jid);
    if (j && j.seat) setSelectedSeat(j.seat);
  };

  const handleSetPanel = (n) => {
    setActivePanel(n);
    pyCall("set_active_panel", n);
  };

  // Apply CSS vars from tweaks.
  React.useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = t.theme;
    root.dataset.density = t.density;
    root.style.setProperty("--accent", t.accent);
    root.style.setProperty("--radius", t.radius + "px");
    root.style.setProperty("--radius-sm", Math.max(2, t.radius - 4) + "px");
    root.style.setProperty("--radius-lg", (t.radius + 4) + "px");
    root.style.setProperty("--font-ui", FONT_STACKS[t.fontStack] || FONT_STACKS.segoe);
    pyCall("set_theme", t.theme);
  }, [t]);

  // Toast helper for "coming soon" actions in stage 1.
  const showToast = (msg) => {
    setToast(msg);
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => setToast(null), 2200);
  };

  return (
    <div className="app-root">
      <WindowChrome theme={t.theme}/>

      <MenuBar onCommand={(cmd) => {
        const handlers = {
          new:        () => showToast("New jury — Stage 2"),
          open:       () => pyCall("open_file").then(r => showToast(r?.msg || "Open — Stage 2")),
          save:       () => pyCall("save").then(r => showToast(r?.msg || "Save — Stage 2")),
          save_as:    () => showToast("Save As — Stage 2"),
          export_pdf: () => pyCall("export_pdf").then(r => showToast(r?.msg || "PDF — Stage 2")),
          upload_csv: () => showToast("Upload CSV — Stage 2"),
          settings:   () => showToast("Settings dialog — Stage 4"),
          about:      () => showToast("Jury Selection Tool · Stage 1 preview"),
          exit:       () => pyCall("exit_app"),
        };
        (handlers[cmd] || (() => {}))();
      }}/>

      <div className="app-body">
        <LeftColumn
          jurors={jurors}
          selectedJid={selectedJuror?.id}
          onSelect={handleSelectJid}
          theme={t.theme}
          onToggleTheme={() => setTweak("theme", t.theme === "dark" ? "light" : "dark")}
          onAction={(a) => showToast(a + " — Stage 2")}
        />

        <main className="col col-center">
          <ControlBar
            rows={rows} cols={cols} jurySize={jurySize} corner={corner}
            setRows={setRows} setCols={setCols} setJurySize={setJurySize} setCorner={setCorner}
            activePanel={activePanel} setActivePanel={handleSetPanel}
            theme={t.theme} setTheme={v => setTweak("theme", v)}
          />

          <SeatGrid
            rows={rows}
            cols={cols}
            jurors={jurors.filter(j => j.panel === activePanel)}
            selectedSeat={selectedSeat}
            onSelectSeat={handleSelectSeat}
          />

          <DetailEditor juror={selectedJuror} panel={activePanel}/>
        </main>

        <RightColumn
          jurors={jurors}
          selectedFinalId={selectedFinal}
          onSelectFinal={setSelectedFinal}
        />
      </div>

      <StatusBar jurors={jurors} activePanel={activePanel} selectedJid={selectedJuror?.id}/>

      <TweaksUI t={t} setTweak={setTweak}/>

      {toast && <div className="toast">{toast}</div>}
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
          {label:"About",             cmd:"about"},
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
