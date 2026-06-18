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
    const pid = e.pointerId;

    const onMove = (ev) => {
      if (ev.pointerId !== pid) return;
      const dFrac = ((ev.clientY - y0) / containerH) * totalFrac;
      const next = [...f0];
      if (aboveIdx != null) next[aboveIdx] = Math.max(0.08, f0[aboveIdx] + dFrac);
      if (belowIdx != null) next[belowIdx] = Math.max(0.08, f0[belowIdx] - dFrac);
      setFracs(next);
    };

    const onUp = (ev) => {
      if (ev.pointerId !== pid) return;
      document.removeEventListener("pointermove",   onMove);
      document.removeEventListener("pointerup",     onUp);
      document.removeEventListener("pointercancel", onUp);
      document.body.style.cursor     = "";
      document.body.style.userSelect = "";
    };

    document.body.style.cursor     = "ns-resize";
    document.body.style.userSelect = "none";
    document.addEventListener("pointermove",   onMove);
    document.addEventListener("pointerup",     onUp);
    document.addEventListener("pointercancel", onUp);
  };

  return { colRef, startDrag };
}

function Sash({ onPointerDown }) {
  return <div className="sash" onPointerDown={onPointerDown} />;
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

// Juror row in the sidebar.  When draggable + dragEnabled, the row uses
// Pointer Events (not HTML5 drag) so touch input works on tablets.
function JurorRow({ juror, tone, onClick, selected, draggable, dragEnabled, onDrop, onContextMenu }) {
  const isDraggable = !!draggable && !!dragEnabled;

  const handleClick = () => {
    if (pointerDrag.shouldSuppressClick()) return;
    if (onClick) onClick();
  };

  const handlePointerDown = isDraggable
    ? (e) => {
        pointerDrag.start(juror.id, e, e.currentTarget, (zone, data) => {
          if (onDrop) onDrop(juror.id, zone, data);
        });
      }
    : undefined;

  return (
    <button
      className={"jrow tone-" + tone + (selected ? " is-selected" : "") + (isDraggable ? " is-draggable" : "")}
      onClick={handleClick}
      onPointerDown={handlePointerDown}
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

function LeftColumn({
  byStatus, selectedJid, onSelect, theme, onToggleTheme, onAction,
  onDrop, dragEnabled, onJurorContextMenu, fracs, setFracs, style,
}) {
  const pool       = byStatus.pool;
  const excused    = byStatus.excused;
  const defStruck  = byStatus.struck_def;
  const proStruck  = byStatus.struck_pro;
  const bothStruck = byStatus.struck_both;

  const act = onAction || (() => {});

  // fracs: [pool, excused, defStruck, proStruck, bothStruck]
  const { colRef, startDrag } = useSash(fracs, setFracs);

  const rowProps = (j, tone) => ({
    juror:    j,
    tone:     tone,
    draggable: true,
    dragEnabled: !!dragEnabled,
    onDrop:   onDrop,
    onClick:  () => onSelect(j.id),
    selected: selectedJid === j.id,
    onContextMenu: onJurorContextMenu,
  });

  return (
    <aside className="col col-left" ref={colRef} style={style}>
      {/* Pool — drop zone: unseat a juror back to pool */}
      <section className="pane pane-pool" style={{ flex: fracs[0] }}
               data-dropzone="pool">
        <SectionTitle kind="pool" count={pool.length}>Preliminary Pool</SectionTitle>
        <div className="pane-body scroll">
          {pool.map(j => <JurorRow key={j.id} {...rowProps(j, "neutral")} />)}
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

      <Sash onPointerDown={(e) => startDrag(0, 1, e)} />

      {/* Excused — drop zone: mark as excused */}
      <section className="pane pane-excused" style={{ flex: fracs[1] }}
               data-dropzone="excused">
        <SectionTitle kind="excused" count={excused.length}>Excused</SectionTitle>
        <div className="pane-body scroll">
          {excused.map(j => <JurorRow key={j.id} {...rowProps(j, "excused")} />)}
        </div>
      </section>

      <Sash onPointerDown={(e) => startDrag(1, 2, e)} />

      {/* Defense struck — drop zone */}
      <section className="pane pane-struck pane-struck-def" style={{ flex: fracs[2] }}
               data-dropzone="struck-def">
        <SectionTitle kind="struck-def" count={defStruck.length}>Defense Struck</SectionTitle>
        <div className="pane-body scroll">
          {defStruck.map(j => <JurorRow key={j.id} {...rowProps(j, "struck")} />)}
        </div>
      </section>

      <Sash onPointerDown={(e) => startDrag(2, 3, e)} />

      {/* Prosecution struck — drop zone */}
      <section className="pane pane-struck pane-struck-pro" style={{ flex: fracs[3] }}
               data-dropzone="struck-pro">
        <SectionTitle kind="struck-pro" count={proStruck.length}>Prosecution Struck</SectionTitle>
        <div className="pane-body scroll">
          {proStruck.map(j => <JurorRow key={j.id} {...rowProps(j, "struck")} />)}
        </div>
      </section>

      <Sash onPointerDown={(e) => startDrag(3, 4, e)} />

      {/* Both struck — drop zone */}
      <section className="pane pane-struck pane-struck-both" style={{ flex: fracs[4] }}
               data-dropzone="struck-both">
        <SectionTitle kind="struck-both" count={bothStruck.length}>Both Struck</SectionTitle>
        <div className="pane-body scroll">
          {bothStruck.map(j => <JurorRow key={j.id} {...rowProps(j, "struck-both")} />)}
          {bothStruck.length === 0 && <div className="pane-empty">—</div>}
        </div>
      </section>
    </aside>
  );
}

function RightColumn({ finals, selectedFinalId, onSelectFinal, onJurorContextMenu, fracs, setFracs, style }) {
  // `finals` is already sorted by finalNo by the parent (byStatus.final).
  const selected = finals.find(j => j.id === selectedFinalId) || finals[0];

  // fracs: [finalList, finalInfo]
  const { colRef, startDrag } = useSash(fracs, setFracs);

  return (
    <aside className="col col-right" ref={colRef} style={style}>
      {/* Final jury list — drop zone: drag any juror here to mark as final */}
      <section className="pane pane-final" style={{ flex: fracs[0] }}
               data-dropzone="final">
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

      <Sash onPointerDown={(e) => startDrag(0, 1, e)} />

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

// React.memo so the sidebars only re-render when their actual props change.
const MemoLeftColumn  = React.memo(LeftColumn);
const MemoRightColumn = React.memo(RightColumn);
Object.assign(window, {
  LeftColumn:  MemoLeftColumn,
  RightColumn: MemoRightColumn,
  SectionTitle, JurorRow,
});
