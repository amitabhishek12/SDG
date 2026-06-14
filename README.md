# Synthetic Data Generator

A web application that generates synthetic datasets from either a standard ERP
table (SAP / Oracle) or a custom schema. Preview a 10-row sample, approve it,
then generate any number of records and export to CSV, Excel, PDF, or Parquet.

It works fully offline: ERP schemas are served from a built-in catalog of
common SAP and Oracle tables. OpenAI schema inference is an optional fallback
for tables not in the catalog.

## Architecture

- **Backend** — FastAPI (`backend/`). Schema modelling, an offline ERP catalog
  (`erp_catalog.py`) with fuzzy table search, optional OpenAI schema inference,
  Faker-based data generation, and export serializers.
- **Frontend** — React + Vite (`frontend/`). A landing page introduces the
  product, then a step-based flow handles record count → source → schema →
  preview → export. Proxies `/api` to the backend in dev.

## How it works

1. From the landing page, click **Get started**.
2. Enter the number of records to generate (capped, default 100,000).
3. Choose a source:
   - **Standard ERP**: pick SAP/Oracle, then search for a table by name. An
     exact match resolves directly; otherwise the five closest tables are
     suggested. You can also browse the full catalog. Once a table is chosen,
     pick exactly the fields you need (key fields are preselected). Tables not
     in the catalog can be inferred via OpenAI when a key is configured.
   - **Custom Dataset**: declare the number of fields, then either upload an
     Excel/CSV with four columns (`field_name`, `key`, `data_type`, `length`)
     or fill in a form. A template is downloadable.
4. Review the resolved schema.
5. Generate a 10-row preview and confirm it looks right.
6. Generate the full dataset and download it as CSV, Excel, PDF, or Parquet.

## Configuration

Set in `backend/.env` (see `backend/.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | _unset_ | Optional. Enables ERP schema inference for tables not in the catalog, plus contextual data fallback. When unset, the catalog and Faker generation still work fully offline. |
| `OPENAI_BASE_URL` | _unset_ | Optional. Override the OpenAI endpoint (e.g. an OpenRouter-compatible base URL). |
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
