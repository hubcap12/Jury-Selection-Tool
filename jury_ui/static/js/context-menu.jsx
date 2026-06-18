/* Custom context menu for juror rows and seats */

function ContextMenu({ juror, x, y, scale = 1, onClose,
                        onSetStatus, onSetRating,
                        onMarkFinal, onUnmarkFinal,
                        onUnseat, onEdit }) {
  const ref = React.useRef(null);

  // Adjust position so the menu never goes off-screen.
  //
  // The menu is `position: fixed` inside #root, which carries the global
  // `zoom: var(--ui-scale)`.  A fixed element's `left`/`top` are multiplied
  // by that zoom, while pointer clientX/Y and getBoundingClientRect both
  // report real (viewport) pixels.  So we compute the desired on-screen
  // position in real px, then divide by the scale to get the `left`/`top`
  // value that renders there.
  React.useLayoutEffect(() => {
    if (!ref.current) return;
    const Z   = scale || 1;
    const r   = ref.current.getBoundingClientRect();
    const vw  = window.innerWidth;
    const vh  = window.innerHeight;
    const renderLeft = (r.right  > vw) ? x - r.width  : x;
    const renderTop  = (r.bottom > vh) ? y - r.height : y;
    ref.current.style.left = (renderLeft / Z) + "px";
    ref.current.style.top  = (renderTop  / Z) + "px";
  }, []);

  // Close on outside click or Escape
  React.useEffect(() => {
    const onDown = (e) => { if (ref.current && !ref.current.contains(e.target)) onClose(); };
    const onKey  = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown",     onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown",     onKey);
    };
  }, []);

  const status   = juror.status || "pool";
  const isFinal  = status === "final";
  const rating   = juror.rating || 0;
  const ratingGlyph = rating > 0 ? "▲".repeat(rating)
                    : rating < 0 ? "▼".repeat(-rating) : "";

  const act = (fn) => () => { fn(); onClose(); };

  const Item = ({ label, onClick, disabled, active }) => (
    <button
      className={"ctx-item" + (disabled ? " ctx-disabled" : "") + (active ? " ctx-active" : "")}
      onClick={disabled ? undefined : act(onClick)}
    >{label}</button>
  );
  const Sep = () => <div className="ctx-sep" />;

  return (
    <div ref={ref} className="ctx-menu" style={{ left: x / (scale || 1), top: y / (scale || 1) }}>

      {/* Header */}
      <div className="ctx-header">
        <span className="ctx-header-name">{juror.name}</span>
        {ratingGlyph && <span className={"ctx-header-rating " + (rating > 0 ? "ctx-up" : "ctx-down")}>{ratingGlyph}</span>}
      </div>

      {/* Priority row */}
      <div className="ctx-priority-row">
        <span className="ctx-priority-lbl">Priority:</span>
        <div className="ctx-priority-btns">
          {[3,2,1].map(v => (
            <button key={v}
              className={"ctx-prio-btn ctx-prio-up" + (rating===v ? " is-active" : "")}
              onClick={act(() => onSetRating(juror.id, rating === v ? 0 : v))}>
              {"▲".repeat(v)}
            </button>
          ))}
          <button
            className={"ctx-prio-btn ctx-prio-clear" + (rating===0 ? " is-active" : "")}
            onClick={act(() => onSetRating(juror.id, 0))}>—</button>
          {[-1,-2,-3].map(v => (
            <button key={v}
              className={"ctx-prio-btn ctx-prio-down" + (rating===v ? " is-active" : "")}
              onClick={act(() => onSetRating(juror.id, rating === v ? 0 : v))}>
              {"▼".repeat(-v)}
            </button>
          ))}
        </div>
      </div>

      <Sep />

      <Item label={isFinal ? "Remove from Final Jury" : "Add to Final Jury"}
            onClick={() => isFinal ? onUnmarkFinal(juror.id) : onMarkFinal(juror.id)} />

      <Sep />

      {status !== "pool" && (
        <Item label="Return to Pool" onClick={() => onUnseat(juror.id)} />
      )}
      <Item label="Excuse  (for cause)"   onClick={() => onSetStatus(juror.id, "excused")}    disabled={status === "excused"}    active={status === "excused"} />
      <Item label="Strike — Defense"      onClick={() => onSetStatus(juror.id, "struck_def")} disabled={status === "struck_def"} active={status === "struck_def"} />
      <Item label="Strike — Prosecution"  onClick={() => onSetStatus(juror.id, "struck_pro")} disabled={status === "struck_pro"} active={status === "struck_pro"} />
      <Item label="Strike — Both"         onClick={() => onSetStatus(juror.id, "struck_both")} disabled={status === "struck_both"} active={status === "struck_both"} />

      <Sep />

      <Item label="Edit Notes…" onClick={() => onEdit(juror)} />
    </div>
  );
}

Object.assign(window, { ContextMenu });
