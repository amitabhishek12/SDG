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


@app.get("/api/erp-schema")
def erp_schema(erp_id: str, table: str) -> dict:
    description = erp_catalog.get_table_description(erp_id, table)
    name = erp_catalog.erp_name(erp_id)
    if description is None or name is None:
        raise HTTPException(status_code=404, detail="Unknown ERP or table")
    if not llm.llm_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "ERP schema inference requires an OPENAI_API_KEY. "
                "Use Custom Dataset instead, or configure the key."
            ),
        )
    try:
        schema = llm.infer_erp_schema(erp_id, name, table, description)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"Schema inference failed: {exc}"
        ) from exc
    return {"schema": schema.model_dump()}


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
