"""Compute summary statistics for numerical and categorical columns."""

from __future__ import annotations

import pandas as pd


def compute_numerical_stats(
    df: pd.DataFrame,
    numerical_cols: list[str],
) -> pd.DataFrame:
    """Compute descriptive statistics for numerical columns.

    For each column the following statistics are calculated:
    mean, median, standard deviation, min, max, 25th percentile,
    75th percentile, and skewness.  All values are rounded to two
    decimal places.

    Args:
        df: The source DataFrame.
        numerical_cols: List of numerical column names to analyse.

    Returns:
        A DataFrame indexed by column name with one row per column
        and statistic names as column headers.
    """
    records: list[dict[str, float]] = []
    for col in numerical_cols:
        series = df[col].dropna()
        records.append(
            {
                "Mean": round(series.mean(), 2),
                "Median": round(series.median(), 2),
                "Std": round(series.std(), 2),
                "Min": round(series.min(), 2),
                "Max": round(series.max(), 2),
                "25%": round(series.quantile(0.25), 2),
                "75%": round(series.quantile(0.75), 2),
                "Skewness": round(series.skew(), 2),
            }
        )

    return pd.DataFrame(records, index=numerical_cols)


def compute_categorical_stats(
    df: pd.DataFrame,
    categorical_cols: list[str],
) -> pd.DataFrame:
    """Compute descriptive statistics for categorical columns.

    For each column the following are calculated: unique value count,
    mode (most frequent value), mode frequency, and a comma-separated
    string of the top 5 most common values.

    Args:
        df: The source DataFrame.
        categorical_cols: List of categorical column names to
            analyse.

    Returns:
        A DataFrame indexed by column name with one row per column
        and statistic names as column headers.
    """
    records: list[dict[str, str | int]] = []
    for col in categorical_cols:
        series = df[col].dropna()
        value_counts = series.value_counts()
        n_unique = series.nunique()

        if len(value_counts) > 0:
            mode_value = value_counts.index[0]
            mode_freq = int(value_counts.iloc[0])
        else:
            mode_value = "N/A"
            mode_freq = 0

        top_5 = ", ".join(str(v) for v in value_counts.head(5).index)

        records.append(
            {
                "Unique": n_unique,
                "Mode": mode_value,
                "Mode Freq": mode_freq,
                "Top 5": top_5,
            }
        )

    return pd.DataFrame(records, index=categorical_cols)
