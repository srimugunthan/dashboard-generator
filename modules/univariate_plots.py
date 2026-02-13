"""Generate univariate distribution plots for numerical and categorical columns."""

from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from modules.chart_helpers import PlotResult, configure_plot_style
from modules.constants import MAX_CATEGORICAL_BARS, MAX_UNIVARIATE_PLOTS
from modules.schema_detector import SchemaInfo

logger = logging.getLogger(__name__)

# Default slot split: up to 5 numerical, 4 categorical.
_DEFAULT_NUM_SLOTS = 5
_DEFAULT_CAT_SLOTS = 4


def generate_univariate_plots(
    df: pd.DataFrame,
    schema_info: SchemaInfo,
) -> list[PlotResult]:
    """Create histogram and bar-chart plots for the most interesting columns.

    Numerical columns are ranked by variance (descending) and categorical
    columns by unique-value count (descending).  The total number of plots
    is capped at ``MAX_UNIVARIATE_PLOTS`` (9), split as up to 5 numerical
    and 4 categorical.  If one type has fewer columns than its slot
    allocation, the surplus slots are given to the other type.

    Args:
        df: The loaded DataFrame.
        schema_info: Detected schema information.

    Returns:
        A list of PlotResult objects (one per generated plot).
    """
    configure_plot_style()

    num_cols = _select_numerical_columns(df, schema_info)
    cat_cols = _select_categorical_columns(df, schema_info)

    # Determine slot allocation ----------------------------------------
    num_slots, cat_slots = _allocate_slots(
        len(num_cols), len(cat_cols)
    )

    selected_num = num_cols[:num_slots]
    selected_cat = cat_cols[:cat_slots]

    plots: list[PlotResult] = []

    for col in selected_num:
        result = _create_histogram(df, col)
        if result is not None:
            plots.append(result)

    for col in selected_cat:
        result = _create_bar_chart(df, col)
        if result is not None:
            plots.append(result)

    return plots


# -- private helpers -----------------------------------------------------


def _allocate_slots(
    n_num: int,
    n_cat: int,
) -> tuple[int, int]:
    """Divide the total plot budget between numerical and categorical.

    Args:
        n_num: Number of available numerical columns.
        n_cat: Number of available categorical columns.

    Returns:
        A tuple of (numerical_slots, categorical_slots).
    """
    num_slots = min(n_num, _DEFAULT_NUM_SLOTS)
    cat_slots = min(n_cat, _DEFAULT_CAT_SLOTS)

    # If one type under-uses its slots, donate the remainder.
    num_surplus = _DEFAULT_NUM_SLOTS - num_slots
    cat_surplus = _DEFAULT_CAT_SLOTS - cat_slots

    num_slots = min(n_num, num_slots + cat_surplus)
    cat_slots = min(n_cat, cat_slots + num_surplus)

    # Final cap to never exceed the global maximum.
    total = num_slots + cat_slots
    if total > MAX_UNIVARIATE_PLOTS:
        # Scale down proportionally (shouldn't happen with 5+4=9).
        cat_slots = MAX_UNIVARIATE_PLOTS - num_slots

    return num_slots, cat_slots


def _select_numerical_columns(
    df: pd.DataFrame,
    schema_info: SchemaInfo,
) -> list[str]:
    """Rank numerical columns by variance (descending).

    Args:
        df: The loaded DataFrame.
        schema_info: Detected schema information.

    Returns:
        Column names sorted by descending variance.
    """
    variances: list[tuple[str, float]] = []
    for col in schema_info.numerical_cols:
        try:
            var = df[col].var()
            if pd.notna(var):
                variances.append((col, float(var)))
        except TypeError:
            logger.debug("Skipping column %s: variance not computable", col)

    variances.sort(key=lambda x: x[1], reverse=True)
    return [col for col, _ in variances]


def _select_categorical_columns(
    df: pd.DataFrame,
    schema_info: SchemaInfo,
) -> list[str]:
    """Rank categorical columns by unique-value count (descending).

    Args:
        df: The loaded DataFrame.
        schema_info: Detected schema information.

    Returns:
        Column names sorted by descending unique count.
    """
    unique_counts: list[tuple[str, int]] = []
    for col in schema_info.categorical_cols:
        n_unique = int(df[col].nunique())
        unique_counts.append((col, n_unique))

    unique_counts.sort(key=lambda x: x[1], reverse=True)
    return [col for col, _ in unique_counts]


def _create_histogram(
    df: pd.DataFrame,
    col: str,
) -> PlotResult | None:
    """Create a histogram with KDE overlay for a numerical column.

    Args:
        df: The loaded DataFrame.
        col: The column name to plot.

    Returns:
        A PlotResult, or None if the plot could not be created.
    """
    try:
        series = df[col].dropna()
        fig, ax = plt.subplots()
        sns.histplot(data=df, x=col, kde=True, ax=ax)
        ax.set_title(col)
        plt.tight_layout()

        desc = (
            f"Histogram of '{col}'. "
            f"Mean={series.mean():.4g}, "
            f"Median={series.median():.4g}, "
            f"Std={series.std():.4g}, "
            f"Min={series.min():.4g}, "
            f"Max={series.max():.4g}."
        )

        return PlotResult(
            figure=fig,
            title=col,
            plot_type="histogram",
            description_for_ai=desc,
            column_names=[col],
        )
    except Exception:
        logger.exception("Failed to create histogram for column '%s'", col)
        return None


def _create_bar_chart(
    df: pd.DataFrame,
    col: str,
) -> PlotResult | None:
    """Create a horizontal bar chart for a categorical column.

    Values beyond ``MAX_CATEGORICAL_BARS`` are lumped into an
    "Other" category.

    Args:
        df: The loaded DataFrame.
        col: The column name to plot.

    Returns:
        A PlotResult, or None if the plot could not be created.
    """
    try:
        counts = df[col].value_counts()
        n_unique = len(counts)

        if n_unique > MAX_CATEGORICAL_BARS:
            top = counts.iloc[:MAX_CATEGORICAL_BARS]
            other_total = counts.iloc[MAX_CATEGORICAL_BARS:].sum()
            counts = pd.concat(
                [top, pd.Series({"Other": other_total})]
            )

        fig, ax = plt.subplots()
        sns.barplot(
            x=counts.values,
            y=counts.index.astype(str),
            orient="h",
            ax=ax,
        )
        ax.set_title(col)
        ax.set_xlabel("Count")
        plt.tight_layout()

        mode_value = df[col].mode()
        mode_str = str(mode_value.iloc[0]) if len(mode_value) > 0 else "N/A"
        mode_freq = int(counts.iloc[0]) if len(counts) > 0 else 0

        desc = (
            f"Bar chart of '{col}'. "
            f"Unique values={n_unique}, "
            f"Mode='{mode_str}', "
            f"Mode frequency={mode_freq}."
        )

        return PlotResult(
            figure=fig,
            title=col,
            plot_type="bar_chart",
            description_for_ai=desc,
            column_names=[col],
        )
    except Exception:
        logger.exception(
            "Failed to create bar chart for column '%s'", col
        )
        return None
