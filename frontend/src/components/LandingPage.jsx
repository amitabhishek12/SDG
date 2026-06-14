const FEATURES = [
  {
    title: "ERP-aware schemas",
    body: "Pick a standard SAP or Oracle table and start from its real fields, keys, data types, and lengths — no manual setup.",
  },
  {
    title: "Search any table",
    body: "Type a table name; get an exact match or the five closest suggestions from the built-in catalog.",
  },
  {
    title: "Custom datasets",
    body: "No ERP? Upload a four-column Excel/CSV or define fields in a form, then generate against your own schema.",
  },
  {
    title: "Pick your fields",
    body: "Choose exactly the fields you need from a table — keys are preselected so output stays consistent.",
  },
  {
    title: "Preview before you commit",
    body: "Review the first 10 rows with headers and confirm the data looks right before generating the full set.",
  },
  {
    title: "Export anywhere",
    body: "Download as CSV, Excel, PDF, or Parquet — ready for testing, demos, training, or analytics.",
  },
];

export default function LandingPage({ onStart, llmEnabled }) {
  return (
    <div className="landing">
      <header className="landing-hero">
        <div className="hero-inner">
          <span className="badge">Synthetic Data Generator</span>
          <h1>
            Generate realistic test data from <span>ERP tables</span> or your
            own schema.
          </h1>
          <p className="lead">
            Create production-like datasets in seconds — without touching real
            data. Start from a standard SAP/Oracle table or define a custom
            schema, preview a sample, then export thousands of records in the
            format you need.
          </p>
          <div className="hero-actions">
            <button className="primary lg" onClick={onStart}>
              Get started
            </button>
            <span className="hero-note">
              {llmEnabled
                ? "Catalog + AI schema inference enabled"
                : "Works fully offline · no data leaves your machine"}
            </span>
          </div>
        </div>
      </header>

      <section className="features">
        <h2 className="features-title">What you can do</h2>
        <div className="feature-grid">
          {FEATURES.map((f) => (
            <div className="feature-card" key={f.title}>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="cta">
        <div className="cta-inner">
          <h2>Ready to create your dataset?</h2>
          <p>Define a schema, preview it, and export — in a few clicks.</p>
          <button className="primary lg" onClick={onStart}>
            Create synthetic data
          </button>
        </div>
      </section>

      <footer className="landing-footer">
        Synthetic Data Generator · FastAPI + React
      </footer>
    </div>
  );
}
