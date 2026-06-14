# Synthetic Data Generator

A web application that generates synthetic datasets from either a standard ERP
table (SAP / Oracle) or a custom schema. Preview a 10-row sample, approve it,
then generate any number of records and export to CSV, Excel, PDF, or Parquet.

## Architecture

- **Backend** — FastAPI (`backend/`). Schema modelling, ERP catalog, OpenAI
  schema inference, Faker-based data generation with an LLM fallback, and export
  serializers.
- **Frontend** — React + Vite (`frontend/`). Step-based UI: record count →
  source → schema → preview → export. Proxies `/api` to the backend in dev.

## How it works

1. Enter the number of records to generate (capped, default 100,000).
2. Choose a source:
   - **Standard ERP**: pick SAP/Oracle and a table; the schema (fields, keys,
     data type, length) is inferred via OpenAI.
   - **Custom Dataset**: declare the number of fields, then either upload an
     Excel/CSV with four columns (`field_name`, `key`, `data_type`, `length`)
     or fill in a form. A template is downloadable.
3. Review the resolved schema.
4. Generate a 10-row preview and confirm it looks right.
5. Generate the full dataset and download it as CSV, Excel, PDF, or Parquet.

## Configuration

Set in `backend/.env` (see `backend/.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | _unset_ | Enables ERP schema inference and contextual data fallback. When unset, custom datasets still work via Faker. |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model id |
| `MAX_RECORDS` | `100000` | Upper limit per generation |
| `PREVIEW_ROWS` | `10` | Rows shown in the preview |

## Running locally

Backend:

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Note: the backend environment in this workspace uses Python 3.14.5, so the
dependency pins in `backend/requirements.txt` are set to versions that install
cleanly on that interpreter. If you create a new environment, use Python 3.14+
or reuse the existing `backend/.venv` to avoid package build errors on Windows.

Frontend (in another terminal):

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api` to `http://localhost:8000`.

## Data types

ERP-style types are supported and mapped internally for generation:
`CHAR`, `NUMC`, `DEC`, `CURR`, `QUAN`, `INT`, `DATS`, `TIMS`, `LANG`, `CUKY`,
`UNIT`.
