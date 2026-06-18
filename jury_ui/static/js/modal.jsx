/* Modal — used for Add / Edit juror.
   Renders a centered overlay; click backdrop or press Esc to dismiss. */

function Modal({ title, onClose, children, footer }) {
  React.useEffect(() => {
    const fn = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", fn);
    return () => document.removeEventListener("keydown", fn);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onPointerDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal" role="dialog" aria-modal="true">
        <header className="modal-head">
          <h2 className="modal-title">{title}</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </header>
        <div className="modal-body">{children}</div>
        {footer && <footer className="modal-foot">{footer}</footer>}
      </div>
    </div>
  );
}

function JurorFormModal({ mode, initial, onSubmit, onClose }) {
  const [name, setName]         = React.useState(initial?.name || "");
  const [age, setAge]           = React.useState(initial?.age ?? "");
  const [keywords, setKeywords] = React.useState(initial?.keywords || "");
  const [notes, setNotes]       = React.useState(initial?.notes || "");
  const nameRef = React.useRef(null);

  React.useEffect(() => { nameRef.current?.focus(); nameRef.current?.select(); }, []);

  const submit = () => {
    if (!name.trim()) { nameRef.current?.focus(); return; }
    onSubmit({ name: name.trim(), age, keywords, notes });
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit();
  };

  const title = mode === "edit" ? `Edit Juror #${initial?.id ?? ""}` : "Add Juror";

  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-default" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit}>
            {mode === "edit" ? "Save" : "Add"}
          </button>
        </>
      }
    >
      <div className="form-grid" onKeyDown={onKeyDown}>
        <label className="form-label">Name</label>
        <input ref={nameRef} className="input" value={name}
               onChange={(e) => setName(e.target.value)} placeholder="Full name"/>

        <label className="form-label">Age</label>
        <input className="input input-num" value={age} type="number" min="0" max="120"
               onChange={(e) => setAge(e.target.value)} placeholder=""/>

        <label className="form-label">Keywords</label>
        <input className="input" value={keywords}
               onChange={(e) => setKeywords(e.target.value)}
               placeholder="e.g. fireman, trucker"/>

        <label className="form-label form-label-top">Notes</label>
        <textarea className="form-textarea" rows={5} value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Free-text notes…"/>
      </div>
    </Modal>
  );
}

function ConfirmModal({ title, message, confirmLabel = "Confirm", danger, onConfirm, onClose }) {
  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-default" onClick={onClose}>Cancel</button>
          <button className={"btn " + (danger ? "btn-danger" : "btn-primary")}
                  onClick={() => { onConfirm(); onClose(); }}>{confirmLabel}</button>
        </>
      }
    >
      <p className="modal-msg">{message}</p>
    </Modal>
  );
}

function PromptModal({ title, message, defaultValue = "", confirmLabel = "OK",
                      placeholder = "", onConfirm, onClose }) {
  const [value, setValue] = React.useState(defaultValue);
  const inputRef = React.useRef(null);
  React.useEffect(() => { inputRef.current?.focus(); inputRef.current?.select(); }, []);
  const submit = () => { onConfirm(value); onClose(); };
  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-default" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit}>{confirmLabel}</button>
        </>
      }
    >
      {message && <p className="modal-msg">{message}</p>}
      <input
        ref={inputRef}
        className="input"
        style={{ marginTop: 10 }}
        value={value}
        placeholder={placeholder}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
      />
    </Modal>
  );
}

Object.assign(window, { Modal, JurorFormModal, ConfirmModal, PromptModal });
