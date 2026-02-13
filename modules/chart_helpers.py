"""Shared matplotlib/seaborn styling and PlotResult dataclass."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

from modules.constants import OUTPUT_DIR, PLOT_SAVE_DPI

# Use non-interactive backend so figures don't pop up outside Streamlit
matplotlib.use("Agg")


@dataclass
class PlotResult:
    """Container for a generated matplotlib figure and its metadata."""

    figure: plt.Figure
    title: str
    plot_type: str  # e.g. "histogram", "bar_chart", "scatter", "heatmap"
    description_for_ai: str = ""
    column_names: list[str] = field(default_factory=list)
    saved_path: str | None = None


def configure_plot_style() -> None:
    """Apply a consistent seaborn/matplotlib style for all plots."""
    plt.style.use("seaborn-v0_8-whitegrid")
    sns.set_palette("Set2")
    plt.rcParams["figure.dpi"] = 100
    plt.rcParams["savefig.dpi"] = PLOT_SAVE_DPI
    plt.rcParams["figure.figsize"] = (6, 4)


def save_plot(plot_result: PlotResult, subfolder: str) -> str:
    """Save a PlotResult's figure to disk as PNG.

    Args:
        plot_result: The plot to save.
        subfolder: Subdirectory under OUTPUT_DIR (e.g. "univariate").

    Returns:
        The absolute path to the saved PNG file.
    """
    dir_path = os.path.join(OUTPUT_DIR, subfolder)
    os.makedirs(dir_path, exist_ok=True)

    sanitized = re.sub(r"[^a-z0-9]+", "_", plot_result.title.lower()).strip("_")
    filename = f"{sanitized}.png"
    filepath = os.path.join(dir_path, filename)

    plot_result.figure.savefig(filepath, dpi=PLOT_SAVE_DPI, bbox_inches="tight")
    plot_result.saved_path = filepath
    return filepath
