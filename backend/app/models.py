"""Pydantic models shared across the API."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ErpType(str, Enum):
    """ERP-style data types exposed to the user."""

    CHAR = "CHAR"  # alphanumeric, fixed length
    NUMC = "NUMC"  # numeric text (digits only, fixed length)
    DEC = "DEC"  # decimal / fixed-point number
    CURR = "CURR"  # currency amount
    QUAN = "QUAN"  # quantity
    INT = "INT"  # integer
    DATS = "DATS"  # date (YYYYMMDD)
    TIMS = "TIMS"  # time (HHMMSS)
    LANG = "LANG"  # language key
    CUKY = "CUKY"  # currency key (e.g. USD)
    UNIT = "UNIT"  # unit of measure


class Field_(BaseModel):
    """A single field in a dataset schema."""

    field_name: str = Field(..., min_length=1)
    key: bool = False
    data_type: ErpType
    length: int = Field(default=10, ge=1, le=4000)
    notes: str | None = None

    @field_validator("field_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class Schema(BaseModel):
    """A complete dataset schema."""

    source: str = "custom"  # "custom" or an ERP id (e.g. "sap")
    table: str | None = None
    fields: list[Field_]

    @field_validator("fields")
    @classmethod
    def non_empty(cls, v: list[Field_]) -> list[Field_]:
        if not v:
            raise ValueError("schema must contain at least one field")
        return v


class ErpTableInfo(BaseModel):
    erp_id: str
    erp_name: str
    table: str
    description: str


class ErpInfo(BaseModel):
    erp_id: str
    erp_name: str
    tables: list[ErpTableInfo]


class PreviewRequest(BaseModel):
    schema_: Schema = Field(..., alias="schema")

    model_config = {"populate_by_name": True}


class GenerateRequest(BaseModel):
    schema_: Schema = Field(..., alias="schema")
    count: int = Field(..., ge=1)
    fmt: str = Field(default="csv")

    model_config = {"populate_by_name": True}


class PreviewResponse(BaseModel):
    headers: list[str]
    rows: list[list[str]]
