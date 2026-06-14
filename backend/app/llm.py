"""OpenAI client for schema inference and contextual data fallback.

All functions degrade gracefully when no API key is configured: callers should
check ``llm_available()`` or handle ``LLMUnavailable``.
"""

import json
import re

from .config import get_settings
from .models import ErpType, Field_, Schema


class LLMUnavailable(RuntimeError):
    """Raised when an LLM operation is requested but no key is configured."""


def llm_available() -> bool:
    return get_settings().llm_enabled


def _client():
    settings = get_settings()
    if not settings.llm_enabled:
        raise LLMUnavailable("OPENAI_API_KEY is not configured")
    # Imported lazily so the app runs without the SDK installed in dev.
    from openai import OpenAI

    # base_url is passed only when set, so the same client works against
    # OpenAI (default) or an OpenAI-compatible provider like OpenRouter.
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )


def _complete(prompt: str, max_tokens: int) -> str:
    client = _client()
    settings = get_settings()
    resp = client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or ""


def _extract_json(text: str) -> str:
    """Pull the first JSON object/array out of a model response."""
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    start = min(
        (i for i in (text.find("{"), text.find("[")) if i != -1),
        default=-1,
    )
    if start != -1:
        return text[start:].strip()
    return text.strip()


def infer_erp_schema(erp_id: str, erp_name: str, table: str, description: str) -> Schema:
    """Ask the model for the schema of a standard ERP table."""
    valid_types = ", ".join(t.value for t in ErpType)
    prompt = (
        f"You are an expert in {erp_name} ERP data structures. "
        f"Provide the schema of the standard table '{table}' "
        f"({description}). Return ONLY a JSON array of up to 15 of the most "
        "important fields. Each element must be an object with keys: "
        "field_name (string), key (boolean, true for primary-key fields), "
        f"data_type (one of: {valid_types}), length (integer), "
        "notes (short string, optional). "
        "Map native types to the closest of the allowed data_type values."
    )

    raw = _complete(prompt, max_tokens=2000)
    data = json.loads(_extract_json(raw))

    fields: list[Field_] = []
    for item in data:
        try:
            dt = ErpType(str(item.get("data_type", "CHAR")).upper())
        except ValueError:
            dt = ErpType.CHAR
        fields.append(
            Field_(
                field_name=item["field_name"],
                key=bool(item.get("key", False)),
                data_type=dt,
                length=int(item.get("length", 10)),
                notes=item.get("notes"),
            )
        )

    return Schema(source=erp_id, table=table, fields=fields)


def generate_values(field: Field_, count: int) -> list[str]:
    """Use the model to produce realistic values for a contextual field."""
    prompt = (
        f"Generate {count} realistic, distinct sample values for a database "
        f"field named '{field.field_name}' "
        f"(type {field.data_type.value}, max length {field.length}). "
        f"{('Context: ' + field.notes) if field.notes else ''} "
        "Return ONLY a JSON array of strings, no commentary."
    )
    raw = _complete(prompt, max_tokens=4000)
    values = json.loads(_extract_json(raw))
    return [str(v)[: field.length] for v in values][:count]
