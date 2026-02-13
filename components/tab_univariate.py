"""Tab 3 — Univariate Analysis rendering logic."""

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
    """Render the Univariate Analysis tab.

    Displays pre-generated univariate plots in a 3-column grid
    with AI commentary below each chart.

    Args:
        plots: Pre-generated PlotResult objects to display.
        commentary: Dict mapping chart titles to AI commentary
            strings. Defaults to None.
    """
    if not plots:
        st.info("No columns available for univariate analysis.")
        return

    for row_start in range(0, len(plots), 3):
        row_plots = plots[row_start : row_start + 3]
        row_cols = st.columns(3)
        for col_idx, plot_result in enumerate(row_plots):
            with row_cols[col_idx]:
                st.pyplot(plot_result.figure)
                _show_commentary(
                    plot_result.title, commentary,
                )
                save_plot(plot_result, "univariate")
                plt.close(plot_result.figure)
