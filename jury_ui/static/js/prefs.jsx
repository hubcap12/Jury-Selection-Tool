/* PreferencesModal — surfaces the subset of app.config.SETTINGS that
   makes sense in the webview UI.  Persists via window.pywebview.api
   so the Tk app and webview UI share ~/.jurytool_settings.json. */

function PrefsSection({ title, children }) {
  return (
    <div className="prefs-section">
      <h3 className="prefs-section-title">{title}</h3>
      <div className="prefs-section-body">{children}</div>
    </div>
  );
}

function PrefsRow({ label, hint, children }) {
  return (
    <div className="prefs-row">
      <label className="prefs-label">
        {label}
        {hint && <span className="prefs-hint">{hint}</span>}
      </label>
      <div className="prefs-control">{children}</div>
    </div>
  );
}

function PreferencesModal({ initial, onSave, onClose, onPickWorkDir, onSaveLayout }) {
  // ``initial`` is the full response from get_settings():
  //   { values: {...}, page_sizes, pdf_fonts, rte_fonts, corners }
  const [v, setV] = React.useState(initial.values);
  const set = (k) => (val) => setV(prev => ({ ...prev, [k]: val }));

  const submit = () => onSave(v);

  return (
    <Modal
      title="Preferences"
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-default" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit}>Save</button>
        </>
      }
    >
      <div className="prefs">
        <PrefsSection title="New jury defaults">
          <PrefsRow label="Rows">
            <input className="input input-num" type="number" min="1" max="20"
                   value={v.rows} onChange={(e) => set("rows")(parseInt(e.target.value) || 1)} />
          </PrefsRow>
          <PrefsRow label="Columns">
            <input className="input input-num" type="number" min="1" max="20"
                   value={v.cols} onChange={(e) => set("cols")(parseInt(e.target.value) || 1)} />
          </PrefsRow>
          <PrefsRow label="Jury size">
            <input className="input input-num" type="number" min="1" max="24"
                   value={v.jury_size} onChange={(e) => set("jury_size")(parseInt(e.target.value) || 1)} />
          </PrefsRow>
          <PrefsRow label="Seat #1 corner">
            <select className="select" value={v.corner}
                    onChange={(e) => set("corner")(e.target.value)}>
              {initial.corners.map(c => (
                <option key={c} value={c}>
                  {{ TL: "Top-Left", TR: "Top-Right", BL: "Bottom-Left", BR: "Bottom-Right" }[c]}
                </option>
              ))}
            </select>
          </PrefsRow>
          <PrefsRow label="Number of panels">
            <input className="input input-num" type="number" min="1" max="9"
                   value={v.num_panels} onChange={(e) => set("num_panels")(parseInt(e.target.value) || 1)} />
          </PrefsRow>
        </PrefsSection>

        <PrefsSection title="Autosave">
          <PrefsRow label="Interval" hint="minutes (0 disables)">
            <input className="input input-num" type="number" min="0" max="180"
                   value={v.autosave_interval}
                   onChange={(e) => set("autosave_interval")(parseInt(e.target.value) || 0)} />
          </PrefsRow>
          <PrefsRow label="Keep snapshots">
            <input className="input input-num" type="number" min="1" max="20"
                   value={v.autosave_keep}
                   onChange={(e) => set("autosave_keep")(parseInt(e.target.value) || 1)} />
          </PrefsRow>
        </PrefsSection>

        <PrefsSection title="PDF export">
          <PrefsRow label="Page size">
            <select className="select" value={v.pdf_page_size}
                    onChange={(e) => set("pdf_page_size")(e.target.value)}>
              {initial.page_sizes.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </PrefsRow>
          <PrefsRow label="Margin" hint="inches">
            <input className="input input-num" type="number" step="0.05" min="0.25" max="2.0"
                   value={v.pdf_margin}
                   onChange={(e) => set("pdf_margin")(parseFloat(e.target.value) || 0.75)} />
          </PrefsRow>
          <PrefsRow label="Font">
            <select className="select" value={v.pdf_font}
                    onChange={(e) => set("pdf_font")(e.target.value)}>
              {initial.pdf_fonts.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          </PrefsRow>
          <PrefsRow label="Default title">
            <input className="input" type="text" value={v.pdf_title || ""}
                   onChange={(e) => set("pdf_title")(e.target.value)}
                   placeholder="Jury Selection Report" />
          </PrefsRow>
          <PrefsRow label="Default filename">
            <input className="input" type="text" value={v.pdf_filename || ""}
                   onChange={(e) => set("pdf_filename")(e.target.value)}
                   placeholder="jury_report.pdf" />
          </PrefsRow>
          <PrefsRow label="Include summary page">
            <input type="checkbox" className="prefs-check"
                   checked={!!v.pdf_summary}
                   onChange={(e) => set("pdf_summary")(e.target.checked)} />
          </PrefsRow>
          <PrefsRow label="Hide empty seats">
            <input type="checkbox" className="prefs-check"
                   checked={!!v.pdf_hide_empty}
                   onChange={(e) => set("pdf_hide_empty")(e.target.checked)} />
          </PrefsRow>
        </PrefsSection>

        <PrefsSection title="Layout">
          <PrefsRow label="All sash positions" hint="column widths, info panel height, sidebar pane sizes">
            <button className="btn btn-default" onClick={onSaveLayout}>
              Save current as default
            </button>
          </PrefsRow>
        </PrefsSection>

        <PrefsSection title="Display">
          <PrefsRow label="UI scale" hint="size of all text and controls">
            <div className="prefs-scale">
              <input type="range" className="prefs-range"
                     min="0.8" max="1.6" step="0.05"
                     value={v.ui_scale ?? 1}
                     onChange={(e) => set("ui_scale")(parseFloat(e.target.value))} />
              <span className="prefs-scale-val">{Math.round((v.ui_scale ?? 1) * 100)}%</span>
            </div>
          </PrefsRow>
        </PrefsSection>

        <PrefsSection title="Input &amp; interaction">
          <PrefsRow label="Enable drag &amp; drop" hint="drag jurors to seats, status panes, or the final jury list">
            <input type="checkbox" className="prefs-check"
                   checked={!!v.drag_enabled}
                   onChange={(e) => set("drag_enabled")(e.target.checked)} />
          </PrefsRow>
        </PrefsSection>

        <PrefsSection title="Working directory">
          <PrefsRow label="Folder" hint="default save & autosave location">
            <div className="prefs-row-path">
              <input className="input prefs-path-input" type="text"
                     value={v.work_dir || ""}
                     onChange={(e) => set("work_dir")(e.target.value)}
                     placeholder="(uses home directory)" />
              <button className="btn btn-default prefs-pick-btn"
                      onClick={async () => {
                        const r = await onPickWorkDir();
                        if (r?.path) set("work_dir")(r.path);
                      }}>Browse…</button>
            </div>
          </PrefsRow>
        </PrefsSection>
      </div>
    </Modal>
  );
}

Object.assign(window, { PreferencesModal });
