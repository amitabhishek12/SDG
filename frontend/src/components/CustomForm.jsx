import { useEffect, useState } from "react";

const FALLBACK_TYPES = [
  "CHAR",
  "NUMC",
  "DEC",
  "CURR",
  "QUAN",
  "INT",
  "DATS",
  "TIMS",
  "LANG",
  "CUKY",
  "UNIT",
];

function blankRow() {
  return { field_name: "", key: false, data_type: "CHAR", length: 10 };
}

export default function CustomForm({ fieldCount, dataTypes, onSubmit }) {
  const types = dataTypes?.length ? dataTypes : FALLBACK_TYPES;
  const [rows, setRows] = useState(() =>
    Array.from({ length: fieldCount }, blankRow)
  );

  // Resize the form when the requested field count changes.
  useEffect(() => {
    setRows((prev) => {
      const next = prev.slice(0, fieldCount);
      while (next.length < fieldCount) next.push(blankRow());
      return next;
    });
  }, [fieldCount]);

  const update = (i, patch) =>
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  const valid = rows.every((r) => r.field_name.trim() && r.length >= 1);

  return (
    <div className="custom-form">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Field name</th>
              <th>Key</th>
              <th>Data type</th>
              <th>Length</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td>
                  <input
                    value={r.field_name}
                    placeholder={`field_${i + 1}`}
                    onChange={(e) =>
                      update(i, { field_name: e.target.value })
                    }
                  />
                </td>
                <td className="center">
                  <input
                    type="checkbox"
                    checked={r.key}
                    onChange={(e) => update(i, { key: e.target.checked })}
                  />
                </td>
                <td>
                  <select
                    value={r.data_type}
                    onChange={(e) => update(i, { data_type: e.target.value })}
                  >
                    {types.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    min={1}
                    max={4000}
                    value={r.length}
                    onChange={(e) =>
                      update(i, { length: Number(e.target.value) })
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="actions">
        <button
          className="primary"
          disabled={!valid}
          onClick={() =>
            onSubmit(
              rows.map((r) => ({
                field_name: r.field_name.trim(),
                key: r.key,
                data_type: r.data_type,
                length: Number(r.length),
              }))
            )
          }
        >
          Use this schema
        </button>
      </div>
    </div>
  );
}
