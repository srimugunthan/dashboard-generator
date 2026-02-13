"""CSV loading, validation, and sampling utilities."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from modules.constants import MAX_COLUMNS, MAX_ROWS_DEFAULT, RANDOM_SEED


@st.cache_data(show_spinner="Loading CSV...")
def load_csv(
    file_bytes: bytes,
    file_name: str,
    max_rows: int = MAX_ROWS_DEFAULT,
) -> tuple[pd.DataFrame, list[str]]:
    """Load and validate a CSV file, returning (DataFrame, warnings).

    Args:
        file_bytes: Raw bytes of the uploaded file.
        file_name: Original filename (used in messages only).
        max_rows: Maximum rows to keep; excess rows are sampled.

    Returns:
        A tuple of (validated DataFrame, list of warning strings).

    Raises:
        ValueError: If the CSV is empty or unreadable.
    """
    warnings: list[str] = []
    buf = BytesIO(file_bytes)

    # Encoding fallback: utf-8 → latin-1
    try:
        df = pd.read_csv(buf, encoding="utf-8")
    except UnicodeDecodeError:
        buf.seek(0)
        df = pd.read_csv(buf, encoding="latin-1")
        warnings.append("File was read with latin-1 encoding (utf-8 failed).")

    if df.empty or df.shape[0] == 0:
        raise ValueError("The uploaded CSV is empty.")

    # Drop columns that are 100 % null
    all_null_cols = [c for c in df.columns if df[c].isna().all()]
    if all_null_cols:
        df = df.drop(columns=all_null_cols)
        warnings.append(
            f"Dropped {len(all_null_cols)} all-null column(s): "
            f"{', '.join(all_null_cols)}"
        )

    # Cap columns
    if df.shape[1] > MAX_COLUMNS:
        df = df.iloc[:, :MAX_COLUMNS]
        warnings.append(
            f"Dataset has more than {MAX_COLUMNS} columns; "
            f"only the first {MAX_COLUMNS} are kept."
        )

    # Sample if too many rows
    if df.shape[0] > max_rows:
        df = df.sample(n=max_rows, random_state=RANDOM_SEED)
        warnings.append(
            f"Dataset sampled to {max_rows:,} rows "
            f"(original: {df.shape[0]:,})."
        )

    return df, warnings
