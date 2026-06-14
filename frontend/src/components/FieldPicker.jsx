import { useMemo, useState } from "react";

// Shows every field of a resolved table with checkboxes.
// Key fields are preselected by default. The user confirms a subset, which
// becomes the schema sent to preview/generate.
export default function FieldPicker({ table, description, source, fields, onConfirm, onBack }) {
  const [selected, setSelected] = useState(() => {
    const init = {};
    for (const f of fields) init[f.field_name] = !!f.key;
    return init;
  });

  const selectedCount = useMemo(
    () => Object.values(selected).filter(Boolean).length,
    [selected]
  );

  const toggle = (name) =>
    setSelected((s) => ({ ...s, [name]: !s[name] }));

  const setAll = (val) =>
    setSelected(Object.fromEntries(fields.map((f) => [f.field_name, val])));

  const confirm = () => {
    const chosen = fields.filter((f) => selected[f.field_name]);
    onConfirm(chosen);
  };

  return (
    <div className="field-picker">
      <div className="picker-head">
        <div>
          <h3>
            {table}
            {source && <span className="source-tag">{source}</span>}
          </h3>
          {description && <p className="hint">{description}</p>}
        </div>
        <div className="picker-actions">
          <button className="ghost" onClick={() => setAll(true)}>
            Select all
          </button>
          <button className="ghost" onClick={() => setAll(false)}>
            Clear
          </button>
        </div>
      </div>

      <p className="hint">
        Select the fields you need. Key fields are selected by default.
      </p>

      <div className="field-list">
        <div className="field-row header">
          <span className="col-check" />
          <span className="col-name">Field</span>
          <span className="col-type">Type</span>
          <span className="col-len">Length</span>
          <span className="col-key">Key</span>
        </div>
        {fields.map((f) => (
          <label className="field-row" key={f.field_name}>
            <span className="col-check">
              <input
                type="checkbox"
                checked={!!selected[f.field_name]}
                onChange={() => toggle(f.field_name)}
              />
            </span>
            <span className="col-name">
              {f.field_name}
              {f.notes && <em className="field-note">{f.notes}</em>}
            </span>
            <span className="col-type">{f.data_type}</span>
            <span className="col-len">{f.length ?? "—"}</span>
            <span className="col-key">{f.key ? "🔑" : ""}</span>
          </label>
        ))}
      </div>

      <div className="picker-footer">
        <button className="ghost" onClick={onBack}>
          ← Back
        </button>
        <div className="picker-footer-right">
          <span className="hint">{selectedCount} selected</span>
          <button
            className="primary"
            disabled={selectedCount === 0}
            onClick={confirm}
          >
            Use these fields
          </button>
        </div>
      </div>
    </div>
  );
}
