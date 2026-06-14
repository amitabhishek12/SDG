# Synthetic Data Generator — Specification

## Problem Statement

Teams need realistic synthetic datasets that mirror real ERP table structures
(SAP, Oracle) or arbitrary custom schemas, without exposing production data. The
product is a web application that lets a user define a schema — either by picking
an ERP table or by supplying a custom field list — preview a sample, confirm it
meets expectations, then generate any requested number of records and export them
in multiple formats.

## Goals

- Let a user specify how many records to generate.
- Support two schema sources: a standard ERP table, or a custom dataset.
- For ERP, infer table metadata (fields, keys, data type, length) via an LLM.
- For custom, accept the schema via Excel/CSV upload or an in-app form.
- Always show a 10-row preview and require user consent before full generation.
- Export generated data as Excel, CSV, PDF, or Parquet.
- Run as a self-contained web application.

## Non-Goals

- No user authentication or persistence (stateless, single-session).
- No direct live connection to real SAP/Oracle systems.
- No editing/versioning of previously generated datasets.

## Technology Decisions

| Concern | Decision |
|---|---|
| Frontend | React (SPA) |
| Backend | Python FastAPI |
| ERP schema metadata | LLM-generated (OpenAI API) |
| Synthetic data engine | Faker (primary) + LLM fallback for contextual fields |
| LLM provider | OpenAI via `OPENAI_API_KEY` env var |
| Prebuilt ERPs | SAP + Oracle, a few sample tables each |
| Field data types | ERP-style types (CHAR, NUMC, DEC, DATS, etc.) mapped internally |
| Upload validation | Strict 4-column schema + downloadable template |
| Record cap | Configurable cap (default 100,000) |
| Auth / storage | None — stateless |

## User Flow

1. **Record count** — User enters the desired number of records.
2. **Source selection** — User chooses an ERP (SAP / Oracle) or "Custom Dataset".
3. **ERP path**
   - User selects an ERP and a table.
   - Backend asks the LLM for the table's schema: field name, key flag,
     ERP data type, length, and any other relevant attributes.
   - The resolved schema is displayed for review.
4. **Custom path**
   - User is asked for the number of fields.
   - User chooses one of two input methods:
     - **Upload**: Excel/CSV with exactly four columns —
       `field_name`, `key`, `data_type`, `length`. A template is downloadable.
     - **Form**: an in-app form to enter each field's name, data type, length,
       and key flag.
5. **Preview** — Backend generates the **first 10 rows** with headers and shows
   them to the user.
6. **Consent** — User confirms the preview is correct.
   - If not satisfied, user returns to edit the schema/inputs and re-previews.
7. **Full generation** — On approval, backend generates all requested records
   (subject to the configured cap).
8. **Export** — User downloads the dataset as Excel, CSV, PDF, or Parquet.

## Functional Requirements

### Schema definition
- **FR-1**: Accept a numeric record count; validate it is a positive integer
  within the configured cap.
- **FR-2**: Present ERP options (SAP, Oracle) and a list of sample tables per ERP.
- **FR-3**: For a selected ERP + table, call the LLM to produce a schema of
  fields with: `field_name`, `key` (bool), `data_type` (ERP-style), `length`,
  and optional notes. Return a normalized schema object.
- **FR-4**: Offer "Custom Dataset" when no ERP/table is chosen.
- **FR-5**: For custom, prompt for the number of fields.
- **FR-6**: Support Excel/CSV upload with strict columns
  (`field_name`, `key`, `data_type`, `length`); reject files that do not match
  the template and report which columns are wrong/missing.
- **FR-7**: Provide a downloadable upload template (Excel and CSV).
- **FR-8**: Support a form-based schema entry as an alternative to upload, sized
  to the declared number of fields.

### Data generation
- **FR-9**: Map ERP-style data types (e.g. CHAR, NUMC, DEC, DATS, TIMS, INT,
  CURR) to internal generator types.
- **FR-10**: Generate values with Faker according to type and length
  constraints; truncate/pad to declared length where applicable.
- **FR-11**: For fields Faker cannot meaningfully populate (contextual/semantic),
  fall back to the LLM to produce realistic values.
- **FR-12**: Honor `key` fields by generating unique values for them.
- **FR-13**: Generate exactly 10 preview rows on request.
- **FR-14**: On consent, generate the full record count (≤ configured cap).

### Export
- **FR-15**: Export the generated dataset as `.xlsx`, `.csv`, `.pdf`, and
  `.parquet`, with headers.
- **FR-16**: Streamed/downloadable response with appropriate content types and
  filenames.

### Web application
- **FR-17**: React SPA served alongside / calling the FastAPI backend.
- **FR-18**: Stateless — schema and generated data held only for the active
  session/request; no login.
- **FR-19**: Surface clear validation and error messages (bad upload, LLM
  failure, count over cap).

## Non-Functional Requirements

- **NFR-1**: Record cap and OpenAI settings configurable via environment.
- **NFR-2**: Missing/invalid `OPENAI_API_KEY` degrades gracefully — ERP schema
  inference and LLM fallback are disabled with a clear message; Faker-based
  custom generation still works.
- **NFR-3**: Preview generation responds quickly (10 rows) independent of the
  full requested count.
- **NFR-4**: `.gitignore` excludes Python and Node artifacts, env files, and
  generated output.

## Acceptance Criteria

- [ ] User can enter a record count and is blocked if it exceeds the cap.
- [ ] Selecting SAP/Oracle + a sample table returns an LLM-inferred schema with
      field name, key, data type, and length.
- [ ] Choosing Custom prompts for field count and offers upload or form input.
- [ ] Upload rejects files not matching the strict 4-column template and a
      template file is downloadable.
- [ ] Form input produces a valid schema for the declared number of fields.
- [ ] A 10-row preview with headers is shown before any full generation.
- [ ] No full dataset is generated until the user approves the preview.
- [ ] On approval, the exact requested number of records is generated.
- [ ] Key fields contain unique values.
- [ ] Dataset can be downloaded as Excel, CSV, PDF, and Parquet.
- [ ] App runs as a web page (React frontend + FastAPI backend).
- [ ] App works without auth and stores nothing between sessions.

## Implementation Approach

1. **Scaffold repo**: `backend/` (FastAPI) and `frontend/` (React), root
   `.gitignore`, READMEs, and Ona automations/devcontainer wiring.
2. **Backend core models**: schema/field models, ERP-type → internal-type
   mapping, config (record cap, OpenAI settings).
3. **ERP metadata service**: sample ERP/table catalog (SAP + Oracle) and an
   LLM client that returns a normalized schema for a selected table; graceful
   degradation without a key.
4. **Custom schema intake**: endpoints for upload (strict 4-column parsing +
   validation), template download, and form-submitted schemas.
5. **Data generation engine**: Faker-based generator honoring types, lengths,
   and key uniqueness, with LLM fallback for contextual fields; `generate(n)`
   and `preview()` (10 rows).
6. **Export service**: serializers for xlsx, csv, pdf, parquet with download
   endpoints.
7. **API layer**: REST endpoints tying together count → source → schema →
   preview → consent → full generation → export.
8. **Frontend**: step-based UI (record count → source → schema input → preview
   → consent → export) calling the backend; template download and export
   buttons.
9. **Validation & errors**: surface count cap, upload, and LLM errors clearly.
10. **Run & verify**: launch via preview server, walk both ERP and custom paths
    end to end, confirm all four export formats.
