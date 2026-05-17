/* Top control bar, juror detail editor, status bar  ------------------------ */

function NumberStepper({ label, value, onChange, min = 1, max = 99 }) {
  return (
    <div className="stepper">
      <label className="stepper-label">{label}</label>
      <div className="stepper-control">
        <button className="stepper-btn" onClick={() => onChange(Math.max(min, value - 1))} aria-label="decrement">−</button>
        <input
          className="stepper-input"
          value={value}
          onChange={e => {
            const v = parseInt(e.target.value, 10);
            if (!Number.isNaN(v)) onChange(Math.max(min, Math.min(max, v)));
          }}
        />
        <button className="stepper-btn" onClick={() => onChange(Math.min(max, value + 1))} aria-label="increment">+</button>
      </div>
    </div>
  );
}

function StartCorner({ value, onChange }) {
  // Picks which corner seat #1 starts in. TL/TR/BL/BR.
  const opts = [
    { id: "TL", arrow: "↖" },
    { id: "TR", arrow: "↗" },
    { id: "BL", arrow: "↙" },
    { id: "BR", arrow: "↘" },
  ];
  return (
    <div className="corner">
      <label className="stepper-label">Start #1:</label>
      <div className="corner-grid">
        {opts.map(o => (
          <button
            key={o.id}
            className={"corner-btn" + (value === o.id ? " is-active" : "")}
            onClick={() => onChange(o.id)}
            aria-label={"Start at " + o.id}
          >
            {o.arrow}
          </button>
        ))}
      </div>
    </div>
  );
}

function PanelTabs({ active, onChange, count = 3 }) {
  return (
    <div className="panel-tabs" role="tablist">
      {Array.from({ length: count }).map((_, i) => {
        const n = i + 1;
        const isActive = active === n;
        return (
          <button
            key={n}
            role="tab"
            aria-selected={isActive}
            className={"panel-tab" + (isActive ? " is-active" : "")}
            onClick={() => onChange(n)}
          >
            Panel {n}
          </button>
        );
      })}
    </div>
  );
}

function ThemeToggle({ theme, onChange }) {
  return (
    <div className="theme-toggle" role="tablist">
      <button
        role="tab"
        aria-selected={theme === "light"}
        className={"theme-btn" + (theme === "light" ? " is-active" : "")}
        onClick={() => onChange("light")}
      >
        <span className="theme-glyph">☀</span> Light
      </button>
      <button
        role="tab"
        aria-selected={theme === "dark"}
        className={"theme-btn" + (theme === "dark" ? " is-active" : "")}
        onClick={() => onChange("dark")}
      >
        <span className="theme-glyph">☾</span> Dark
      </button>
    </div>
  );
}

function ControlBar({
  rows, cols, jurySize, corner,
  setRows, setCols, setJurySize, setCorner,
  activePanel, setActivePanel,
  theme, setTheme,
}) {
  return (
    <div className="control-bar">
      <div className="control-bar-title">Juror Pool</div>

      <div className="control-bar-row">
        <div className="control-group">
          <NumberStepper label="Rows:"    value={rows}     onChange={setRows}     min={1} max={20}/>
          <NumberStepper label="Columns:" value={cols}     onChange={setCols}     min={1} max={20}/>
          <NumberStepper label="Jury Size:" value={jurySize} onChange={setJurySize} min={1} max={24}/>
          <StartCorner value={corner} onChange={setCorner}/>
        </div>

        <div className="control-group control-group-right">
          <PanelTabs active={activePanel} onChange={setActivePanel}/>
          <div className="control-spacer"></div>
          <ThemeToggle theme={theme} onChange={setTheme}/>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */

function DetailEditor({ juror, panel }) {
  if (!juror) {
    return (
      <section className="detail">
        <div className="detail-tab">Juror Details</div>
        <div className="detail-empty">Select a seat or pool juror to see details.</div>
      </section>
    );
  }

  return (
    <section className="detail">
      <div className="detail-tab">Juror Details</div>

      <div className="detail-head">
        <span className="chip chip-panel">Panel {panel}</span>
        <span className="chip chip-seat">Seat {juror.seat}</span>
        <span className="detail-sep">—</span>
        <span className="detail-jid">Juror #{juror.id}</span>
        <span className="detail-name">{juror.name}</span>
        <span className="detail-sep">·</span>
        <span className="detail-age">Age {juror.age}</span>
      </div>

      <div className="detail-grid">
        <label className="detail-label">Keywords:</label>
        <input className="input" defaultValue={juror.keywords || ""} placeholder="Add keywords…"/>

        <label className="detail-label detail-label-top">Notes:</label>
        <div className="notes-wrap">
          <div className="notes-toolbar">
            <select className="select select-sm" defaultValue="Helvetica">
              <option>Helvetica</option>
              <option>Segoe UI</option>
              <option>Consolas</option>
              <option>Georgia</option>
            </select>
            <select className="select select-sm select-tiny" defaultValue="10">
              <option>8</option><option>9</option><option>10</option>
              <option>11</option><option>12</option><option>14</option>
            </select>
            <span className="tb-divider"></span>
            <button className="tb-btn tb-btn-b"><b>B</b></button>
            <button className="tb-btn tb-btn-i"><i>I</i></button>
            <button className="tb-btn tb-btn-u"><u>U</u></button>
            <span className="tb-divider"></span>
            <button className="tb-btn">•</button>
            <span className="tb-divider"></span>
            <button className="tb-btn tb-btn-text">Clear fmt</button>
          </div>
          <textarea className="notes-area" defaultValue={juror.notes || ""} placeholder="Type notes…"></textarea>
        </div>
      </div>

      <div className="detail-priority">
        <label className="detail-label">Priority:</label>
        <div className="priority-row">
          <button className="prio-btn prio-up3"   title="Strong positive">▲▲▲</button>
          <button className="prio-btn prio-up2"   title="Positive">▲▲</button>
          <button className="prio-btn prio-up1"   title="Slight positive">▲</button>
          <button className="prio-btn prio-down1" title="Slight negative">▼</button>
          <button className="prio-btn prio-down2" title="Negative">▼▼</button>
          <button className="prio-btn prio-down3" title="Strong negative">▼▼▼</button>
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */

function StatusBar({ jurors, activePanel, selectedJid }) {
  const seatedCt = jurors.filter(j => j.status === "seated" && j.panel === activePanel).length;
  const finalCt  = jurors.filter(j => j.status === "final").length;
  const poolCt   = jurors.filter(j => j.status === "pool").length;
  const struckCt = jurors.filter(j => /^struck/.test(j.status)).length;

  return (
    <footer className="statusbar">
      <span className="status-cell"><span className="status-dot d-pool"></span>Pool {poolCt}</span>
      <span className="status-cell"><span className="status-dot d-seated"></span>Seated {seatedCt}</span>
      <span className="status-cell"><span className="status-dot d-struck"></span>Struck {struckCt}</span>
      <span className="status-cell"><span className="status-dot d-final"></span>Final Jury {finalCt}</span>
      <span className="status-spacer"></span>
      <span className="status-cell status-cell-muted">Autosave on · every 15 min</span>
      <span className="status-cell status-cell-muted">Panel {activePanel} of 3</span>
      <span className="status-cell status-cell-muted">v1.4 · PolyForm Noncommercial</span>
    </footer>
  );
}

Object.assign(window, { ControlBar, DetailEditor, StatusBar });
