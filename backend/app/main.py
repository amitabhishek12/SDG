"""FastAPI application: synthetic data generator API."""

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from . import erp_catalog, exporter, generator, llm, schema_intake
from .config import get_settings
from .models import (
    ErpType,
    GenerateRequest,
    PreviewRequest,
    PreviewResponse,
    Schema,
    TableSchemaResponse,
    TableSearchResponse,
)

app = FastAPI(title="Synthetic Data Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "llm_enabled": settings.llm_enabled,
        "max_records": settings.max_records,
        "preview_rows": settings.preview_rows,
    }


@app.get("/api/config")
def config() -> dict:
    settings = get_settings()
    return {
        "max_records": settings.max_records,
        "preview_rows": settings.preview_rows,
        "llm_enabled": settings.llm_enabled,
        "data_types": [t.value for t in ErpType],
        "export_formats": ["csv", "xlsx", "pdf", "parquet"],
    }


@app.get("/api/erps")
def list_erps() -> dict:
    return {"erps": [e.model_dump() for e in erp_catalog.list_erps()]}


@app.get("/api/erp-tables/search", response_model=TableSearchResponse)
def search_tables(erp_id: str, q: str) -> TableSearchResponse:
    """Resolve a free-text table name against the offline catalog.

    Returns an exact match, up to 5 close suggestions, or a not-found status.
    When the catalog has no match but the LLM is available, the table can still
    be resolved via /api/erp-schema (status "none" with source "llm").
    """
    if erp_catalog.erp_name(erp_id) is None:
        raise HTTPException(status_code=404, detail="Unknown ERP")

    result = erp_catalog.search_tables(erp_id, q)
    # If nothing matched but the LLM is available, signal that the exact query
    # can still be attempted via the schema endpoint.
    if result["status"] == "none" and llm.llm_available():
        return TableSearchResponse(status="none", matches=[], source="llm")
    return TableSearchResponse(**result, source="catalog")


@app.get("/api/erp-schema", response_model=TableSchemaResponse)
def erp_schema(erp_id: str, table: str) -> TableSchemaResponse:
    """Return a table's full field list.

    LLM inference is attempted first when a key is configured. If the LLM is
    unavailable or fails, fall back to the offline catalog. (With the LLM
    disabled the catalog is always used, so the app works fully offline.)
    """
    name = erp_catalog.erp_name(erp_id)
    if name is None:
        raise HTTPException(status_code=404, detail="Unknown ERP")

    catalog_fields = erp_catalog.get_catalog_fields(erp_id, table)
    catalog_desc = erp_catalog.get_table_description(erp_id, table)

    # Primary: LLM inference (when configured).
    if llm.llm_available():
        try:
            schema = llm.infer_erp_schema(
                erp_id, name, table, catalog_desc or table
            )
            return TableSchemaResponse(
                erp_id=erp_id,
                table=table.upper(),
                description=catalog_desc,
                source="llm",
                fields=schema.fields,
            )
        except Exception:  # noqa: BLE001 - fall back to the catalog below
            pass

    # Fallback: offline catalog.
    if catalog_fields is not None:
        return TableSchemaResponse(
            erp_id=erp_id,
            table=table.upper(),
            description=catalog_desc,
            source="catalog",
            fields=catalog_fields,
        )

    raise HTTPException(
        status_code=404,
        detail=(
            f"Table '{table}' is not in the catalog. Configure an "
            "OPENAI_API_KEY to infer schemas for arbitrary tables, or "
            "pick a catalogued table."
        ),
    )


@app.post("/api/upload-schema")
async def upload_schema(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    try:
        schema = schema_intake.parse_upload(content, file.filename or "upload")
    except schema_intake.UploadValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"schema": schema.model_dump()}


@app.get("/api/template")
def template(fmt: str = "xlsx") -> Response:
    if fmt == "csv":
        data = schema_intake.template_csv()
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=schema_template.csv"},
        )
    if fmt == "xlsx":
        data = schema_intake.template_xlsx()
        return Response(
            content=data,
            media_type=exporter.media_type("xlsx"),
            headers={
                "Content-Disposition": "attachment; filename=schema_template.xlsx"
            },
        )
    raise HTTPException(status_code=400, detail="fmt must be csv or xlsx")


@app.post("/api/preview", response_model=PreviewResponse)
def preview(req: PreviewRequest) -> PreviewResponse:
    settings = get_settings()
    headers, rows = generator.preview(req.schema_, settings.preview_rows)
    return PreviewResponse(headers=headers, rows=rows)


@app.post("/api/generate")
def generate(req: GenerateRequest) -> Response:
    settings = get_settings()
    if req.count > settings.max_records:
        raise HTTPException(
            status_code=400,
            detail=f"count exceeds the configured cap of {settings.max_records}",
        )
    if not exporter.supported(req.fmt):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {req.fmt}")

    df = generator.generate_dataframe(req.schema_, req.count)
    data = exporter.to_bytes(df, req.fmt)
    filename = f"synthetic_data.{req.fmt}"
    return Response(
        content=data,
        media_type=exporter.media_type(req.fmt),
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
