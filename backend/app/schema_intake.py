"""Custom schema intake: strict 4-column upload parsing and template export."""

import io

import pandas as pd

from .models import ErpType, Field_, Schema

REQUIRED_COLUMNS = ["field_name", "key", "data_type", "length"]


class UploadValidationError(ValueError):
    """Raised when an uploaded schema file does not match the template."""


def _normalize_columns(cols: list[str]) -> list[str]:
    return [str(c).strip().lower().replace(" ", "_") for c in cols]


def _coerce_key(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"x", "true", "yes", "y", "1", "key"}


def parse_upload(content: bytes, filename: str) -> Schema:
    """Parse an uploaded Excel/CSV file into a Schema.

    Enforces the strict four-column template; raises UploadValidationError
    listing missing/unexpected columns when the file does not match.
    """
    buf = io.BytesIO(content)
    name = filename.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(buf)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(buf)
        else:
            raise UploadValidationError(
                "Unsupported file type. Upload a .csv or .xlsx file."
            )
    except UploadValidationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise UploadValidationError(f"Could not read file: {exc}") from exc

    df.columns = _normalize_columns(list(df.columns))

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"missing columns: {', '.join(missing)}")
        if extra:
            parts.append(f"unexpected columns: {', '.join(extra)}")
        raise UploadValidationError(
            "File does not match the template (" + "; ".join(parts) + "). "
            f"Expected exactly: {', '.join(REQUIRED_COLUMNS)}."
        )

    fields: list[Field_] = []
    for idx, row in df.iterrows():
        raw_type = str(row["data_type"]).strip().upper()
        try:
            dt = ErpType(raw_type)
        except ValueError as exc:
            valid = ", ".join(t.value for t in ErpType)
            raise UploadValidationError(
                f"Row {idx + 2}: invalid data_type '{raw_type}'. "
                f"Allowed: {valid}."
            ) from exc
        try:
            length = int(row["length"])
        except (ValueError, TypeError) as exc:
            raise UploadValidationError(
                f"Row {idx + 2}: length must be an integer."
            ) from exc
        fields.append(
            Field_(
                field_name=str(row["field_name"]).strip(),
                key=_coerce_key(row["key"]),
                data_type=dt,
                length=length,
            )
        )

    if not fields:
        raise UploadValidationError("File contains no data rows.")

    return Schema(source="custom", fields=fields)


def template_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"field_name": "MATERIAL_ID", "key": "X", "data_type": "CHAR", "length": 18},
            {"field_name": "DESCRIPTION", "key": "", "data_type": "CHAR", "length": 40},
            {"field_name": "QUANTITY", "key": "", "data_type": "QUAN", "length": 13},
            {"field_name": "CREATED_ON", "key": "", "data_type": "DATS", "length": 8},
        ],
        columns=REQUIRED_COLUMNS,
    )


def template_csv() -> bytes:
    return template_dataframe().to_csv(index=False).encode("utf-8")


def template_xlsx() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        template_dataframe().to_excel(writer, index=False, sheet_name="schema")
    return buf.getvalue()
