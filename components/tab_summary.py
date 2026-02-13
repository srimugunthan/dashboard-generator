"""Tab 2 — Summary Statistics rendering logic."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.schema_detector import SchemaInfo
from modules.summary_stats import (
    compute_categorical_stats,
    compute_numerical_stats,
)


def render(df: pd.DataFrame, schema_info: SchemaInfo) -> None:
    """Render the Summary Statistics tab.

    Displays computed descriptive statistics for both numerical and
    categorical columns detected in the uploaded dataset.

    Args:
        df: The loaded DataFrame.
        schema_info: Detected schema information.
    """
    # --- Numerical columns ---
    st.subheader("Numerical Columns")
    if schema_info.numerical_cols:
        num_stats = compute_numerical_stats(
            df, schema_info.numerical_cols
        )
        st.dataframe(
            num_stats,
            use_container_width=True,
            hide_index=False,
        )
    else:
        st.info("No numerical columns found.")

    # --- Categorical columns ---
    st.subheader("Categorical Columns")
    if schema_info.categorical_cols:
        cat_stats = compute_categorical_stats(
            df, schema_info.categorical_cols
        )
        st.dataframe(
            cat_stats,
            use_container_width=True,
            hide_index=False,
        )
    else:
        st.info("No categorical columns found.")
