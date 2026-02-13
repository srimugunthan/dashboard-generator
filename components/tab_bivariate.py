"""Tab 4 — Bivariate Analysis rendering logic."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from modules.bivariate_plots import generate_bivariate_plots
from modules.chart_helpers import save_plot
from modules.schema_detector import SchemaInfo


def render(df: pd.DataFrame, schema_info: SchemaInfo) -> None:
    """Render the Bivariate Analysis tab.

    Generates bivariate plots (correlation heatmap, scatter plots,
    and grouped bar charts) and displays them in the Streamlit UI.

    Args:
        df: The loaded DataFrame.
        schema_info: Detected schema information.
    """
    plots = generate_bivariate_plots(df, schema_info)

    if not plots:
        st.info("Not enough columns for bivariate analysis.")
        return

    start_idx = 0

    # Render heatmap full-width if it is the first plot
    if plots[0].plot_type == "heatmap":
        heatmap = plots[0]
        st.pyplot(heatmap.figure)
        st.caption("AI commentary will appear here.")
        save_plot(heatmap, "bivariate")
        plt.close(heatmap.figure)
        start_idx = 1

    # Render remaining plots in a 3-column grid
    remaining_plots = plots[start_idx:]
    for row_start in range(0, len(remaining_plots), 3):
        row_plots = remaining_plots[row_start : row_start + 3]
        cols = st.columns(3)
        for col_idx, plot_result in enumerate(row_plots):
            with cols[col_idx]:
                st.pyplot(plot_result.figure)
                st.caption("AI commentary will appear here.")
                save_plot(plot_result, "bivariate")
                plt.close(plot_result.figure)
