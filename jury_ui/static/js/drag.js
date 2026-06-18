/* Pointer drag engine — replaces the HTML5 Drag-and-Drop API.
 *
 * The HTML5 API fires only on mouse input.  PointerEvents (pointerdown /
 * pointermove / pointerup) unify mouse, touch, and stylus — Qt WebEngine
 * (Chromium) supports them fully, so juror tiles can be dragged with a
 * finger on a 2-in-1 tablet.
 *
 * Usage
 * -----
 *   pointerDrag.start(jid, pointerEvent, sourceElement, onDrop)
 *
 *   jid         — juror id being dragged
 *   pointerEvent— the native or React onPointerDown event object
 *   sourceElement — DOM node to clone as the drag ghost
 *   onDrop(zone, data) — called on a successful drop:
 *       zone  — value of data-dropzone on the nearest drop-zone ancestor
 *       data  — { seatNo: number | null }
 *
 * A drag activates only after the pointer moves THRESHOLD px.  Short
 * taps/clicks fire normally.  After an activated drag completes the next
 * click on any element is suppressed to prevent ghost-clicks on touch.
 *
 * Drop zones are any DOM elements with a data-dropzone attribute:
 *   data-dropzone="seat"       data-seat-no="<n>"
 *   data-dropzone="pool"
 *   data-dropzone="excused"
 *   data-dropzone="struck-def"
 *   data-dropzone="struck-pro"
 *   data-dropzone="struck-both"
 *   data-dropzone="final"
 */
(function () {
  "use strict";

  var THRESHOLD = 8; // px before ghost appears and drag is "active"

  var _active    = false;
  var _started   = false; // threshold crossed?
  var _pointerId = null;
  var _ghost     = null;
  var _overZone  = null;
  var _onDrop    = null;
  var _sourceEl  = null;
  var _startX = 0, _startY = 0;
  var _offsetX = 0, _offsetY = 0;
  var _suppressNextClick = false;

  // ── Ghost ────────────────────────────────────────────────────────────────

  function _createGhost(el) {
    var rect = el.getBoundingClientRect();
    var g = el.cloneNode(true);
    g.classList.remove("is-selected", "is-drag-over");
    g.setAttribute("aria-hidden", "true");
    g.setAttribute("tabindex", "-1");
    g.style.cssText = [
      "position:fixed",
      "pointer-events:none",
      "z-index:9999",
      "opacity:0.88",
      "transition:none",
      "will-change:left,top",
      "transform:scale(1.05) rotate(1.5deg)",
      "box-shadow:0 12px 32px rgba(0,0,0,0.45),0 2px 8px rgba(0,0,0,0.3)",
      "left:"  + rect.left   + "px",
      "top:"   + rect.top    + "px",
      "width:" + rect.width  + "px",
      "height:"+ rect.height + "px",
    ].join(";");
    document.body.appendChild(g);
    return g;
  }

  // ── Drop-zone tracking ───────────────────────────────────────────────────

  function _findZone(x, y) {
    // Hide ghost so it doesn't intercept the hit test.
    if (_ghost) _ghost.style.visibility = "hidden";
    var el = document.elementFromPoint(x, y);
    if (_ghost) _ghost.style.visibility = "";
    return el ? el.closest("[data-dropzone]") : null;
  }

  function _setOver(zone) {
    if (_overZone === zone) return;
    if (_overZone) _overZone.classList.remove("is-drag-over");
    _overZone = zone;
    if (_overZone) _overZone.classList.add("is-drag-over");
  }

  // ── Cleanup ───────────────────────────────────────────────────────────────

  function _cleanup() {
    if (_ghost) { _ghost.remove(); _ghost = null; }
    _setOver(null);
    document.body.style.userSelect = "";
    document.body.style.cursor = "";
    _active = false;
    _started = false;
    _pointerId = null;
    _onDrop = null;
    _sourceEl = null;
  }

  // ── Pointer event handlers ────────────────────────────────────────────────

  function _onMove(ev) {
    if (ev.pointerId !== _pointerId) return;
    var x = ev.clientX, y = ev.clientY;

    if (!_started) {
      var dx = x - _startX, dy = y - _startY;
      if (dx * dx + dy * dy < THRESHOLD * THRESHOLD) return;
      _started = true;
      _ghost = _createGhost(_sourceEl);
      document.body.style.userSelect = "none";
      document.body.style.cursor = "grabbing";
    }

    _ghost.style.left = (x - _offsetX) + "px";
    _ghost.style.top  = (y - _offsetY) + "px";
    _setOver(_findZone(x, y));
  }

  function _onUp(ev) {
    if (ev.pointerId !== _pointerId) return;
    document.removeEventListener("pointermove",   _onMove);
    document.removeEventListener("pointerup",     _onUp);
    document.removeEventListener("pointercancel", _onUp);

    var dropped  = _started && _overZone !== null;
    var zone     = _overZone;
    var callback = _onDrop;

    // Suppress the synthetic click that fires after touch-release so a
    // completed drag doesn't also trigger a seat selection.
    if (_started) {
      _suppressNextClick = true;
      setTimeout(function () { _suppressNextClick = false; }, 400);
    }

    _cleanup();

    if (dropped && zone && callback) {
      var ds = zone.dataset;
      callback(ds.dropzone, {
        seatNo: ds.seatNo ? parseInt(ds.seatNo, 10) : null,
      });
    }
  }

  // ── Public API ────────────────────────────────────────────────────────────

  /**
   * Begin tracking a potential drag gesture.
   * Call from an element's onPointerDown handler.
   */
  function start(jid, ev, sourceEl, onDrop) {
    if (_active) return;
    // Ignore non-primary buttons (right-click, middle-click).
    if (ev.button != null && ev.button !== 0) return;

    _active    = true;
    _started   = false;
    _pointerId = ev.pointerId;
    _onDrop    = onDrop;
    _sourceEl  = sourceEl;

    var rect = sourceEl.getBoundingClientRect();
    _startX  = ev.clientX;
    _startY  = ev.clientY;
    _offsetX = ev.clientX - rect.left;
    _offsetY = ev.clientY - rect.top;

    document.addEventListener("pointermove",   _onMove);
    document.addEventListener("pointerup",     _onUp);
    document.addEventListener("pointercancel", _onUp);
  }

  /** True while a drag gesture is in progress (threshold may not be crossed yet). */
  function isActive() { return _active; }

  /** True in the 400 ms window after a completed drag — use to suppress click. */
  function shouldSuppressClick() { return _suppressNextClick; }

  window.pointerDrag = { start: start, isActive: isActive, shouldSuppressClick: shouldSuppressClick };
})();
