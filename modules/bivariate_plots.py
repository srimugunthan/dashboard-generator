"""Generate bivariate analysis plots (heatmap, scatter, grouped bar)."""

from __future__ import annotations

import logging
from itertools import combinations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from modules.chart_helpers import PlotResult, configure_plot_style
from modules.constants import (
    MAX_BIVARIATE_PLOTS,
    MAX_CATEGORICAL_BARS,
    MIN_CORRELATION_THRESHOLD,
)
from modules.schema_detector import SchemaInfo

logger = logging.getLogger(__name__)


def generate_bivariate_plots(
    df: pd.DataFrame,
    schema_info: SchemaInfo,
) -> list[PlotResult]:
    """Generate bivariate analysis plots capped at MAX_BIVARIATE_PLOTS.

    Produces a correlation heatmap (if >= 2 numerical columns),
    scatter plots for highly correlated numerical pairs, and
    grouped bar charts for categorical-vs-numerical pairs ranked
    by eta-squared.

    Args:
        df: The loaded DataFrame.
        schema_info: Detected schema information.

    Returns:
        A list of PlotResult objects (at most MAX_BIVARIATE_PLOTS).
    """
    configure_plot_style()

    numerical_cols = schema_info.numerical_cols
    categorical_cols = schema_info.categorical_cols

    if len(numerical_cols) == 0:
        return []

    results: list[PlotResult] = []
    remaining = MAX_BIVARIATE_PLOTS

    # --- Correlation heatmap (always first, if >= 2 numerical cols) ---
    corr: pd.DataFrame | None = None
    if len(numerical_cols) >= 2:
        heatmap = _make_correlation_heatmap(df, numerical_cols)
        if heatmap is not None:
            results.append(heatmap)
            remaining -= 1

        corr = df[numerical_cols].corr()

    # --- Determine scatter / grouped-bar slot allocation ---
    max_scatter = min(4, remaining)
    max_bar = min(4, remaining)

    scatter_candidates = _rank_scatter_pairs(corr, numerical_cols)
    bar_candidates = _rank_grouped_bar_pairs(
        df, categorical_cols, numerical_cols
    )

    n_scatter_available = min(len(scatter_candidates), max_scatter)
    n_bar_available = min(len(bar_candidates), max_bar)

    # If one type has fewer than 4 candidates, give remaining
    # slots to the other type (total remaining slots = remaining).
    if n_scatter_available + n_bar_available <= remaining:
        n_scatter = n_scatter_available
        n_bar = n_bar_available
    elif n_scatter_available < max_scatter:
        n_scatter = n_scatter_available
        n_bar = min(n_bar_available, remaining - n_scatter)
    elif n_bar_available < max_bar:
        n_bar = n_bar_available
        n_scatter = min(n_scatter_available, remaining - n_bar)
    else:
        n_scatter = min(n_scatter_available, remaining // 2)
        n_bar = min(n_bar_available, remaining - n_scatter)

    # --- Scatter plots ---
    for col1, col2, r_val in scatter_candidates[:n_scatter]:
        try:
            plot = _make_scatter_plot(df, col1, col2, r_val)
            results.append(plot)
        except Exception:
            logger.exception(
                "Failed to create scatter plot for %s vs %s",
                col1,
                col2,
            )

    # --- Grouped bar charts ---
    for cat_col, num_col, eta_sq in bar_candidates[:n_bar]:
        try:
            plot = _make_grouped_bar(df, cat_col, num_col, eta_sq)
            results.append(plot)
        except Exception:
            logger.exception(
                "Failed to create grouped bar for %s vs %s",
                cat_col,
                num_col,
            )

    return results


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _make_correlation_heatmap(
    df: pd.DataFrame,
    numerical_cols: list[str],
) -> PlotResult | None:
    """Create a correlation heatmap for numerical columns.

    Args:
        df: The loaded DataFrame.
        numerical_cols: List of numerical column names.

    Returns:
        A PlotResult containing the heatmap, or None on failure.
    """
    try:
        corr = df[numerical_cols].corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        annot = len(numerical_cols) <= 15
        sns.heatmap(
            corr,
            annot=annot,
            cmap="RdBu_r",
            center=0,
            fmt=".2f",
            ax=ax,
        )
        ax.set_title("Correlation Heatmap")
        plt.tight_layout()

        desc = _top_correlated_pairs_description(corr)

        return PlotResult(
            figure=fig,
            title="Correlation Heatmap",
            plot_type="heatmap",
            description_for_ai=desc,
            column_names=list(numerical_cols),
        )
    except Exception:
        logger.exception("Failed to create correlation heatmap")
        return None


def _top_correlated_pairs_description(
    corr: pd.DataFrame,
    top_n: int = 3,
) -> str:
    """Build a description string with the top correlated pairs.

    Args:
        corr: Correlation matrix DataFrame.
        top_n: Number of top pairs to include.

    Returns:
        Human-readable string listing the top correlated pairs.
    """
    pairs: list[tuple[str, str, float]] = []
    cols = corr.columns.tolist()
    for i, j in combinations(range(len(cols)), 2):
        r_val = corr.iloc[i, j]
        if not np.isnan(r_val):
            pairs.append((cols[i], cols[j], r_val))

    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    top_pairs = pairs[:top_n]

    if not top_pairs:
        return "No significant correlations found."

    lines = ["Top correlated pairs:"]
    for c1, c2, r_val in top_pairs:
        lines.append(f"  {c1} & {c2}: r = {r_val:.2f}")
    return "\n".join(lines)


def _rank_scatter_pairs(
    corr: pd.DataFrame | None,
    numerical_cols: list[str],
) -> list[tuple[str, str, float]]:
    """Rank numerical column pairs by absolute correlation.

    Only pairs with |r| >= MIN_CORRELATION_THRESHOLD are included.

    Args:
        corr: Correlation matrix, or None if fewer than 2
            numerical columns.
        numerical_cols: List of numerical column names.

    Returns:
        Sorted list of (col1, col2, r) tuples, descending by |r|.
    """
    if corr is None or len(numerical_cols) < 2:
        return []

    pairs: list[tuple[str, str, float]] = []
    cols = corr.columns.tolist()
    for i, j in combinations(range(len(cols)), 2):
        r_val = corr.iloc[i, j]
        if not np.isnan(r_val) and abs(r_val) >= MIN_CORRELATION_THRESHOLD:
            pairs.append((cols[i], cols[j], r_val))

    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    return pairs


def _rank_grouped_bar_pairs(
    df: pd.DataFrame,
    categorical_cols: list[str],
    numerical_cols: list[str],
) -> list[tuple[str, str, float]]:
    """Rank (categorical, numerical) pairs by eta-squared.

    Args:
        df: The loaded DataFrame.
        categorical_cols: List of categorical column names.
        numerical_cols: List of numerical column names.

    Returns:
        Sorted list of (cat_col, num_col, eta_squared) tuples,
        descending by eta-squared.
    """
    if not categorical_cols or not numerical_cols:
        return []

    pairs: list[tuple[str, str, float]] = []
    for cat_col in categorical_cols:
        for num_col in numerical_cols:
            eta_sq = _compute_eta_squared(df, cat_col, num_col)
            if eta_sq is not None:
                pairs.append((cat_col, num_col, eta_sq))

    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs


def _compute_eta_squared(
    df: pd.DataFrame,
    cat_col: str,
    num_col: str,
) -> float | None:
    """Compute eta-squared for a categorical-numerical pair.

    Eta-squared = SS_between / SS_total, measuring the proportion
    of variance in the numerical column explained by group
    membership in the categorical column.

    Args:
        df: The loaded DataFrame.
        cat_col: Name of the categorical column.
        num_col: Name of the numerical column.

    Returns:
        Eta-squared value, or None if computation fails.
    """
    try:
        subset = df[[cat_col, num_col]].dropna()
        if subset.empty:
            return None

        groups = [
            group[num_col].values
            for _, group in subset.groupby(cat_col)
        ]
        # Need at least 2 groups with data
        groups = [g for g in groups if len(g) > 0]
        if len(groups) < 2:
            return None

        grand_mean = subset[num_col].mean()
        ss_total = float(np.sum((subset[num_col] - grand_mean) ** 2))
        if ss_total == 0:
            return 0.0

        ss_between = sum(
            len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups
        )
        return float(ss_between / ss_total)
    except Exception:
        logger.exception(
            "Failed to compute eta-squared for %s vs %s",
            cat_col,
            num_col,
        )
        return None


def _make_scatter_plot(
    df: pd.DataFrame,
    col1: str,
    col2: str,
    r_val: float,
) -> PlotResult:
    """Create a scatter plot for two numerical columns.

    Args:
        df: The loaded DataFrame.
        col1: Name of the x-axis column.
        col2: Name of the y-axis column.
        r_val: Pre-computed Pearson correlation coefficient.

    Returns:
        A PlotResult containing the scatter plot.
    """
    fig, ax = plt.subplots()
    sns.scatterplot(data=df, x=col1, y=col2, alpha=0.6, ax=ax)
    ax.set_title(f"{col1} vs {col2}")
    plt.tight_layout()

    desc = (
        f"Scatter plot of {col1} vs {col2}. "
        f"Pearson correlation r = {r_val:.2f}."
    )

    return PlotResult(
        figure=fig,
        title=f"{col1} vs {col2}",
        plot_type="scatter",
        description_for_ai=desc,
        column_names=[col1, col2],
    )


def _make_grouped_bar(
    df: pd.DataFrame,
    cat_col: str,
    num_col: str,
    eta_sq: float,
) -> PlotResult:
    """Create a horizontal grouped bar chart.

    Shows the mean of a numerical column grouped by the top
    categories (limited to MAX_CATEGORICAL_BARS).

    Args:
        df: The loaded DataFrame.
        cat_col: Name of the categorical column.
        num_col: Name of the numerical column.
        eta_sq: Pre-computed eta-squared value.

    Returns:
        A PlotResult containing the grouped bar chart.
    """
    means = (
        df.groupby(cat_col)[num_col]
        .mean()
        .dropna()
        .sort_values(ascending=False)
        .head(MAX_CATEGORICAL_BARS)
    )

    fig, ax = plt.subplots()
    means.sort_values(ascending=True).plot.barh(ax=ax)
    ax.set_title(f"{cat_col} vs {num_col}")
    ax.set_xlabel(num_col)
    ax.set_ylabel(cat_col)
    plt.tight_layout()

    top_cats = means.index.tolist()[:5]
    top_cats_str = ", ".join(str(c) for c in top_cats)
    desc = (
        f"Grouped bar chart of mean {num_col} by {cat_col}. "
        f"Eta-squared = {eta_sq:.3f}. "
        f"Top categories: {top_cats_str}."
    )

    return PlotResult(
        figure=fig,
        title=f"{cat_col} vs {num_col}",
        plot_type="grouped_bar",
        description_for_ai=desc,
        column_names=[cat_col, num_col],
    )
