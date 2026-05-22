/* Left + right sidebars  ---------------------------------------------------- */

/* Drag-to-resize sash hook (controlled).
   `fracs` / `setFracs` come from the parent so positions can be saved
   centrally.  `startDrag(aboveIdx, belowIdx, mouseEvent)` — pass null
   for the fixed side. */
function useSash(fracs, setFracs) {
  const colRef = React.useRef(null);
  const fracsRef = React.useRef(fracs);
  fracsRef.current = fracs;

  const startDrag = (aboveIdx, belowIdx, e) => {
    e.preventDefault();
    const y0 = e.clientY;
    const f0 = [...fracsRef.current];
    const totalFrac = f0.reduce((a, b) => a + b, 0);
    const containerH = colRef.current?.clientHeight ?? 600;

    const onMove = (ev) => {
      const dFrac = ((ev.clientY - y0) / containerH) * totalFrac;
      const next = [...f0];
      if (aboveIdx != null) next[aboveIdx] = Math.max(0.08, f0[aboveIdx] + dFrac);
      if (belowIdx != null) next[belowIdx] = Math.max(0.08, f0[belowIdx] - dFrac);
      setFracs(next);
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

  return { colRef, startDrag };
}

function Sash({ onMouseDown }) {
  return <div className="sash" onMouseDown={onMouseDown} />;
}

function SectionTitle({ kind, children, count }) {
  return (
    <div className={"section-title section-" + kind}>
      <span className="section-dot" aria-hidden="true"></span>
      <span className="section-label">{children}</span>
      {count != null && <span className="section-count">{count}</span>}
    </div>
  );
}

function JurorRow({ juror, tone, onClick, selected, draggable, onContextMenu }) {
  return (
    <button
      className={"jrow tone-" + tone + (selected ? " is-selected" : "")}
      onClick={onClick}
      draggable={!!draggable}
      onDragStart={(e) => {
        if (!draggable) return;
        e.dataTransfer.setData("text/plain", String(juror.id));
        e.dataTransfer.effectAllowed = "move";
      }}
      onContextMenu={(e) => { e.preventDefault(); onContextMenu && onContextMenu(juror, e.clientX, e.clientY); }}
    >
      <span className="jrow-id">#{juror.id}</span>
      <span className="jrow-name">{juror.name}</span>
    </button>
  );
}

function FinalJurorRow({ juror, idx }) {
  return (
    <div className="fjrow">
      <span className="fjrow-idx">{idx}.</span>
      <span className="fjrow-id">#{juror.id}</span>
      <span className="fjrow-name">{juror.name}</span>
    </div>
  );
}

function LeftColumn({ jurors, selectedJid, onSelect, theme, onToggleTheme, onAction, onUnseatDrop, onJurorContextMenu, fracs, setFracs, style }) {
  const pool       = jurors.filter(j => j.status === "pool");
  const excused    = jurors.filter(j => j.status === "excused");
  const defStruck  = jurors.filter(j => j.status === "struck_def");
  const proStruck  = jurors.filter(j => j.status === "struck_pro");
  const bothStruck = jurors.filter(j => j.status === "struck_both");

  const act = onAction || (() => {});

  // fracs: [pool, excused, defStruck, proStruck, bothStruck]
  const { colRef, startDrag } = useSash(fracs, setFracs);

  const [poolDragOver, setPoolDragOver] = React.useState(false);
  const poolDropProps = {
    onDragOver: (e) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; setPoolDragOver(true); },
    onDragLeave: () => setPoolDragOver(false),
    onDrop: (e) => {
      e.preventDefault();
      setPoolDragOver(false);
      const jid = parseInt(e.dataTransfer.getData("text/plain"), 10);
      if (!Number.isNaN(jid)) onUnseatDrop && onUnseatDrop(jid);
    },
  };

  return (
    <aside className="col col-left" ref={colRef} style={style}>
      <section className={"pane pane-pool" + (poolDragOver ? " is-drag-over" : "")}
               style={{ flex: fracs[0] }} {...poolDropProps}>
        <SectionTitle kind="pool" count={pool.length}>Preliminary Pool</SectionTitle>
        <div className="pane-body scroll">
          {pool.map(j => (
            <JurorRow key={j.id} juror={j} tone="neutral" draggable
                      onClick={() => onSelect(j.id)} selected={selectedJid===j.id}
                      onContextMenu={onJurorContextMenu}/>
          ))}
          {pool.length === 0 && <div className="pane-empty">— no jurors —</div>}
        </div>
      </section>

      <section className="pane pane-actions">
        <div className="btn-row">
          <button className="btn btn-default" onClick={() => act("Add juror")}>Add</button>
          <button className="btn btn-default" onClick={() => act("Edit juror")}>Edit</button>
          <button className="btn btn-primary" onClick={() => act("Auto Seat")}>Auto Seat</button>
        </div>
        <div className="btn-row">
          <button className="btn btn-default" onClick={() => act("Remove juror")}>Remove</button>
          <button className="btn btn-default" onClick={() => act("Save")}>Save</button>
        </div>
        <div className="btn-row">
          <button className="btn btn-default" onClick={() => act("Upload CSV")}>Upload CSV</button>
          <button className="btn btn-default" onClick={() => act("Export PDF")}>Export PDF</button>
        </div>
        <div className="btn-row">
          <button className="btn btn-danger" onClick={() => act("Reset")}>Reset</button>
        </div>
      </section>

      <Sash onMouseDown={(e) => startDrag(0, 1, e)} />

      <section className="pane pane-excused" style={{ flex: fracs[1] }}>
        <SectionTitle kind="excused" count={excused.length}>Excused</SectionTitle>
        <div className="pane-body scroll">
          {excused.map(j => (
            <JurorRow key={j.id} juror={j} tone="excused" draggable onClick={() => onSelect(j.id)} selected={selectedJid===j.id}
                      onContextMenu={onJurorContextMenu}/>
          ))}
        </div>
      </section>

      <Sash onMouseDown={(e) => startDrag(1, 2, e)} />

      <section className="pane pane-struck pane-struck-def" style={{ flex: fracs[2] }}>
        <SectionTitle kind="struck-def" count={defStruck.length}>Defense Struck</SectionTitle>
        <div className="pane-body scroll">
          {defStruck.map(j => (
            <JurorRow key={j.id} juror={j} tone="struck" draggable onClick={() => onSelect(j.id)} selected={selectedJid===j.id}
                      onContextMenu={onJurorContextMenu}/>
          ))}
        </div>
      </section>

      <Sash onMouseDown={(e) => startDrag(2, 3, e)} />

      <section className="pane pane-struck pane-struck-pro" style={{ flex: fracs[3] }}>
        <SectionTitle kind="struck-pro" count={proStruck.length}>Prosecution Struck</SectionTitle>
        <div className="pane-body scroll">
          {proStruck.map(j => (
            <JurorRow key={j.id} juror={j} tone="struck" draggable onClick={() => onSelect(j.id)} selected={selectedJid===j.id}
                      onContextMenu={onJurorContextMenu}/>
          ))}
        </div>
      </section>

      <Sash onMouseDown={(e) => startDrag(3, 4, e)} />

      <section className="pane pane-struck pane-struck-both" style={{ flex: fracs[4] }}>
        <SectionTitle kind="struck-both" count={bothStruck.length}>Both Struck</SectionTitle>
        <div className="pane-body scroll">
          {bothStruck.map(j => (
            <JurorRow key={j.id} juror={j} tone="struck-both" draggable onClick={() => onSelect(j.id)} selected={selectedJid===j.id}
                      onContextMenu={onJurorContextMenu}/>
          ))}
          {bothStruck.length === 0 && <div className="pane-empty">—</div>}
        </div>
      </section>
    </aside>
  );
}

function RightColumn({ jurors, selectedFinalId, onSelectFinal, onJurorContextMenu, fracs, setFracs, style }) {
  const finals = jurors
    .filter(j => j.status === "final")
    .sort((a, b) => (a.finalNo || 99) - (b.finalNo || 99));

  const selected = finals.find(j => j.id === selectedFinalId) || finals[0];

  // fracs: [finalList, finalInfo]
  const { colRef, startDrag } = useSash(fracs, setFracs);

  return (
    <aside className="col col-right" ref={colRef} style={style}>
      <section className="pane pane-final" style={{ flex: fracs[0] }}>
        <SectionTitle kind="final" count={finals.length}>Final Jury</SectionTitle>
        <div className="pane-body scroll">
          {finals.map((j, i) => (
            <button
              key={j.id}
              className={"jrow tone-final" + (selected?.id === j.id ? " is-selected" : "")}
              onClick={() => onSelectFinal(j.id)}
              onContextMenu={(e) => { e.preventDefault(); onJurorContextMenu && onJurorContextMenu(j, e.clientX, e.clientY); }}
            >
              <span className="jrow-idx">{i + 1}.</span>
              <span className="jrow-id">#{j.id}</span>
              <span className="jrow-name">{j.name}</span>
            </button>
          ))}
        </div>
      </section>

      <Sash onMouseDown={(e) => startDrag(0, 1, e)} />

      <section className="pane pane-final-info" style={{ flex: fracs[1] }}>
        <div className="pane-header-tab">Final Jury Info</div>
        <div className="pane-body">
          {selected ? (
            <div className="fj-info">
              <div className="fj-info-head">
                <span className="fj-info-final">Final #{selected.finalNo}</span>
                <span className="fj-info-sep">—</span>
                <span className="fj-info-id">#{selected.id}</span>
                <span className="fj-info-name">{selected.name}</span>
                <span className="fj-info-sep">·</span>
                <span className="fj-info-age">Age {selected.age}</span>
              </div>
              <div className="fj-info-row">
                <label>Keywords:</label>
                <div className="fj-info-val">{selected.keywords || ""}</div>
              </div>
              <div className="fj-info-row fj-info-notes">
                <label>Notes:</label>
                <div className="fj-info-val fj-info-notes-val">{selected.notes || ""}</div>
              </div>
            </div>
          ) : (
            <div className="pane-empty">No final jurors yet.</div>
          )}
        </div>
      </section>
    </aside>
  );
}

Object.assign(window, { LeftColumn, RightColumn, SectionTitle, JurorRow });
