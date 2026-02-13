"""Parse user-provided schema text into structured column metadata via OpenAI."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from difflib import get_close_matches

from openai import OpenAI

from modules.constants import OPENAI_MODEL

logger = logging.getLogger(__name__)

PARSE_SYSTEM_PROMPT = (
    "You are a data-schema parser. The user will provide a free-form "
    "description of a CSV dataset's columns. Return ONLY valid JSON with "
    "this exact structure:\n"
    '{"columns": [\n'
    '  {"name": "<column_name>", '
    '"type": "numerical|categorical|datetime", '
    '"description": "<short description>"}\n'
    "]}\n"
    "Rules:\n"
    "- Use the column names exactly as they appear in the user text.\n"
    "- type must be one of: numerical, categorical, datetime.\n"
    "- If the type is ambiguous, make your best guess.\n"
    "- Return an empty columns list if you cannot parse anything."
)


@dataclass
class UserColumnInfo:
    """Metadata for a single column as declared by the user."""

    name: str
    declared_type: str  # "numerical", "categorical", or "datetime"
    description: str = ""


@dataclass
class UserSchema:
    """Structured representation of user-provided schema text."""

    columns: list[UserColumnInfo] = field(default_factory=list)


def parse_schema_text(
    schema_text: str,
    csv_columns: list[str],
    api_key: str,
) -> UserSchema:
    """Parse free-form schema text into a structured UserSchema.

    Uses OpenAI to interpret the text, then fuzzy-matches column names
    against the actual CSV columns.

    Args:
        schema_text: Raw text describing columns (from st.text_area).
        csv_columns: Actual column names from the uploaded CSV.
        api_key: OpenAI API key.

    Returns:
        A UserSchema with matched column info.
    """
    if not schema_text or not schema_text.strip():
        return UserSchema()

    try:
        raw = _call_openai(schema_text, api_key)
        return _build_user_schema(raw, csv_columns)
    except Exception:
        logger.exception("Failed to parse schema text via OpenAI")
        return UserSchema()


def _call_openai(schema_text: str, api_key: str) -> dict:
    """Send schema text to OpenAI and return parsed JSON dict."""
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PARSE_SYSTEM_PROMPT},
            {"role": "user", "content": schema_text},
        ],
        temperature=0.0,
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def _build_user_schema(
    raw: dict,
    csv_columns: list[str],
) -> UserSchema:
    """Validate and fuzzy-match parsed column names to real CSV columns."""
    columns_raw = raw.get("columns", [])
    if not isinstance(columns_raw, list):
        return UserSchema()

    lower_csv = [c.lower() for c in csv_columns]
    matched: list[UserColumnInfo] = []

    for entry in columns_raw:
        name = str(entry.get("name", "")).strip()
        col_type = str(entry.get("type", "categorical")).strip().lower()
        desc = str(entry.get("description", "")).strip()

        if col_type not in {"numerical", "categorical", "datetime"}:
            col_type = "categorical"

        # Exact match first
        if name in csv_columns:
            matched.append(UserColumnInfo(name, col_type, desc))
            continue

        # Case-insensitive match
        lower_name = name.lower()
        if lower_name in lower_csv:
            real_name = csv_columns[lower_csv.index(lower_name)]
            matched.append(UserColumnInfo(real_name, col_type, desc))
            continue

        # Fuzzy match (cutoff 0.6)
        close = get_close_matches(lower_name, lower_csv, n=1, cutoff=0.6)
        if close:
            real_name = csv_columns[lower_csv.index(close[0])]
            matched.append(UserColumnInfo(real_name, col_type, desc))
        else:
            logger.warning("Schema column '%s' not found in CSV", name)

    return UserSchema(columns=matched)
