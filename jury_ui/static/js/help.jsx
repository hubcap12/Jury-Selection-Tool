/* Help modal — Quick Start · Shortcuts · About */

function HelpModal({ initialTab, onClose }) {
  const [tab, setTab] = React.useState(initialTab || "quickstart");

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal modal-help" onClick={e => e.stopPropagation()}>
        <div className="modal-head">
          <h2 className="modal-title">Help</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="help-tabs">
          {[["quickstart","Quick Start"],["shortcuts","Shortcuts"],["about","About"]].map(([id, label]) => (
            <button key={id}
              className={"help-tab" + (tab === id ? " is-active" : "")}
              onClick={() => setTab(id)}>
              {label}
            </button>
          ))}
        </div>

        <div className="modal-body help-body">
          {tab === "quickstart" && <HelpQuickStart />}
          {tab === "shortcuts"  && <HelpShortcuts />}
          {tab === "about"      && <HelpAbout />}
        </div>
      </div>
    </div>
  );
}

function HelpQuickStart() {
  const steps = [
    ["Add jurors",
     "Click “Add Juror” in the left panel. Enter the juror’s name and optional age, keywords, and notes."],
    ["Seat jurors",
     "Drag a juror from the Preliminary Pool onto any seat in the grid, or use “Auto Seat” to fill empty seats automatically. Drag from seat to seat to swap."],
    ["View details",
     "Click any juror (seated or in pool) to open their detail panel on the right. Keywords and notes save automatically when you click away."],
    ["Set priority",
     "Use the ▲/▼ buttons in the detail panel to rate a juror from +3 (strongly favor) to −3 (strongly against). The — button in the middle clears the rating."],
    ["Set status",
     "Use the status pills in the detail panel to mark a juror as Excused, Defense Strike, Prosecution Strike, Both Struck, or Final Juror."],
    ["Final jury",
     "Mark jurors “Final” to lock in the jury. They auto-number in selection order. Use the jury size setting to distinguish jurors from alternates."],
    ["Multiple panels",
     "Use the Panel 1 / 2 / 3 tabs to track separate seating rounds or alternate configurations. Each panel has independent seat assignments."],
    ["Save your work",
     "File → Save (Ctrl+S) writes a .json file you can reopen later. Both the classic and new UIs share the same file format."],
    ["Export PDF",
     "File → Export PDF generates a printable jury report with all juror details, statuses, and notes."],
    ["Upload CSV",
     "File → Upload CSV to bulk-import jurors. Columns: name, age, keywords, notes. A header row is optional; lines starting with # are skipped."],
  ];

  return (
    <div className="help-steps">
      {steps.map(([title, desc], i) => (
        <div key={i} className="help-step">
          <div className="help-step-num">{i + 1}</div>
          <div className="help-step-body">
            <div className="help-step-title">{title}</div>
            <div className="help-step-desc">{desc}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function HelpShortcuts() {
  const groups = [
    ["File", [
      ["Ctrl+S",         "Save"],
      ["Ctrl+Shift+S",   "Save As"],
      ["Ctrl+O",         "Open file"],
      ["Ctrl+,",         "Preferences"],
    ]],
    ["Notes editor", [
      ["Ctrl+B", "Bold"],
      ["Ctrl+I", "Italic"],
      ["Ctrl+U", "Underline"],
    ]],
    ["Help", [
      ["F1", "This help window"],
    ]],
  ];

  return (
    <div className="help-shortcuts">
      {groups.map(([group, rows]) => (
        <div key={group} className="help-shortcut-group">
          <div className="help-shortcut-heading">{group}</div>
          <table className="help-shortcut-table">
            <tbody>
              {rows.map(([keys, desc]) => (
                <tr key={keys}>
                  <td><kbd className="kbd">{keys}</kbd></td>
                  <td className="help-shortcut-desc">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

function HelpAbout() {
  return (
    <div className="help-about">
      <div className="help-about-logo" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="52" height="52">
          <path d="M4 5h16M6 5v9a6 6 0 0 0 12 0V5M9 19h6M12 19v3"
            fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      </div>
      <div className="help-about-name">Jury Selection Tool</div>
      <div className="help-about-version">Version 1.1.0</div>
      <div className="help-about-publisher">Cole Mason</div>
      <div className="help-about-divider"></div>
      <p className="help-about-desc">
        A desktop tool for managing and tracking juror seating, strikes,
        and final selections during jury selection proceedings.
      </p>
      <p className="help-about-desc">
        Save files are plain JSON and load in both the classic (Tk) and
        new (webview) frontends interchangeably.
      </p>
    </div>
  );
}

Object.assign(window, { HelpModal });
