"""Synthetic data generation: Faker-driven with an OpenAI fallback.

Values are produced per field according to the ERP-style data type and length.
Key fields receive unique values. Fields whose name suggests semantic content
(name, email, address, ...) are routed to the LLM when it is available, falling
back to Faker otherwise so generation always succeeds offline.
"""

import random
from datetime import date, datetime, timedelta

import pandas as pd
from faker import Faker

from . import llm
from .models import ErpType, Field_, Schema

_fake = Faker()

# Field-name keywords that benefit from contextual (LLM) generation.
_SEMANTIC_KEYWORDS = (
    "name",
    "email",
    "address",
    "city",
    "country",
    "phone",
    "company",
    "description",
    "street",
)


def _is_semantic(field: Field_) -> bool:
    lname = field.field_name.lower()
    return any(k in lname for k in _SEMANTIC_KEYWORDS)


def _faker_semantic(field: Field_) -> str:
    lname = field.field_name.lower()
    if "email" in lname:
        v = _fake.email()
    elif "company" in lname or "org" in lname:
        v = _fake.company()
    elif "city" in lname:
        v = _fake.city()
    elif "country" in lname:
        v = _fake.country()
    elif "phone" in lname:
        v = _fake.phone_number()
    elif "address" in lname or "street" in lname:
        v = _fake.street_address()
    elif "description" in lname:
        v = _fake.sentence()
    elif "name" in lname:
        v = _fake.name()
    else:
        v = _fake.word()
    return str(v)[: field.length]


def _gen_scalar(field: Field_, seq: int) -> str:
    """Generate a single value for a non-semantic field."""
    dt = field.data_type
    length = field.length

    if dt == ErpType.CHAR:
        return _fake.lexify("?" * min(length, 12)).upper()[:length]
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
        return random.choice(["E", "D", "F", "S", "I"])
    if dt == ErpType.CUKY:
        return random.choice(["USD", "EUR", "GBP", "JPY", "CHF"])
    if dt == ErpType.UNIT:
        return random.choice(["EA", "KG", "L", "M", "PC"])
    return _fake.lexify("?" * min(length, 10))[:length]


def _unique_value(field: Field_, seq: int, used: set[str]) -> str:
    """Produce a value guaranteed unique within ``used`` for key fields."""
    for _ in range(50):
        candidate = _gen_scalar(field, seq)
        if candidate not in used:
            used.add(candidate)
            return candidate
    # Fallback: deterministic suffix to guarantee uniqueness.
    candidate = f"{seq}"[: field.length].rjust(min(field.length, 6), "0")
    used.add(candidate)
    return candidate


def _generate_column(field: Field_, count: int) -> list[str]:
    # Semantic fields: try the LLM, then fall back to Faker.
    if _is_semantic(field) and not field.key:
        if llm.llm_available():
            try:
                values = llm.generate_values(field, count)
                if len(values) >= count:
                    return values[:count]
                # Pad shortfall with Faker.
                values += [_faker_semantic(field) for _ in range(count - len(values))]
                return values
            except Exception:  # noqa: BLE001 - fall back gracefully
                pass
        return [_faker_semantic(field) for _ in range(count)]

    if field.key:
        used: set[str] = set()
        return [_unique_value(field, i, used) for i in range(count)]

    return [_gen_scalar(field, i) for i in range(count)]


def generate_dataframe(schema: Schema, count: int) -> pd.DataFrame:
    columns = {f.field_name: _generate_column(f, count) for f in schema.fields}
    return pd.DataFrame(columns, columns=[f.field_name for f in schema.fields])


def preview(schema: Schema, rows: int) -> tuple[list[str], list[list[str]]]:
    df = generate_dataframe(schema, rows)
    headers = list(df.columns)
    data = [[str(v) for v in row] for row in df.itertuples(index=False, name=None)]
    return headers, data
