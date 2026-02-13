"""Generate AI-driven analytical questions and insight plots."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from openai import OpenAI

from modules.chart_helpers import PlotResult, configure_plot_style
from modules.constants import MAX_CATEGORICAL_BARS, OPENAI_MODEL
from modules.schema_detector import SchemaInfo

logger = logging.getLogger(__name__)

_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "insightful_questions.txt"
)

_COMMENTARY_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "chart_commentary.txt"
)


def _load_prompt_template() -> str:
    """Read the insightful-questions system prompt from disk.

    Returns:
        The raw prompt template string.

    Raises:
        FileNotFoundError: If the prompt file is missing.
    """
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_user_message(
    schema_info: SchemaInfo,
    df: pd.DataFrame,
) -> str:
    """Build the user message containing schema and sample data.

    Args:
        schema_info: Detected schema metadata.
        df: The uploaded DataFrame.

    Returns:
        A formatted string for the OpenAI user message.
    """
    parts: list[str] = []

    # Column schema summary
    parts.append("## Column Schema")
    for col_meta in schema_info.columns:
        line = (
            f"- {col_meta.name} | type={col_meta.semantic_type} "
            f"| dtype={col_meta.dtype} "
            f"| null%={col_meta.pct_missing} "
            f"| unique={col_meta.n_unique}"
        )
        if col_meta.description:
            line += f" | desc={col_meta.description}"
        parts.append(line)

    # Numerical column statistics
    num_cols = schema_info.numerical_cols
    if num_cols:
        parts.append("\n## Numerical Column Stats")
        for col in num_cols:
            if col in df.columns:
                series = df[col].dropna()
                if len(series) > 0:
                    parts.append(
                        f"- {col}: mean={series.mean():.4g}, "
                        f"std={series.std():.4g}, "
                        f"min={series.min():.4g}, "
                        f"max={series.max():.4g}"
                    )

    # 5-row sample
    parts.append("\n## Sample Data (first 5 rows)")
    parts.append(df.head(5).to_csv(index=False))

    return "\n".join(parts)


def generate_questions(
    schema_info: SchemaInfo,
    df: pd.DataFrame,
    api_key: str,
) -> list[dict]:
    """Generate insightful analytical questions about the dataset.

    Reads a prompt template, sends schema and sample data to OpenAI,
    and returns validated question dicts.

    Args:
        schema_info: Detected schema metadata.
        df: The uploaded DataFrame.
        api_key: OpenAI API key.

    Returns:
        A list of question dicts, each containing: question,
        chart_type, x_column, y_column, group_column.
    """
    system_prompt = _load_prompt_template()
    user_message = _build_user_message(schema_info, df)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
    )

    content = response.choices[0].message.content or "{}"
    raw = json.loads(content)
    questions_raw = raw.get("questions", [])

    if not isinstance(questions_raw, list):
        logger.warning("OpenAI returned non-list questions: %s", type(questions_raw))
        return []

    valid_columns = set(df.columns)
    valid_questions: list[dict] = []

    for q in questions_raw:
        if not isinstance(q, dict):
            continue

        x_col = q.get("x_column")
        y_col = q.get("y_column")
        group_col = q.get("group_column")

        # Validate x_column exists
        if x_col and x_col not in valid_columns:
            logger.warning(
                "Skipping question: x_column '%s' not found",
                x_col,
            )
            continue

        # Validate y_column if provided and not null
        if y_col and y_col not in valid_columns:
            logger.warning(
                "Skipping question: y_column '%s' not found",
                y_col,
            )
            continue

        # Validate group_column if provided and not null
        if group_col and group_col not in valid_columns:
            logger.warning(
                "Skipping question: group_column '%s' not found",
                group_col,
            )
            continue

        valid_questions.append(
            {
                "question": str(q.get("question", "")),
                "chart_type": str(q.get("chart_type", "")),
                "x_column": x_col,
                "y_column": y_col,
                "group_column": group_col,
            }
        )

    return valid_questions


def _truncate_title(text: str, max_len: int = 60) -> str:
    """Truncate a title string to a maximum length.

    Args:
        text: The original title text.
        max_len: Maximum number of characters. Defaults to 60.

    Returns:
        The truncated title, with ellipsis if shortened.
    """
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _build_description(
    question: dict,
    df: pd.DataFrame,
) -> str:
    """Build a description string for a PlotResult.

    Args:
        question: The question dict with chart metadata.
        df: The uploaded DataFrame.

    Returns:
        A human-readable description including the question and
        relevant column statistics.
    """
    parts: list[str] = [f"Question: {question['question']}"]

    for key in ("x_column", "y_column"):
        col = question.get(key)
        if col and col in df.columns:
            series = df[col].dropna()
            if pd.api.types.is_numeric_dtype(series):
                parts.append(
                    f"{col}: mean={series.mean():.4g}, "
                    f"std={series.std():.4g}, "
                    f"min={series.min():.4g}, "
                    f"max={series.max():.4g}"
                )
            else:
                parts.append(
                    f"{col}: {series.nunique()} unique values"
                )

    return " | ".join(parts)


def _create_histogram(
    df: pd.DataFrame,
    x_column: str,
) -> plt.Figure:
    """Create a histogram with KDE for a numerical column.

    Args:
        df: The uploaded DataFrame.
        x_column: Column name for the x-axis.

    Returns:
        A matplotlib Figure.
    """
    fig, ax = plt.subplots()
    sns.histplot(data=df, x=x_column, kde=True, ax=ax)
    return fig


def _create_scatter(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
) -> plt.Figure:
    """Create a scatter plot for two numerical columns.

    Args:
        df: The uploaded DataFrame.
        x_column: Column name for the x-axis.
        y_column: Column name for the y-axis.

    Returns:
        A matplotlib Figure.
    """
    fig, ax = plt.subplots()
    sns.scatterplot(
        data=df, x=x_column, y=y_column, alpha=0.6, ax=ax,
    )
    return fig


def _create_bar_chart(
    df: pd.DataFrame,
    x_column: str,
) -> plt.Figure:
    """Create a horizontal bar chart of value counts.

    Args:
        df: The uploaded DataFrame.
        x_column: Column name to count values for.

    Returns:
        A matplotlib Figure.
    """
    counts = (
        df[x_column]
        .value_counts()
        .head(MAX_CATEGORICAL_BARS)
    )
    fig, ax = plt.subplots()
    counts.plot.barh(ax=ax)
    ax.set_xlabel("Count")
    ax.set_ylabel(x_column)
    ax.invert_yaxis()
    return fig


def _create_box_plot(
    df: pd.DataFrame,
    x_column: str,
    y_column: str | None,
) -> plt.Figure:
    """Create a box plot, optionally grouped by a categorical column.

    Args:
        df: The uploaded DataFrame.
        x_column: Categorical grouper or numerical column.
        y_column: Numerical column if grouped; None for single-column.

    Returns:
        A matplotlib Figure.
    """
    fig, ax = plt.subplots()
    if y_column:
        sns.boxplot(data=df, x=x_column, y=y_column, ax=ax)
    else:
        sns.boxplot(data=df, y=x_column, ax=ax)
    return fig


def _create_grouped_bar(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
) -> plt.Figure:
    """Create a horizontal bar of mean y_column grouped by x_column.

    Args:
        df: The uploaded DataFrame.
        x_column: Categorical grouping column.
        y_column: Numerical column to aggregate.

    Returns:
        A matplotlib Figure.
    """
    grouped = (
        df.groupby(x_column)[y_column]
        .mean()
        .sort_values(ascending=True)
        .tail(MAX_CATEGORICAL_BARS)
    )
    fig, ax = plt.subplots()
    grouped.plot.barh(ax=ax)
    ax.set_xlabel(f"Mean {y_column}")
    ax.set_ylabel(x_column)
    return fig


_CHART_CREATORS = {
    "histogram": lambda df, q: _create_histogram(
        df, q["x_column"],
    ),
    "scatter": lambda df, q: _create_scatter(
        df, q["x_column"], q["y_column"],
    ),
    "bar_chart": lambda df, q: _create_bar_chart(
        df, q["x_column"],
    ),
    "box_plot": lambda df, q: _create_box_plot(
        df, q["x_column"], q.get("y_column"),
    ),
    "grouped_bar": lambda df, q: _create_grouped_bar(
        df, q["x_column"], q["y_column"],
    ),
}


def generate_insight_plots(
    df: pd.DataFrame,
    questions: list[dict],
) -> list[PlotResult]:
    """Create matplotlib figures for each AI-generated question.

    Args:
        df: The uploaded DataFrame.
        questions: List of question dicts from generate_questions.

    Returns:
        A list of PlotResult objects, one per successfully plotted
        question.
    """
    configure_plot_style()
    results: list[PlotResult] = []

    for question in questions:
        chart_type = question.get("chart_type", "")
        creator = _CHART_CREATORS.get(chart_type)

        if creator is None:
            logger.warning(
                "Unknown chart_type '%s', skipping", chart_type,
            )
            continue

        try:
            fig = creator(df, question)
            title = _truncate_title(question["question"])
            fig.suptitle(title, fontsize=11, y=1.02)
            fig.tight_layout()

            col_names: list[str] = []
            for key in ("x_column", "y_column", "group_column"):
                col = question.get(key)
                if col:
                    col_names.append(col)

            plot_result = PlotResult(
                figure=fig,
                title=title,
                plot_type=chart_type,
                description_for_ai=_build_description(
                    question, df,
                ),
                column_names=col_names,
            )
            results.append(plot_result)

        except Exception:
            logger.warning(
                "Failed to create %s plot for: %s",
                chart_type,
                question.get("question", ""),
                exc_info=True,
            )
            continue

    return results


# ------------------------------------------------------------------
# Batch commentary
# ------------------------------------------------------------------


def _load_commentary_prompt() -> str:
    """Read the chart-commentary system prompt from disk.

    Returns:
        The raw prompt template string.

    Raises:
        FileNotFoundError: If the prompt file is missing.
    """
    return _COMMENTARY_PROMPT_PATH.read_text(encoding="utf-8")


def _build_chart_batch(
    plot_results: list[PlotResult],
    start_idx: int,
) -> str:
    """Build a user message describing a batch of charts.

    Args:
        plot_results: Slice of PlotResult objects for this batch.
        start_idx: Global starting index for numbering.

    Returns:
        Formatted string listing each chart's metadata.
    """
    lines: list[str] = []
    for offset, pr in enumerate(plot_results):
        idx = start_idx + offset + 1
        cols_str = ", ".join(pr.column_names)
        lines.append(
            f"Chart {idx}:\n"
            f"  index: \"{idx}\"\n"
            f"  title: \"{pr.title}\"\n"
            f"  type: \"{pr.plot_type}\"\n"
            f"  columns: [{cols_str}]\n"
            f"  description: \"{pr.description_for_ai}\""
        )
    return "\n\n".join(lines)


def _call_commentary_api(
    client: OpenAI,
    system_prompt: str,
    user_message: str,
) -> dict[str, str]:
    """Call OpenAI for chart commentary with one retry.

    Args:
        client: Configured OpenAI client.
        system_prompt: The system prompt for commentary.
        user_message: The formatted chart batch message.

    Returns:
        Dict mapping chart index strings to commentary strings.
    """
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
            )
            content = (
                response.choices[0].message.content or "{}"
            )
            return json.loads(content)
        except Exception as exc:
            is_rate_limit = "rate" in str(exc).lower()
            if attempt < max_attempts - 1 and is_rate_limit:
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "Rate limit hit, retrying in %ds", wait,
                )
                time.sleep(wait)
            else:
                logger.error(
                    "Commentary API call failed: %s", exc,
                )
                return {}
    return {}


def generate_batch_commentary(
    plot_results: list[PlotResult],
    api_key: str,
    batch_size: int = 10,
) -> dict[str, str]:
    """Generate AI commentary for a list of chart PlotResults.

    Sends chart metadata to OpenAI in batches and collects
    commentary keyed by chart title.

    Args:
        plot_results: All PlotResult objects to generate
            commentary for.
        api_key: OpenAI API key.
        batch_size: Number of charts per API call.
            Defaults to 10.

    Returns:
        Dict mapping chart title to commentary string.
        Returns an empty dict if plot_results is empty or
        all API calls fail.
    """
    if not plot_results:
        return {}

    try:
        system_prompt = _load_commentary_prompt()
    except FileNotFoundError:
        logger.error("Commentary prompt file not found.")
        return {}

    client = OpenAI(api_key=api_key)
    title_map: dict[str, str] = {}

    for batch_start in range(0, len(plot_results), batch_size):
        batch = plot_results[
            batch_start : batch_start + batch_size
        ]
        user_message = _build_chart_batch(batch, batch_start)
        raw = _call_commentary_api(
            client, system_prompt, user_message,
        )

        for idx_str, commentary in raw.items():
            try:
                offset = int(idx_str) - batch_start - 1
                if 0 <= offset < len(batch):
                    title = batch[offset].title
                    title_map[title] = str(commentary)
            except (ValueError, IndexError):
                logger.warning(
                    "Skipping invalid index '%s' in "
                    "commentary response",
                    idx_str,
                )

    return title_map
