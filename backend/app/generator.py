"""Synthetic data generation: LLM-first with a realistic Faker fallback.

Values are produced per field according to the ERP-style data type and length.
Key fields receive unique values.

Realism comes from a semantic resolver that inspects each field's *description*
(catalog ``notes``) as well as its name. SAP/Oracle fields use technical names
(LAND1, ORT01, PSTLZ, REGIO, ...), so matching on the human-readable note is
what lets us emit plausible countries, cities, postal codes, regions, etc.
instead of random characters.

When an LLM is configured it is used first for contextual fields; otherwise the
semantic Faker mapping is used so generation always succeeds offline.
"""

import random
from datetime import date, datetime, timedelta

import pandas as pd
from faker import Faker

from . import llm
from .models import ErpType, Field_, Schema

_fake = Faker()

# ISO-3166 alpha-2 country codes (fit SAP LAND1, length 3).
_COUNTRY_CODES = [
    "US", "DE", "GB", "FR", "IT", "ES", "NL", "BE", "CH", "AT",
    "SE", "NO", "DK", "FI", "PL", "CZ", "IE", "PT", "CA", "MX",
    "BR", "AR", "IN", "CN", "JP", "KR", "AU", "NZ", "ZA", "AE",
]

# US state codes (fit SAP REGIO, length 3).
_REGION_CODES = [
    "CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI",
    "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
]

_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "SEK"]
_UNITS = ["EA", "KG", "L", "M", "PC", "BOX", "PAL", "CTN", "M2", "M3"]
_LANGUAGES = ["E", "D", "F", "S", "I", "P", "J"]
_MATERIAL_TYPES = ["FERT", "HALB", "ROH", "HAWA", "DIEN", "VERP"]
_DOC_TYPES = ["OR", "RE", "KA", "KR", "SA", "DR"]


def _semantic_value(field: Field_) -> str | None:
    """Return a realistic value based on the field's note/name, or None.

    Matching is driven primarily by the field *description* (``notes``) so that
    technically-named ERP fields still produce meaningful data.
    """
    name = field.field_name.upper()
    text = f"{field.notes or ''} {field.field_name}".lower()
    length = field.length

    def fit(v: str) -> str:
        return str(v)[:length]

    # --- Order matters: most specific first. ---

    # Fiscal year / year
    if "fiscal year" in text or "year" in text or name == "GJAHR":
        return fit(str(random.randint(2018, 2025)))

    # Postal / ZIP code
    if "postal" in text or "zip" in text or name in ("PSTLZ", "PSTL2"):
        return fit(_fake.postcode())

    # Region / state / province (short codes vs full names)
    if "region" in text or "state" in text or "province" in text or name == "REGIO":
        return fit(random.choice(_REGION_CODES)) if length <= 4 else fit(_fake.state())

    # Country (codes vs full names)
    if "country" in text or name in ("LAND1", "LAND", "ALAND"):
        return fit(random.choice(_COUNTRY_CODES)) if length <= 3 else fit(_fake.country())

    # City
    if "city" in text or name in ("ORT01", "ORT02"):
        return fit(_fake.city())

    # Street / house number / address
    if "street" in text or "house" in text or "address" in text:
        return fit(_fake.street_address())

    # Email
    if "email" in text or "e-mail" in text or "smtp" in text:
        return fit(_fake.email())

    # Telephone / fax / mobile
    if (
        "telephone" in text
        or "phone" in text
        or "fax" in text
        or "mobile" in text
        or name.startswith("TELF")
    ):
        return fit(_fake.numerify("+1-###-###-####"))

    # Currency key
    if "currency" in text or field.data_type == ErpType.CUKY:
        return fit(random.choice(_CURRENCIES))

    # Unit of measure
    if "unit" in text or field.data_type == ErpType.UNIT:
        return fit(random.choice(_UNITS))

    # Language
    if "language" in text or field.data_type == ErpType.LANG:
        return fit(random.choice(_LANGUAGES))

    # Material type / document type (SAP-specific code fields)
    if "material type" in text:
        return fit(random.choice(_MATERIAL_TYPES))
    if "document type" in text or "doc. type" in text or "doc type" in text:
        return fit(random.choice(_DOC_TYPES))

    # Short SAP org-unit / code fields are identifiers, not free text. Emit a
    # compact numeric code rather than a name when the field is short.
    if length <= 6 and (
        "code" in text
        or "key" in text
        or "number" in text
        or "organization" in text
        or "org." in text
        or "channel" in text
        or "division" in text
        or "office" in text
        or "group" in text
    ):
        return fit(_fake.numerify("####"))

    # Company / organization (free-text name) — only when long enough to hold one
    if length >= 10 and (
        "company" in text
        or "vendor name" in text
        or "supplier name" in text
        or "organization" in text
    ):
        return fit(_fake.company())

    # Created/changed by (user id) — before generic "name"
    if "created by" in text or "changed by" in text or "user" in text:
        return fit(_fake.user_name().upper())

    # Person / customer / vendor name (generic "name")
    if "name" in text:
        return fit(_fake.name())

    # Description / text
    if "description" in text or "text" in text:
        return fit(_fake.catch_phrase())

    # Plant / storage location / warehouse — short numeric codes
    if "plant" in text or "storage location" in text or "warehouse" in text:
        return fit(_fake.numerify("####"))

    return None


