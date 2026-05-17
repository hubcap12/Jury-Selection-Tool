/* Left + right sidebars  ---------------------------------------------------- */

function SectionTitle({ kind, children, count }) {
  return (
    <div className={"section-title section-" + kind}>
      <span className="section-dot" aria-hidden="true"></span>
      <span className="section-label">{children}</span>
      {count != null && <span className="section-count">{count}</span>}
    </div>
  );
}

function JurorRow({ juror, tone, onClick, selected }) {
  return (
    <button
      className={"jrow tone-" + tone + (selected ? " is-selected" : "")}
      onClick={onClick}
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

function LeftColumn({ jurors, selectedJid, onSelect, theme, onToggleTheme, onAction }) {
  const pool       = jurors.filter(j => j.status === "pool");
  const excused    = jurors.filter(j => j.status === "excused");
  const defStruck  = jurors.filter(j => j.status === "struck_def");
  const proStruck  = jurors.filter(j => j.status === "struck_pro");
  const bothStruck = jurors.filter(j => j.status === "struck_both");

  const act = onAction || (() => {});

  return (
    <aside className="col col-left">
      <section className="pane pane-pool">
        <SectionTitle kind="pool" count={pool.length}>Preliminary Pool</SectionTitle>
        <div className="pane-body scroll">
          {pool.map(j => (
            <JurorRow key={j.id} juror={j} tone="neutral" onClick={() => onSelect(j.id)} selected={selectedJid===j.id}/>
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

      <section className="pane pane-excused">
        <SectionTitle kind="excused" count={excused.length}>Excused</SectionTitle>
        <div className="pane-body scroll">
          {excused.map(j => (
            <JurorRow key={j.id} juror={j} tone="excused" onClick={() => onSelect(j.id)} selected={selectedJid===j.id}/>
          ))}
        </div>
      </section>

      <section className="pane pane-struck pane-struck-def">
        <SectionTitle kind="struck-def" count={defStruck.length}>Defense Struck</SectionTitle>
        <div className="pane-body scroll">
          {defStruck.map(j => (
            <JurorRow key={j.id} juror={j} tone="struck" onClick={() => onSelect(j.id)} selected={selectedJid===j.id}/>
          ))}
        </div>
      </section>

      <section className="pane pane-struck pane-struck-pro">
        <SectionTitle kind="struck-pro" count={proStruck.length}>Prosecution Struck</SectionTitle>
        <div className="pane-body scroll">
          {proStruck.map(j => (
            <JurorRow key={j.id} juror={j} tone="struck" onClick={() => onSelect(j.id)} selected={selectedJid===j.id}/>
          ))}
        </div>
      </section>

      <section className="pane pane-struck pane-struck-both">
        <SectionTitle kind="struck-both" count={bothStruck.length}>Both Struck</SectionTitle>
        <div className="pane-body scroll">
          {bothStruck.map(j => (
            <JurorRow key={j.id} juror={j} tone="struck-both" onClick={() => onSelect(j.id)} selected={selectedJid===j.id}/>
          ))}
          {bothStruck.length === 0 && <div className="pane-empty">—</div>}
        </div>
      </section>
    </aside>
  );
}

function RightColumn({ jurors, selectedFinalId, onSelectFinal }) {
  const finals = jurors
    .filter(j => j.status === "final")
    .sort((a, b) => (a.finalNo || 99) - (b.finalNo || 99));

  const selected = finals.find(j => j.id === selectedFinalId) || finals[0];

  return (
    <aside className="col col-right">
      <section className="pane pane-final">
        <SectionTitle kind="final" count={finals.length}>Final Jury</SectionTitle>
        <div className="pane-body scroll">
          {finals.map((j, i) => (
            <button
              key={j.id}
              className={"jrow tone-final" + (selected?.id === j.id ? " is-selected" : "")}
              onClick={() => onSelectFinal(j.id)}
            >
              <span className="jrow-idx">{i + 1}.</span>
              <span className="jrow-id">#{j.id}</span>
              <span className="jrow-name">{j.name}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="pane pane-final-info">
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
