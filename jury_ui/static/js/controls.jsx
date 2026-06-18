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
  const compact = count >= 5;
  return (
    <div className={"panel-tabs" + (compact ? " panel-tabs-compact" : "")} role="tablist">
      {Array.from({ length: count }).map((_, i) => {
        const n = i + 1;
        const isActive = active === n;
        return (
          <button
            key={n}
            role="tab"
            aria-selected={isActive}
            title={`Panel ${n}`}
            className={"panel-tab" + (isActive ? " is-active" : "")}
            onClick={() => onChange(n)}
          >
            {compact ? n : `Panel ${n}`}
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
  activePanel, setActivePanel, numPanels,
  theme, setTheme,
  frozen, onToggleFreeze,
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
          <button
            className={"btn-freeze" + (frozen ? " is-frozen" : "")}
            onClick={onToggleFreeze}
            title={frozen ? "Press F9 or click to unfreeze" : "Freeze screen — disables all controls"}
          >
            {frozen ? "■ Frozen · F9" : "Freeze"}
          </button>
          <PanelTabs active={activePanel} onChange={setActivePanel} count={numPanels}/>
          <div className="control-spacer"></div>
          <ThemeToggle theme={theme} onChange={setTheme}/>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */

function DetailEditor({ juror, panel, onSaveKeywords, onSaveNotes, onSetStatus,
                       onSetRating, onMarkFinal, onUnmarkFinal, onUnseat }) {
  const [kw, setKw]       = React.useState("");
  const [notes, setNotes] = React.useState("");

  React.useEffect(() => {
    setKw(juror?.keywords || "");
    setNotes(juror?.notes || "");
  }, [juror?.id]);

  const status  = juror?.status || "seated";
  const isFinal = status === "final";
  const dimmed  = !juror;

  const Status = ({ value, label, tone }) => (
    <button
      className={"status-pill tone-" + (tone || "neutral") + (status === value ? " is-active" : "")}
      onClick={() => onSetStatus && onSetStatus(juror.id, value)}
    >{label}</button>
  );

  return (
    <section className="detail">
      <div className="detail-tab">Juror Details</div>
      <div className="detail-body">

      <div className="detail-head">
        {juror ? (
          <>
            {juror.seat  && <span className="chip chip-panel">Panel {panel}</span>}
            {juror.seat  && <span className="chip chip-seat">Seat {juror.seat}</span>}
            {!juror.seat && <span className="chip chip-pool">Pool</span>}
            <span className="detail-sep">—</span>
            <span className="detail-jid">Juror #{juror.id}</span>
            <span className="detail-name">{juror.name}</span>
            <span className="detail-sep">·</span>
            <span className="detail-age">Age {juror.age}</span>
          </>
        ) : (
          <span className="detail-empty">Select a seat or pool juror to see details.</span>
        )}
      </div>

      <div className={"detail-grid" + (dimmed ? " detail-dimmed" : "")}>
        <label className="detail-label">Status:</label>
        <div className="status-row">
          <Status value="seated"      label="Seated"      tone="seated"/>
          <Status value="excused"     label="Excused"     tone="excused"/>
          <Status value="struck_def"  label="Def. Strike" tone="struck"/>
          <Status value="struck_pro"  label="Pro. Strike" tone="struck"/>
          <Status value="struck_both" label="Both Struck" tone="struck"/>
          <button
            className={"status-pill tone-final" + (isFinal ? " is-active" : "")}
            onClick={() => isFinal ? onUnmarkFinal(juror.id) : onMarkFinal(juror.id)}
          >{isFinal ? `Final #${juror?.finalNo}` : "Final"}</button>
          {juror?.seat && (
            <button className="status-pill tone-neutral" onClick={() => onUnseat(juror.id)} title="Return to pool">
              Unseat
            </button>
          )}
        </div>

        <label className="detail-label">Keywords:</label>
        <input className="input"
               value={kw}
               onChange={(e) => setKw(e.target.value)}
               onKeyDown={(e) => {
                 if (e.key === "Enter") {
                   e.preventDefault();
                   if (juror && onSaveKeywords) onSaveKeywords(juror.id, kw);
                 }
               }}
               onBlur={() => juror && onSaveKeywords && onSaveKeywords(juror.id, kw)}
               placeholder="Add keywords…"/>

        <label className="detail-label detail-label-top">Notes:</label>
        <RichTextEditor
          value={notes}
          placeholder="Type notes…"
          onSave={(n) => {
            if (!juror) return;
            setNotes(n);
            onSaveNotes && onSaveNotes(juror.id, n);
          }}
        />
      </div>

      <div className={"detail-priority" + (dimmed ? " detail-dimmed" : "")}>
        <label className="detail-label">Priority:</label>
        <div className="priority-row">
          <button className={"prio-btn prio-up3"   + (juror?.rating ===  3 ? " is-active" : "")} onClick={() => onSetRating(juror.id,  3)}>▲▲▲</button>
          <button className={"prio-btn prio-up2"   + (juror?.rating ===  2 ? " is-active" : "")} onClick={() => onSetRating(juror.id,  2)}>▲▲</button>
          <button className={"prio-btn prio-up1"   + (juror?.rating ===  1 ? " is-active" : "")} onClick={() => onSetRating(juror.id,  1)}>▲</button>
          <button className={"prio-btn prio-clear" + (juror?.rating ===  0 ? " is-active" : "")} onClick={() => onSetRating(juror.id,  0)} title="Clear priority">—</button>
          <button className={"prio-btn prio-down1" + (juror?.rating === -1 ? " is-active" : "")} onClick={() => onSetRating(juror.id, -1)}>▼</button>
          <button className={"prio-btn prio-down2" + (juror?.rating === -2 ? " is-active" : "")} onClick={() => onSetRating(juror.id, -2)}>▼▼</button>
          <button className={"prio-btn prio-down3" + (juror?.rating === -3 ? " is-active" : "")} onClick={() => onSetRating(juror.id, -3)}>▼▼▼</button>
        </div>
      </div>

      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */

function StatusBar({ byStatus, struckCount, activePanel, numPanels, selectedJid }) {
  // Status counters are derived from the pre-bucketed `byStatus` map so we
  // don't re-scan the juror list five times per render.  The seated count
  // is panel-scoped, so it filters one bucket (small) instead of all.
  let seatedCt = 0;
  for (const j of byStatus.seated) if (j.panel === activePanel) seatedCt++;
  const finalCt   = byStatus.final.length;
  const poolCt    = byStatus.pool.length;
  const excusedCt = byStatus.excused.length;
  const struckCt  = struckCount;

  return (
    <footer className="statusbar">
      <span className="status-cell"><span className="status-dot d-pool"></span>Pool {poolCt}</span>
      <span className="status-cell"><span className="status-dot d-seated"></span>Seated {seatedCt}</span>
      <span className="status-cell"><span className="status-dot d-excused"></span>Excused {excusedCt}</span>
      <span className="status-cell"><span className="status-dot d-struck"></span>Struck {struckCt}</span>
      <span className="status-cell"><span className="status-dot d-final"></span>Final Jury {finalCt}</span>
      <span className="status-spacer"></span>
      <span className="status-cell status-cell-muted">Autosave on · every 15 min</span>
      <span className="status-cell status-cell-muted">Panel {activePanel} of {numPanels}</span>
      <span className="status-cell status-cell-muted">v2.0.6 · PolyForm Noncommercial</span>
    </footer>
  );
}

// Memoize so unrelated re-renders of the root app don't force these to
// re-render.  Their props are stable now (numbers/strings + useCallback'd
// handlers from the parent) so the comparison succeeds the vast majority
// of the time.
Object.assign(window, {
  ControlBar:    React.memo(ControlBar),
  DetailEditor:  React.memo(DetailEditor),
  StatusBar:     React.memo(StatusBar),
});
