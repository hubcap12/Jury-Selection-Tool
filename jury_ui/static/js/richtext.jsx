/* RichTextEditor — contenteditable with B/I/U + bullets.
   Serialises to/from the same "runs" format the Tk app uses:

     plain text                     → "some text"
     formatted                      → JSON: [{"text":"...","bold":true,...}, ...]

   Round-trips through `app/richtext.py::_notes_to_runs` cleanly so the
   Tk app reads / writes the same notes. */

const RTE_FONTS = ["Helvetica", "Arial", "Times New Roman",
                   "Courier New", "Georgia", "Verdana", "Calibri"];

// ── Parse / serialise ───────────────────────────────────────────────────────

function parseNotes(notes) {
  if (!notes) return [];
  const s = String(notes);
  if (s.trim().startsWith("[")) {
    try {
      const arr = JSON.parse(s);
      if (Array.isArray(arr)) return arr;
    } catch (e) { /* fall through */ }
  }
  return [{ text: s }];
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function runsToHtml(runs) {
  if (!runs.length) return "";
  return runs.map(r => {
    if (!r.text) return "";
    let html = escapeHtml(r.text).replace(/\n/g, "<br>");
    if (r.underline) html = `<u>${html}</u>`;
    if (r.italic)    html = `<em>${html}</em>`;
    if (r.bold)      html = `<strong>${html}</strong>`;
    if (r.font && RTE_FONTS.includes(r.font)) {
      html = `<span data-rte-font="${r.font}" style="font-family:${r.font},sans-serif">${html}</span>`;
    }
    return html;
  }).join("");
}

function _walk(node, fmt, runs) {
  if (node.nodeType === 3 /* text */) {
    if (node.textContent) runs.push({ text: node.textContent, ...fmt });
    return;
  }
  if (node.nodeType !== 1 /* element */) return;
  const tag = node.tagName.toLowerCase();
  if (tag === "br") { runs.push({ text: "\n", ...fmt }); return; }
  if (tag === "li") {
    // Bullets become literal "• " + content + \n so PDF/Tk see them as text.
    runs.push({ text: "• ", ...fmt });
    for (const c of node.childNodes) _walk(c, fmt, runs);
    runs.push({ text: "\n", ...fmt });
    return;
  }
  const inner = { ...fmt };
  if (tag === "strong" || tag === "b") inner.bold = true;
  if (tag === "em"     || tag === "i") inner.italic = true;
  if (tag === "u")                     inner.underline = true;
  if (node.dataset && node.dataset.rteFont) inner.font = node.dataset.rteFont;
  for (const c of node.childNodes) _walk(c, inner, runs);
  // Block-level: insert a newline after if there isn't one already.
  if ((tag === "div" || tag === "p") && node.nextSibling) {
    const last = runs[runs.length - 1];
    if (!last || !last.text.endsWith("\n")) {
      runs.push({ text: "\n", ...fmt });
    }
  }
}

function htmlToRuns(el) {
  const runs = [];
  for (const c of el.childNodes) _walk(c, {}, runs);
  // Merge adjacent runs that share formatting.
  const merged = [];
  const sameFmt = (a, b) =>
    !!a.bold === !!b.bold &&
    !!a.italic === !!b.italic &&
    !!a.underline === !!b.underline &&
    (a.font || null) === (b.font || null);
  for (const r of runs) {
    if (!r.text) continue;
    if (merged.length && sameFmt(merged[merged.length - 1], r)) {
      merged[merged.length - 1].text += r.text;
    } else {
      merged.push({ ...r });
    }
  }
  return merged;
}

function runsToNotes(runs) {
  if (!runs.length) return "";
  // If nothing has formatting, return plain text — matches Tk app's
  // _notes_to_runs round-trip and keeps files diff-friendly.
  const hasFmt = runs.some(r => r.bold || r.italic || r.underline || r.font);
  if (!hasFmt) return runs.map(r => r.text).join("");
  return JSON.stringify(runs);
}

// ── Editor component ────────────────────────────────────────────────────────

function RichTextEditor({ value, onSave, placeholder }) {
  const ref       = React.useRef(null);
  const [toolbar, setToolbar] = React.useState({ bold: false, italic: false, underline: false });
  // Sentinel so the mount-effect always runs, even when value === "".
  const lastValueRef = React.useRef(undefined);
  // Pending debounce timer for keystroke-driven saves.
  const saveTimerRef = React.useRef(null);

  // Mount + reload when external value changes (juror swap, file load).
  React.useEffect(() => {
    if (!ref.current) return;
    if (lastValueRef.current !== value) {
      lastValueRef.current = value;
      ref.current.innerHTML = runsToHtml(parseNotes(value || ""));
    }
  }, [value]);

  // Flush any pending debounced save on unmount so we never lose keystrokes.
  React.useEffect(() => () => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
      fireSaveNow();
    }
  }, []);

  const refreshToolbar = () => {
    setToolbar({
      bold:      document.queryCommandState("bold"),
      italic:    document.queryCommandState("italic"),
      underline: document.queryCommandState("underline"),
    });
  };

  // Immediate save — used by toolbar commands and onBlur, where the user has
  // signalled an explicit pause point.
  const fireSaveNow = () => {
    if (!ref.current || !onSave) return;
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }
    const notes = runsToNotes(htmlToRuns(ref.current));
    lastValueRef.current = notes;
    onSave(notes);
  };

  // Debounced save — used by onInput so we don't round-trip to Python on every
  // keystroke.  400ms is short enough to feel instant but long enough that a
  // burst of typing collapses into a single save.
  const fireSaveDebounced = () => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      saveTimerRef.current = null;
      fireSaveNow();
    }, 400);
  };

  const cmd = (name, arg) => {
    document.execCommand(name, false, arg);
    ref.current.focus();
    refreshToolbar();
    fireSaveNow();
  };

  // Back-compat alias for any older call sites.
  const fireSave = fireSaveNow;

  const onInput = () => { fireSaveDebounced(); };
  const onKey   = () => { setTimeout(refreshToolbar, 0); };
  const onSel   = () => { refreshToolbar(); };

  const clearFmt = () => {
    cmd("removeFormat");
    cmd("unlink");
    // removeFormat doesn't drop list wrappers; convert UL back to plain.
    document.execCommand("insertUnorderedList", false); // toggles off if on
  };

  return (
    <div className="rte">
      <div className="rte-toolbar">
        <button
          type="button"
          className={"rte-btn" + (toolbar.bold ? " is-active" : "")}
          onMouseDown={(e) => { e.preventDefault(); cmd("bold"); }}
          title="Bold (Ctrl+B)"
        ><b>B</b></button>
        <button
          type="button"
          className={"rte-btn" + (toolbar.italic ? " is-active" : "")}
          onMouseDown={(e) => { e.preventDefault(); cmd("italic"); }}
          title="Italic (Ctrl+I)"
        ><i>I</i></button>
        <button
          type="button"
          className={"rte-btn" + (toolbar.underline ? " is-active" : "")}
          onMouseDown={(e) => { e.preventDefault(); cmd("underline"); }}
          title="Underline (Ctrl+U)"
        ><u>U</u></button>
        <span className="rte-sep"></span>
        <button
          type="button"
          className="rte-btn"
          onMouseDown={(e) => { e.preventDefault(); cmd("insertUnorderedList"); }}
          title="Bullet list"
        >•</button>
        <span className="rte-sep"></span>
        <button
          type="button"
          className="rte-btn rte-btn-text"
          onMouseDown={(e) => { e.preventDefault(); clearFmt(); }}
          title="Strip formatting from selection"
        >Clear fmt</button>
      </div>
      <div
        ref={ref}
        className="rte-content"
        contentEditable
        suppressContentEditableWarning={true}
        data-placeholder={placeholder || ""}
        onInput={onInput}
        onKeyUp={onKey}
        onMouseUp={onSel}
        onBlur={fireSaveNow}
        spellCheck={true}
      ></div>
    </div>
  );
}

Object.assign(window, { RichTextEditor, parseNotes, runsToNotes, htmlToRuns, runsToHtml });
