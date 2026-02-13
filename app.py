"""CSV Dashboard Generator — Streamlit entry point."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from components.tab_bivariate import render as render_bivariate
from components.tab_summary import render as render_summary
from components.tab_univariate import render as render_univariate
from modules.ai_insights import (
    generate_batch_commentary,
    generate_insight_plots,
    generate_questions,
)
from modules.bivariate_plots import generate_bivariate_plots
from modules.chart_helpers import PlotResult, save_plot
from modules.constants import MAX_ROWS_DEFAULT
from modules.data_loader import load_csv
from modules.schema_detector import SchemaInfo, detect_schema
from modules.schema_parser import UserSchema, parse_schema_text
from modules.univariate_plots import generate_univariate_plots

st.set_page_config(
    page_title="CSV Dashboard Generator",
    layout="wide",
)

st.title("CSV Dashboard Generator")

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
    )
    max_rows = st.slider(
        "Max Rows",
        min_value=1000,
        max_value=100000,
        value=MAX_ROWS_DEFAULT,
        step=1000,
    )

# ── Main area: Upload + Schema ────────────────────────────────
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
schema_text = st.text_area(
    "Schema Description (optional)",
    placeholder="Paste a description of your columns here...",
    height=120,
)

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Schema",
        "Summary Statistics",
        "Univariate Analysis",
        "Bivariate Analysis",
        "AI Insights",
    ]
)

# ── Data loading & schema detection ───────────────────────────
df: pd.DataFrame | None = None
schema_info: SchemaInfo | None = None

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        df, warnings = load_csv(
            file_bytes, uploaded_file.name, max_rows,
        )
        for w in warnings:
            st.warning(w)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    # Parse user schema (requires API key; skip if not provided)
    user_schema: UserSchema | None = None
    if schema_text and schema_text.strip() and api_key:
        with st.spinner("Parsing schema description..."):
            user_schema = parse_schema_text(
                schema_text,
                list(df.columns),
                api_key,
            )
    elif schema_text and schema_text.strip() and not api_key:
        st.info(
            "Enter an OpenAI API key in the sidebar to "
            "parse the schema description. Using "
            "auto-detection only."
        )

    schema_info = detect_schema(df, user_schema)

# ── Pre-generate plots & commentary ──────────────────────────
uni_plots: list[PlotResult] = []
biv_plots: list[PlotResult] = []
insight_plots: list[PlotResult] = []
questions: list[dict] = []
commentary: dict[str, str] = {}

if df is not None and schema_info is not None:
    uni_plots = generate_univariate_plots(df, schema_info)
    biv_plots = generate_bivariate_plots(df, schema_info)

    if api_key:
        with st.spinner("Generating AI insights..."):
            questions = generate_questions(
                schema_info, df, api_key,
            )
        if questions:
            insight_plots = generate_insight_plots(
                df, questions,
            )

    # Batch commentary for all plots when API key is present
    all_plots = uni_plots + biv_plots + insight_plots
    if api_key and all_plots:
        with st.spinner("Generating AI commentary..."):
            commentary = generate_batch_commentary(
                all_plots, api_key,
            )


# ── Tab 1: Schema ────────────────────────────────────────────
with tab1:
    if df is None or schema_info is None:
        st.info(
            "Schema will appear here after uploading data."
        )
        metric_cols = st.columns(4)
        metric_cols[0].metric("Rows", "\u2014")
        metric_cols[1].metric("Columns", "\u2014")
        metric_cols[2].metric("Numerical", "\u2014")
        metric_cols[3].metric("Categorical", "\u2014")
    else:
        metric_cols = st.columns(4)
        metric_cols[0].metric(
            "Rows", f"{schema_info.n_rows:,}",
        )
        metric_cols[1].metric(
            "Columns", str(schema_info.n_cols),
        )
        metric_cols[2].metric(
            "Numerical",
            str(len(schema_info.numerical_cols)),
        )
        metric_cols[3].metric(
            "Categorical",
            str(len(schema_info.categorical_cols)),
        )

        schema_rows = []
        for cm in schema_info.columns:
            schema_rows.append(
                {
                    "Column": cm.name,
                    "Type": cm.semantic_type,
                    "Description": cm.description or "\u2014",
                    "Null %": f"{cm.pct_missing}%",
                    "Unique #": cm.n_unique,
                }
            )
        st.dataframe(
            pd.DataFrame(schema_rows),
            use_container_width=True,
            hide_index=True,
        )

# ── Tab 2: Summary Statistics ────────────────────────────────
with tab2:
    if df is not None and schema_info is not None:
        render_summary(df, schema_info)
    else:
        st.info(
            "Summary statistics will appear here "
            "after uploading data."
        )

# ── Tab 3: Univariate Analysis ──────────────────────────────
with tab3:
    if df is not None and schema_info is not None:
        render_univariate(
            uni_plots, commentary or None,
        )
    else:
        st.info(
            "Univariate analysis will appear here "
            "after uploading data."
        )

# ── Tab 4: Bivariate Analysis ───────────────────────────────
with tab4:
    if df is not None and schema_info is not None:
        render_bivariate(
            biv_plots, commentary or None,
        )
    else:
        st.info(
            "Bivariate analysis will appear here "
            "after uploading data."
        )

# ── Tab 5: AI Insights ──────────────────────────────────────
with tab5:
    if df is None or schema_info is None:
        st.info(
            "AI insights will appear here "
            "after uploading data."
        )
    elif not api_key:
        st.warning(
            "Enter your OpenAI API key in the sidebar "
            "to enable AI insights."
        )
    elif not questions:
        st.warning(
            "Could not generate insight questions "
            "for this dataset."
        )
    else:
        for question, plot_result in zip(
            questions, insight_plots,
        ):
            st.subheader(question["question"])
            st.pyplot(plot_result.figure)
            if commentary and plot_result.title in commentary:
                st.info(
                    "**AI Commentary:** "
                    f"{commentary[plot_result.title]}"
                )
            else:
                st.caption(
                    "Provide an API key to enable "
                    "AI commentary."
                )
            save_plot(plot_result, "ai_insights")
            plt.close(plot_result.figure)
