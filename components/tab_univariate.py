"""Tab 3 — Univariate Analysis rendering logic."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from modules.chart_helpers import save_plot
from modules.schema_detector import SchemaInfo
from modules.univariate_plots import generate_univariate_plots


def render(df: pd.DataFrame, schema_info: SchemaInfo) -> None:
    """Render the Univariate Analysis tab with histograms and bar charts.

    Generates up to 9 univariate plots (numerical histograms and
    categorical bar charts) and displays them in a 3-column grid.
    Each plot is also saved to disk under the ``univariate`` subfolder.

    Args:
        df: The loaded DataFrame.
        schema_info: Detected schema information.
    """
    plots = generate_univariate_plots(df, schema_info)

    if not plots:
        st.info("No columns available for univariate analysis.")
        return

    for row_start in range(0, len(plots), 3):
        row_plots = plots[row_start : row_start + 3]
        row_cols = st.columns(3)
        for col_idx, plot_result in enumerate(row_plots):
            with row_cols[col_idx]:
                st.pyplot(plot_result.figure)
                st.caption("AI commentary will appear here.")
                save_plot(plot_result, "univariate")
                plt.close(plot_result.figure)
