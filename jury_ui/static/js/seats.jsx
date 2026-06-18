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

// Seat tile.  Pointer-Events drag replaces the HTML5 Drag API so that
// touch input (finger on tablet) works identically to mouse.  Both empty
// and occupied tiles carry data-dropzone / data-seat-no so the drag
// engine can find them via elementFromPoint during a drag.
const Seat = React.memo(function Seat({
  seatNo, juror, selected, onSelectSeat, onDrop, onContextMenu, dragEnabled,
}) {
  const handleClick = React.useCallback(() => {
    if (pointerDrag.shouldSuppressClick()) return;
    if (onSelectSeat) onSelectSeat(seatNo);
  }, [onSelectSeat, seatNo]);

  const handlePointerDown = juror && dragEnabled
    ? (e) => {
        pointerDrag.start(juror.id, e, e.currentTarget, (zone, data) => {
          if (onDrop) onDrop(juror.id, zone, data);
        });
      }
    : undefined;

  if (!juror) {
    return (
      <button
        className="seat seat-empty"
        onClick={handleClick}
        aria-label={`Seat ${seatNo}, empty`}
        data-dropzone="seat"
        data-seat-no={seatNo}
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
    selected        ? "is-selected"  : "",
    dragEnabled     ? "is-draggable" : "",
  ].filter(Boolean).join(" ");

  return (
    <button
      className={cls}
      onClick={handleClick}
      onPointerDown={handlePointerDown}
      onContextMenu={(e) => { e.preventDefault(); onContextMenu && onContextMenu(juror, e.clientX, e.clientY); }}
      data-dropzone="seat"
      data-seat-no={seatNo}
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
});

function seatNum(r, c, rows, cols, corner) {
  switch (corner) {
    case "TR": return r * cols + (cols - 1 - c) + 1;
    case "BL": return (rows - 1 - r) * cols + c + 1;
    case "BR": return (rows - 1 - r) * cols + (cols - 1 - c) + 1;
    default:   return r * cols + c + 1; // TL
  }
}

const SeatGrid = React.memo(function SeatGrid({
  rows, cols, corner, bySeat, selectedSeat,
  onSelectSeat, onDrop, onJurorContextMenu, dragEnabled,
}) {
  const cells = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const seatNo = seatNum(r, c, rows, cols, corner || "TL");
      const juror = bySeat[seatNo];
      cells.push(
        <Seat
          key={juror ? `j${juror.id}` : `s${seatNo}`}
          seatNo={seatNo}
          juror={juror}
          selected={selectedSeat === seatNo}
          onSelectSeat={onSelectSeat}
          onDrop={onDrop}
          onContextMenu={onJurorContextMenu}
          dragEnabled={dragEnabled}
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
});

Object.assign(window, { Seat, SeatGrid, RatingArrows });
