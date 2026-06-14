"""Serialize a generated DataFrame to csv, xlsx, parquet, or pdf."""

import io

import pandas as pd

_MEDIA_TYPES = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "parquet": "application/octet-stream",
    "pdf": "application/pdf",
}


def media_type(fmt: str) -> str:
    return _MEDIA_TYPES.get(fmt, "application/octet-stream")


def supported(fmt: str) -> bool:
    return fmt in _MEDIA_TYPES


def to_bytes(df: pd.DataFrame, fmt: str) -> bytes:
    if fmt == "csv":
        return df.to_csv(index=False).encode("utf-8")
    if fmt == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="data")
        return buf.getvalue()
    if fmt == "parquet":
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        return buf.getvalue()
    if fmt == "pdf":
        return _to_pdf(df)
    raise ValueError(f"Unsupported format: {fmt}")


def _to_pdf(df: pd.DataFrame) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))

    # PDF is a human-readable preview; cap rows to keep the file usable.
    max_rows = 1000
    shown = df.head(max_rows)
    data = [list(shown.columns)] + shown.astype(str).values.tolist()

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ]
        )
    )
    doc.build([table])
    return buf.getvalue()
