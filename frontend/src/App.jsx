import { useEffect, useState } from "react";
import {
  downloadBlob,
  generate,
  getConfig,
  getErps,
  getErpSchema,
  getPreview,
  templateUrl,
  uploadSchema,
} from "./api";
import SchemaTable from "./components/SchemaTable.jsx";
import CustomForm from "./components/CustomForm.jsx";
import PreviewTable from "./components/PreviewTable.jsx";
import Stepper from "./components/Stepper.jsx";

const STEPS = ["Count", "Source", "Schema", "Preview", "Export"];

export default function App() {
  const [config, setConfig] = useState(null);
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [count, setCount] = useState(1000);
  const [source, setSource] = useState(null); // "erp" | "custom"
  const [erps, setErps] = useState([]);
  const [erpId, setErpId] = useState("");
  const [table, setTable] = useState("");
  const [customMethod, setCustomMethod] = useState(null); // "upload" | "form"
  const [fieldCount, setFieldCount] = useState(4);

  const [schema, setSchema] = useState(null);
  const [preview, setPreview] = useState(null);
  const [exportFmt, setExportFmt] = useState("csv");

  useEffect(() => {
    getConfig()
      .then((c) => {
        setConfig(c);
        if (c.export_formats?.length) setExportFmt(c.export_formats[0]);
      })
      .catch((e) => setError(e.message));
    getErps()
      .then(setErps)
      .catch((e) => setError(e.message));
  }, []);

  const go = (n) => {
    setError("");
    setStep(n);
  };

  const fetchErpSchema = async () => {
    setBusy(true);
    setError("");
    try {
      const s = await getErpSchema(erpId, table);
      setSchema(s);
      go(2);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const handleUpload = async (file) => {
    setBusy(true);
    setError("");
    try {
      const s = await uploadSchema(file);
      setSchema(s);
      go(2);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const handleFormSubmit = (fields) => {
    setSchema({ source: "custom", table: null, fields });
    go(2);
  };

  const runPreview = async () => {
    setBusy(true);
    setError("");
    try {
      const p = await getPreview(schema);
      setPreview(p);
      go(3);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const runGenerate = async () => {
    setBusy(true);
    setError("");
    try {
      const { blob, filename } = await generate(schema, count, exportFmt);
      downloadBlob(blob, filename);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const maxRecords = config?.max_records ?? 100000;
  const dataTypes = config?.data_types ?? [];
  const exportFormats = config?.export_formats ?? ["csv", "xlsx", "pdf", "parquet"];

  return (
    <div className="app">
      <header className="header">
        <h1>Synthetic Data Generator</h1>
        <p className="subtitle">
          Define a schema from a standard ERP table or a custom dataset, preview
          a sample, then generate and export records.
        </p>
        {config && !config.llm_enabled && (
          <div className="banner warn">
            LLM features are disabled (no OPENAI_API_KEY). ERP schema inference
            is unavailable; custom datasets use Faker generation.
          </div>
        )}
      </header>

      <Stepper steps={STEPS} current={step} />

      {error && <div className="banner error">{error}</div>}

      <main className="card">
        {step === 0 && (
          <section>
            <h2>How many records?</h2>
            <p className="hint">Maximum allowed: {maxRecords.toLocaleString()}</p>
            <input
              type="number"
              min={1}
              max={maxRecords}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
            />
            <div className="actions">
              <button
                className="primary"
                disabled={!count || count < 1 || count > maxRecords}
                onClick={() => go(1)}
              >
                Next
              </button>
            </div>
          </section>
        )}

        {step === 1 && (
          <section>
            <h2>Choose a data source</h2>
            <div className="choice-grid">
              <button
                className={`choice ${source === "erp" ? "selected" : ""}`}
                onClick={() => setSource("erp")}
              >
                <strong>Standard ERP</strong>
                <span>SAP / Oracle table (schema inferred via OpenAI)</span>
              </button>
              <button
                className={`choice ${source === "custom" ? "selected" : ""}`}
                onClick={() => setSource("custom")}
              >
                <strong>Custom Dataset</strong>
                <span>Upload a file or define fields in a form</span>
              </button>
            </div>

            {source === "erp" && (
              <div className="subpanel">
                <label>
                  ERP
                  <select
                    value={erpId}
                    onChange={(e) => {
                      setErpId(e.target.value);
                      setTable("");
                    }}
                  >
                    <option value="">Select ERP…</option>
                    {erps.map((e) => (
                      <option key={e.erp_id} value={e.erp_id}>
                        {e.erp_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Table
                  <select
                    value={table}
                    onChange={(e) => setTable(e.target.value)}
                    disabled={!erpId}
                  >
                    <option value="">Select table…</option>
                    {erps
                      .find((e) => e.erp_id === erpId)
                      ?.tables.map((t) => (
                        <option key={t.table} value={t.table}>
                          {t.table} — {t.description}
                        </option>
                      ))}
                  </select>
                </label>
                <div className="actions">
                  <button className="ghost" onClick={() => go(0)}>
                    Back
                  </button>
                  <button
                    className="primary"
                    disabled={!erpId || !table || busy}
                    onClick={fetchErpSchema}
                  >
                    {busy ? "Inferring…" : "Get schema"}
                  </button>
                </div>
              </div>
            )}

            {source === "custom" && (
              <div className="subpanel">
                <label>
                  Number of fields
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={fieldCount}
                    onChange={(e) => setFieldCount(Number(e.target.value))}
                  />
                </label>
                <div className="choice-grid">
                  <button
                    className={`choice ${customMethod === "upload" ? "selected" : ""}`}
                    onClick={() => setCustomMethod("upload")}
                  >
                    <strong>Upload Excel/CSV</strong>
                    <span>Four columns: field_name, key, data_type, length</span>
                  </button>
                  <button
                    className={`choice ${customMethod === "form" ? "selected" : ""}`}
                    onClick={() => setCustomMethod("form")}
                  >
                    <strong>Fill a form</strong>
                    <span>Enter each field manually</span>
                  </button>
                </div>

                {customMethod === "upload" && (
                  <div className="upload">
                    <p className="hint">
                      Need the format?{" "}
                      <a href={templateUrl("xlsx")}>Download Excel template</a>{" "}
                      or <a href={templateUrl("csv")}>CSV template</a>.
                    </p>
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={(e) =>
                        e.target.files?.[0] && handleUpload(e.target.files[0])
                      }
                    />
                  </div>
                )}

                {customMethod === "form" && (
                  <CustomForm
                    fieldCount={fieldCount}
                    dataTypes={dataTypes}
                    onSubmit={handleFormSubmit}
                  />
                )}

                <div className="actions">
                  <button className="ghost" onClick={() => go(0)}>
                    Back
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

        {step === 2 && schema && (
          <section>
            <h2>Review schema</h2>
            {schema.table && (
              <p className="hint">
                {schema.source.toUpperCase()} · {schema.table}
              </p>
            )}
            <SchemaTable schema={schema} />
            <div className="actions">
              <button className="ghost" onClick={() => go(1)}>
                Back
              </button>
              <button className="primary" disabled={busy} onClick={runPreview}>
                {busy ? "Generating…" : "Generate 10-row preview"}
              </button>
            </div>
          </section>
        )}

        {step === 3 && preview && (
          <section>
            <h2>Preview (first 10 rows)</h2>
            <p className="hint">
              Does this look right? Approve to generate all {count.toLocaleString()}{" "}
              records.
            </p>
            <PreviewTable headers={preview.headers} rows={preview.rows} />
            <div className="actions">
              <button className="ghost" onClick={() => go(2)}>
                Adjust schema
              </button>
              <button className="primary" onClick={() => go(4)}>
                Looks good — continue
              </button>
            </div>
          </section>
        )}

        {step === 4 && (
          <section>
            <h2>Generate & export</h2>
            <p className="hint">
              {count.toLocaleString()} records · {schema?.fields.length} fields
            </p>
            <label>
              Export format
              <select
                value={exportFmt}
                onChange={(e) => setExportFmt(e.target.value)}
              >
                {exportFormats.map((f) => (
                  <option key={f} value={f}>
                    {f.toUpperCase()}
                  </option>
                ))}
              </select>
            </label>
            <div className="actions">
              <button className="ghost" onClick={() => go(3)}>
                Back
              </button>
              <button className="primary" disabled={busy} onClick={runGenerate}>
                {busy ? "Generating…" : `Generate & download ${exportFmt.toUpperCase()}`}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
