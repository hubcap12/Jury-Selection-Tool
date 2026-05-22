/* Seat grid + seat tile  ---------------------------------------------------- */

function RatingArrows({ rating }) {
  if (!rating) return null;
  const up = rating > 0;
  const n = Math.min(3, Math.abs(rating));
  const glyph = up ? "▲" : "▼";
  const cls = up ? "rating-up" : "rating-down";
  return (
    <span className={"seat-rating " + cls}>
      {Array.from({ length: n }).map((_, i) => <span key={i}>{glyph}</span>)}
    </span>
  );
}

function Seat({ seatNo, juror, selected, onClick, onDropJuror, onContextMenu }) {
  const [dragOver, setDragOver] = React.useState(false);

  const dropProps = {
    onDragOver: (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      if (!dragOver) setDragOver(true);
    },
    onDragLeave: () => setDragOver(false),
    onDrop: (e) => {
      e.preventDefault();
      setDragOver(false);
      const jid = parseInt(e.dataTransfer.getData("text/plain"), 10);
      if (!Number.isNaN(jid)) onDropJuror && onDropJuror(jid, seatNo);
    },
  };

  if (!juror) {
    return (
      <button
        className={"seat seat-empty" + (dragOver ? " is-drag-over" : "")}
        onClick={onClick}
        aria-label={`Seat ${seatNo}, empty`}
        {...dropProps}
      >
        <span className="seat-stripe" aria-hidden="true"></span>
        <header className="seat-eyebrow">
          <span className="seat-num">{String(seatNo).padStart(2,"0")}</span>
          <span className="seat-jid">— · —</span>
        </header>
        <div className="seat-name seat-empty-label">empty</div>
        <div className="seat-age">no juror</div>
        <footer className="seat-status seat-status-empty">UNASSIGNED</footer>
      </button>
    );
  }

  // Status footer ALWAYS renders so the grid alignment is rock-solid.
  const statusText =
    juror.status === "final"       ? `FINAL JUROR #${juror.finalNo}` :
    juror.status === "excused"     ? "EXCUSED"                       :
    juror.status === "struck_def"  ? "DEFENSE STRIKE"                :
    juror.status === "struck_pro"  ? "STATE STRIKE"                  :
    juror.status === "struck_both" ? "BOTH STRUCK"                   :
    "SEATED";

  const cls = [
    "seat",
    `seat-${juror.status}`,
    selected ? "is-selected" : "",
    dragOver ? "is-drag-over" : "",
  ].join(" ").trim();

  return (
    <button
      className={cls}
      onClick={onClick}
      draggable={true}
      onDragStart={(e) => {
        e.dataTransfer.setData("text/plain", String(juror.id));
        e.dataTransfer.effectAllowed = "move";
      }}
      onContextMenu={(e) => { e.preventDefault(); onContextMenu && onContextMenu(juror, e.clientX, e.clientY); }}
      {...dropProps}
    >
      <span className="seat-stripe" aria-hidden="true"></span>
      <header className="seat-eyebrow">
        <span className="seat-num">{String(seatNo).padStart(2,"0")}</span>
        <span className="seat-eyebrow-right">
          <RatingArrows rating={juror.rating} />
          <span className="seat-jid">Juror #{juror.id}</span>
        </span>
      </header>
      <div className="seat-text">
        <div className="seat-name">{juror.name}</div>
        {juror.keywords && (
          <div className="seat-keywords" title={juror.keywords}>{juror.keywords}</div>
        )}
      </div>
      <div className="seat-age">Age {juror.age}</div>
      <footer className={"seat-status seat-status-" + juror.status}>{statusText}</footer>
    </button>
  );
}

function seatNum(r, c, rows, cols, corner) {
  switch (corner) {
    case "TR": return r * cols + (cols - 1 - c) + 1;
    case "BL": return (rows - 1 - r) * cols + c + 1;
    case "BR": return (rows - 1 - r) * cols + (cols - 1 - c) + 1;
    default:   return r * cols + c + 1; // TL
  }
}

function SeatGrid({ rows, cols, corner, jurors, selectedSeat, onSelectSeat, onDropJuror, onJurorContextMenu }) {
  const bySeat = {};
  jurors.forEach(j => { if (j.seat) bySeat[j.seat] = j; });

  const cells = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const seatNo = seatNum(r, c, rows, cols, corner || "TL");
      cells.push(
        <Seat
          key={seatNo}
          seatNo={seatNo}
          juror={bySeat[seatNo]}
          selected={selectedSeat === seatNo}
          onClick={() => onSelectSeat(seatNo)}
          onDropJuror={onDropJuror}
          onContextMenu={onJurorContextMenu}
        />
      );
    }
  }

  return (
    <div className="seat-grid-wrap">
      <div
        className="seat-grid"
        style={{
          gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
          gridTemplateRows: `repeat(${rows}, minmax(0, 1fr))`,
        }}
      >
        {cells}
      </div>
    </div>
  );
}

Object.assign(window, { Seat, SeatGrid, RatingArrows });
