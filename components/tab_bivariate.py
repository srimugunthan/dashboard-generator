"""Tab 4 — Bivariate Analysis rendering logic."""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from modules.chart_helpers import PlotResult, save_plot


def _show_commentary(
    title: str,
    commentary: dict[str, str] | None,
) -> None:
    """Display AI commentary or a fallback caption.

    Args:
        title: The chart title used as a lookup key.
        commentary: Dict mapping chart titles to commentary
            strings, or None if commentary is unavailable.
    """
    if commentary and title in commentary:
        st.info(f"**AI Commentary:** {commentary[title]}")
    else:
        st.caption(
            "Provide an API key to enable AI commentary."
        )


def render(
    plots: list[PlotResult],
    commentary: dict[str, str] | None = None,
) -> None:
    """Render the Bivariate Analysis tab.

    Displays pre-generated bivariate plots. A heatmap (if
    present as the first plot) is rendered full-width, followed
    by remaining plots in a 3-column grid.

    Args:
        plots: Pre-generated PlotResult objects to display.
        commentary: Dict mapping chart titles to AI commentary
            strings. Defaults to None.
    """
    if not plots:
        st.info("Not enough columns for bivariate analysis.")
        return

    start_idx = 0

    # Render heatmap full-width if it is the first plot
    if plots[0].plot_type == "heatmap":
        heatmap = plots[0]
        st.pyplot(heatmap.figure)
        _show_commentary(heatmap.title, commentary)
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
                _show_commentary(
                    plot_result.title, commentary,
                )
                save_plot(plot_result, "bivariate")
                plt.close(plot_result.figure)
