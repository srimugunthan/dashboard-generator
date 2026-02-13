"""Auto-detect column types and merge with user-provided schema."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from modules.constants import MAX_UNIQUE_FOR_CATEGORICAL
from modules.schema_parser import UserSchema


@dataclass
class ColumnMeta:
    """Metadata for a single DataFrame column."""

    name: str
    dtype: str
    semantic_type: str  # "numerical", "categorical", or "datetime"
    description: str = ""
    null_count: int = 0
    pct_missing: float = 0.0
    n_unique: int = 0


@dataclass
class SchemaInfo:
    """Complete schema information for a loaded DataFrame."""

    n_rows: int = 0
    n_cols: int = 0
    numerical_cols: list[str] = field(default_factory=list)
    categorical_cols: list[str] = field(default_factory=list)
    datetime_cols: list[str] = field(default_factory=list)
    columns: list[ColumnMeta] = field(default_factory=list)


def detect_schema(
    df: pd.DataFrame,
    user_schema: UserSchema | None = None,
) -> SchemaInfo:
    """Build a SchemaInfo by merging auto-detection with user overrides.

    Args:
        df: The loaded DataFrame.
        user_schema: Optional user-provided schema (takes priority).

    Returns:
        A fully populated SchemaInfo.
    """
    user_lookup: dict[str, tuple[str, str]] = {}
    if user_schema:
        for col_info in user_schema.columns:
            user_lookup[col_info.name] = (
                col_info.declared_type,
                col_info.description,
            )

    columns_meta: list[ColumnMeta] = []
    numerical_cols: list[str] = []
    categorical_cols: list[str] = []
    datetime_cols: list[str] = []

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        n_total = len(df)
        pct_missing = round(null_count / n_total * 100, 1) if n_total else 0.0
        n_unique = int(df[col].nunique())

        # Determine semantic type
        if col in user_lookup:
            semantic_type, description = user_lookup[col]
        else:
            semantic_type = _auto_detect_type(df[col], n_unique)
            description = ""

        meta = ColumnMeta(
            name=col,
            dtype=str(df[col].dtype),
            semantic_type=semantic_type,
            description=description,
            null_count=null_count,
            pct_missing=pct_missing,
            n_unique=n_unique,
        )
        columns_meta.append(meta)

        if semantic_type == "numerical":
            numerical_cols.append(col)
        elif semantic_type == "datetime":
            datetime_cols.append(col)
        else:
            categorical_cols.append(col)

    return SchemaInfo(
        n_rows=len(df),
        n_cols=len(df.columns),
        numerical_cols=numerical_cols,
        categorical_cols=categorical_cols,
        datetime_cols=datetime_cols,
        columns=columns_meta,
    )


def _auto_detect_type(series: pd.Series, n_unique: int) -> str:
    """Heuristically classify a column as numerical, categorical, or datetime.

    Args:
        series: A single DataFrame column.
        n_unique: Pre-computed unique-value count.

    Returns:
        One of "numerical", "categorical", or "datetime".
    """
    if pd.api.types.is_bool_dtype(series):
        return "categorical"

    if pd.api.types.is_numeric_dtype(series):
        if n_unique > MAX_UNIQUE_FOR_CATEGORICAL:
            return "numerical"
        return "categorical"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Object dtype: try parsing as datetime
    if series.dtype == object:
        try:
            pd.to_datetime(series.dropna().head(50), infer_datetime_format=True)
            return "datetime"
        except (ValueError, TypeError):
            pass

    return "categorical"
