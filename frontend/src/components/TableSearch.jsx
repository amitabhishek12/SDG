import { useState } from "react";
import { searchTables } from "../api";

// Lets the user type any table name. On search it resolves against the catalog:
// exact match -> calls onResolved(table); otherwise shows up to 5 suggestions.
export default function TableSearch({ erpId, onResolved }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState(null); // "exact" | "suggestions" | "none"
  const [matches, setMatches] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [llmHint, setLlmHint] = useState(false);

  const run = async () => {
    const q = query.trim();
    if (!q) return;
    setBusy(true);
    setErr("");
    setStatus(null);
    setMatches([]);
    setLlmHint(false);
    try {
      const res = await searchTables(erpId, q);
      setStatus(res.status);
      if (res.status === "exact") {
        onResolved(res.table);
      } else if (res.status === "suggestions") {
        setMatches(res.matches);
      } else {
        // none — if backend says source is "llm", the exact query can still be tried
        setLlmHint(res.source === "llm");
      }
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="table-search">
      <label>
        Table name
        <div className="search-row">
          <input
            type="text"
            placeholder="e.g. MARA, KNA1, VBAK…"
            value={query}
            onChange={(e) => setQuery(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && run()}
          />
          <button className="primary" disabled={!query.trim() || busy} onClick={run}>
            {busy ? "Searching…" : "Search"}
          </button>
        </div>
      </label>

      {err && <div className="banner error">{err}</div>}

      {status === "suggestions" && (
        <div className="suggestions">
          <p className="hint">
            No exact match. Did you mean one of these?
          </p>
          <ul className="suggestion-list">
            {matches.map((m) => (
              <li key={m.table}>
                <button className="suggestion" onClick={() => onResolved(m.table)}>
                  <strong>{m.table}</strong>
                  <span>{m.description}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {status === "none" && !llmHint && (
        <div className="banner warn">
          No table matching “{query}” was found in the catalog. Try a different
          name, or use a suggested table.
        </div>
      )}

      {status === "none" && llmHint && (
        <div className="subpanel">
          <div className="banner warn">
            “{query}” isn’t in the catalog, but AI schema inference is available.
          </div>
          <button className="primary" onClick={() => onResolved(query.trim())}>
            Infer “{query}” with AI
          </button>
        </div>
      )}
    </div>
  );
}