def _is_semantic(field: Field_) -> bool:
    """Whether the field has a meaningful semantic mapping."""
    return _semantic_value(field) is not None


def _faker_semantic(field: Field_) -> str:
    """Always-succeeds semantic value (used for fallback and padding)."""
    v = _semantic_value(field)
    return v if v is not None else _gen_scalar(field, 0)


def _gen_scalar(field: Field_, seq: int) -> str:
    """Generate a single value for a non-semantic field by data type."""
    dt = field.data_type
    length = field.length

    if dt == ErpType.CHAR:
        # Mixed letters+digits reads more like a real code than pure letters.
        pattern = "?" * min(length, 4) + "#" * max(length - 4, 0)
        return _fake.bothify(pattern).upper()[:length]
    if dt == ErpType.NUMC:
        return "".join(random.choices("0123456789", k=length))
    if dt == ErpType.INT:
        hi = min(10 ** min(length, 9) - 1, 2_000_000_000)
        return str(random.randint(0, hi))
    if dt in (ErpType.DEC, ErpType.CURR, ErpType.QUAN):
        whole = random.randint(0, 10 ** min(max(length - 3, 1), 7) - 1)
        return f"{whole}.{random.randint(0, 99):02d}"
    if dt == ErpType.DATS:
        start = date(2015, 1, 1)
        d = start + timedelta(days=random.randint(0, 4000))
        return d.strftime("%Y%m%d")
    if dt == ErpType.TIMS:
        t = datetime(2000, 1, 1) + timedelta(seconds=random.randint(0, 86399))
        return t.strftime("%H%M%S")
    if dt == ErpType.LANG:
        return random.choice(_LANGUAGES)
    if dt == ErpType.CUKY:
        return random.choice(_CURRENCIES)
    if dt == ErpType.UNIT:
        return random.choice(_UNITS)
    return _fake.lexify("?" * min(length, 10))[:length]


def _gen_value(field: Field_, seq: int) -> str:
    """Single value: semantic mapping first, then type-based scalar."""
    sem = _semantic_value(field)
    return sem if sem is not None else _gen_scalar(field, seq)


def _unique_value(field: Field_, seq: int, used: set[str]) -> str:
    """Produce a value guaranteed unique within ``used`` for key fields."""
    for _ in range(50):
        candidate = _gen_value(field, seq)
        if candidate not in used:
            used.add(candidate)
            return candidate
    # Fallback: deterministic suffix to guarantee uniqueness.
    candidate = f"{seq}"[: field.length].rjust(min(field.length, 6), "0")
    used.add(candidate)
    return candidate


def _generate_column(field: Field_, count: int) -> list[str]:
    # Contextual fields: try the LLM first, then fall back to semantic Faker.
    if _is_semantic(field) and not field.key:
        if llm.llm_available():
            try:
                values = llm.generate_values(field, count)
                if len(values) >= count:
                    return values[:count]
                # Pad any shortfall with the semantic Faker mapping.
                values += [_faker_semantic(field) for _ in range(count - len(values))]
                return values
            except Exception:  # noqa: BLE001 - fall back gracefully
                pass
        return [_faker_semantic(field) for _ in range(count)]

    if field.key:
        used: set[str] = set()
        return [_unique_value(field, i, used) for i in range(count)]

    return [_gen_value(field, i) for i in range(count)]


def generate_dataframe(schema: Schema, count: int) -> pd.DataFrame:
    columns = {f.field_name: _generate_column(f, count) for f in schema.fields}
    return pd.DataFrame(columns, columns=[f.field_name for f in schema.fields])


def preview(schema: Schema, rows: int) -> tuple[list[str], list[list[str]]]:
    df = generate_dataframe(schema, rows)
    headers = list(df.columns)
    data = [[str(v) for v in row] for row in df.itertuples(index=False, name=None)]
    return headers, data
