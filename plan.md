# Dashboard Generator - Implementation Plan

## Context

Build a web application that lets users upload a CSV dataset **and provide a schema description** to automatically generate a comprehensive analytics dashboard. The dashboard includes summary statistics, univariate plots, bivariate plots, and AI-generated insights with commentary beneath each chart.

**Inputs:** CSV file upload + schema description (text/markdown pasted into a text area)
**Tech choices:** Streamlit, Pandas, Matplotlib/Seaborn, OpenAI API (gpt-4o-mini)

---

## Project Structure

```
dashboard_generator/
├── app.py                        # Streamlit entry point
├── requirements.txt
├── .gitignore                    # Includes output/ directory
├── .env.example                  # Template for OPENAI_API_KEY
├── .streamlit/
│   └── config.toml               # Theme + max upload size
├── components/
│   ├── __init__.py
│   ├── tab_summary.py            # Tab 2 rendering logic                   (Phase 3A)
│   ├── tab_univariate.py         # Tab 3 rendering logic                   (Phase 3B)
│   └── tab_bivariate.py          # Tab 4 rendering logic                   (Phase 3C)
├── output/                       # Generated plots saved here (created at runtime)
│   ├── univariate/               # Histograms + bar charts as PNG
│   ├── bivariate/                # Heatmap, scatter, grouped bars as PNG
│   └── ai_insights/              # AI-generated insight plots as PNG
├── modules/
│   ├── __init__.py
│   ├── constants.py              # Thresholds, limits, defaults
│   ├── data_loader.py            # CSV upload, validation, sampling
│   ├── schema_parser.py          # Parse user-provided schema text into structured format
│   ├── schema_detector.py        # Column classification, merges user schema + auto-detection
│   ├── chart_helpers.py          # Shared matplotlib styling + PlotResult  (Phase 2)
│   ├── summary_stats.py          # Descriptive statistics                  (Phase 3A)
│   ├── univariate_plots.py       # Histograms + bar charts                 (Phase 3B)
│   ├── bivariate_plots.py        # Correlation heatmap, scatter, grouped bars (Phase 3C)
│   └── ai_insights.py            # OpenAI: questions, insight plots, commentary
└── prompts/
    ├── insightful_questions.txt  # Prompt template for 3 questions
    └── chart_commentary.txt      # Prompt template for batch commentary
```

---

## Dashboard Layout

The app uses Streamlit's `layout="wide"` mode. Content flows top-to-bottom with a sidebar for configuration.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SIDEBAR                │  MAIN CONTENT                                │
│                         │                                              │
│  ┌───────────────────┐  │  ┌──────────────────────────────────────────┐ │
│  │ OpenAI API Key    │  │  │  📊 CSV Dashboard Generator (title)     │ │
│  │ [••••••••••••]    │  │  └──────────────────────────────────────────┘ │
│  ├───────────────────┤  │                                              │
│  │ Max Rows          │  │  ┌──────────────────────────────────────────┐ │
│  │ [10000        ]   │  │  │  Upload CSV:  [ Choose File ]           │ │
│  └───────────────────┘  │  │  Schema:      [ Text area ...         ] │ │
│                         │  │               [ (optional)             ] │ │
│                         │  └──────────────────────────────────────────┘ │
│                         │                                              │
│                         │  ┌─ Schema ─┬─ Summary ─┬─ Univariate ─┬──┐ │
│                         │  │          │  Stats    │  Analysis    │..│ │
│                         │  └──────────┴───────────┴──────────────┴──┘ │
│                         │  (tab content below)                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tab 1: Schema
```
┌──────────────────────────────────────────────────────────────┐
│  Headline metrics (st.metric in 4 columns)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Rows     │ │ Columns  │ │ Numerical│ │Categorical│       │
│  │  10,000  │ │    15    │ │    8     │ │    7     │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│                                                              │
│  Schema table (st.dataframe, full width):                    │
│  ┌────────────┬──────────┬─────────────┬────────┬──────────┐ │
│  │ Column     │ Type     │ Description │ Null % │ Unique # │ │
│  ├────────────┼──────────┼─────────────┼────────┼──────────┤ │
│  │ age        │ numerical│ Age in yrs  │  2.1%  │   72     │ │
│  │ city       │ categor. │ Home city   │  0.0%  │   15     │ │
│  │ ...        │ ...      │ ...         │  ...   │  ...     │ │
│  └────────────┴──────────┴─────────────┴────────┴──────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Tab 2: Summary Statistics
```
┌──────────────────────────────────────────────────────────────┐
│  "Numerical Columns" (st.subheader)                          │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ st.dataframe — rows=columns, cols=mean/median/std/...   ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  "Categorical Columns" (st.subheader)                        │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ st.dataframe — rows=columns, cols=unique/mode/freq/...  ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

### Tab 3: Univariate Analysis (max 9 plots, 3x3 grid)
```
┌──────────────────────────────────────────────────────────────┐
│  3-column grid using st.columns(3)                           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ [histogram]  │  │ [histogram]  │  │ [histogram]  │       │
│  │  AI comment  │  │  AI comment  │  │  AI comment  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ [histogram]  │  │ [bar chart]  │  │ [bar chart]  │       │
│  │  AI comment  │  │  AI comment  │  │  AI comment  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ [bar chart]  │  │ [bar chart]  │  │ [bar chart]  │       │
│  │  AI comment  │  │  AI comment  │  │  AI comment  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

### Tab 4: Bivariate Analysis (max 9 plots, heatmap full-width + 3x3-ish grid)
```
┌──────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐│
│  │         Correlation Heatmap (full width)                 ││
│  │         AI commentary below                             ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  Remaining 8 plots in 3-column grid:                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ [scatter]    │  │ [scatter]    │  │ [scatter]    │       │
│  │  AI comment  │  │  AI comment  │  │  AI comment  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ [scatter]    │  │ [grouped bar]│  │ [grouped bar]│       │
│  │  AI comment  │  │  AI comment  │  │  AI comment  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │ [grouped bar]│  │ [grouped bar]│                          │
│  │  AI comment  │  │  AI comment  │                          │
│  └──────────────┘  └──────────────┘                          │
└──────────────────────────────────────────────────────────────┘
```

### Tab 5: AI Insights (3 plots, 1 per row full-width)
```
┌──────────────────────────────────────────────────────────────┐
│  "Question 1: Is there a relationship between...?"           │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              [insight plot — full width]                 ││
│  └──────────────────────────────────────────────────────────┘│
│  AI commentary: "This scatter plot reveals that..."          │
│                                                              │
│  "Question 2: How does X vary across...?"                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              [insight plot — full width]                 ││
│  └──────────────────────────────────────────────────────────┘│
│  AI commentary: "The grouped bar chart shows..."             │
│                                                              │
│  "Question 3: What is the distribution of...?"               │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              [insight plot — full width]                 ││
│  └──────────────────────────────────────────────────────────┘│
│  AI commentary: "The histogram indicates that..."            │
└──────────────────────────────────────────────────────────────┘
```

### Plot counts summary

| Section | Max plots |
|---|---|
| Univariate (3x3 grid) | 9 |
| Bivariate (1 heatmap + up to 8 in grid) | 9 |
| AI Insights (full-width) | 3 |
| **Total** | **21** |

---

## Implementation Phases

5 phases total. Phase 3 contains 3 parallel workstreams (3A, 3B, 3C). Each phase is independently testable — run `streamlit run app.py` after each phase to verify.

---

### Phase 1: Blank Layout Skeleton

**Goal:** Show the full dashboard structure with placeholder content. No logic, no data processing.

**Files to create:**
- `dashboard_generator/app.py` — Streamlit entry point
- `dashboard_generator/requirements.txt` — `streamlit`, `pandas`, `matplotlib`, `seaborn`, `openai`, `python-dotenv`
- `dashboard_generator/.streamlit/config.toml` — theme + `maxUploadSize=200`
- `dashboard_generator/modules/__init__.py`
- `dashboard_generator/modules/constants.py` — all tunable values: `MAX_ROWS_DEFAULT=10000`, `MAX_UNIQUE_FOR_CATEGORICAL=20`, `MAX_UNIVARIATE_PLOTS=9`, `MAX_BIVARIATE_PLOTS=9`, `MAX_CATEGORICAL_BARS=15`, `MIN_CORRELATION_THRESHOLD=0.3`, `OPENAI_MODEL="gpt-4o-mini"`, `OUTPUT_DIR="output"`, `PLOT_SAVE_DPI=150`, etc.

**What `app.py` does:**
- `st.set_page_config(layout="wide")`, title
- Sidebar: API key input (password), max rows slider — non-functional, just rendered
- Main area: file uploader (disabled/non-functional), schema text area
- 5 tabs with placeholder text:
  - Tab 1 "Schema": `st.info("Schema will appear here after uploading data")`
  - Tab 2 "Summary Statistics": placeholder with sample `st.metric` boxes (greyed out / dummy values) and empty dataframe shells
  - Tab 3 "Univariate Analysis": 3x3 grid of `st.columns(3)` with grey placeholder boxes (`st.container` with border) labeled "Plot 1", "Plot 2", ... "Plot 9", each with "AI commentary" text below
  - Tab 4 "Bivariate Analysis": full-width placeholder for heatmap + 3-col grid of 8 placeholder boxes
  - Tab 5 "AI Insights": 3 full-width placeholder blocks labeled "Insight 1", "Insight 2", "Insight 3"

**How to test:**
1. `pip install -r requirements.txt`
2. `streamlit run dashboard_generator/app.py`
3. Verify: all 5 tabs render, sidebar shows controls, placeholders visible in every tab, 3x3 grid layout looks correct in wide mode

---

### Phase 2: Data Upload + Schema Detection + Chart Helpers

**Goal:** User can upload a CSV and optionally paste a schema. The Schema tab populates with real data. Also create the shared `chart_helpers.py` module needed by the parallel workstreams in Phase 3.

**Files to create:**
- `modules/data_loader.py` — CSV loading, validation, sampling
- `modules/schema_parser.py` — parse user schema text via OpenAI
- `modules/schema_detector.py` — auto-detect column types, merge with user schema
- `modules/chart_helpers.py` — shared matplotlib styling + `PlotResult` dataclass
- `components/__init__.py`
- `components/tab_summary.py` — skeleton with placeholder content for Tab 2
- `components/tab_univariate.py` — skeleton with placeholder content for Tab 3
- `components/tab_bivariate.py` — skeleton with placeholder content for Tab 4

**`modules/data_loader.py`:**
- Accept Streamlit `UploadedFile`, read with `pd.read_csv`
- Encoding fallback: try utf-8, then latin-1
- Validate: reject empty DataFrames
- Drop columns that are 100% null
- Sample if rows exceed `max_rows` (random sample, fixed seed=42)
- Cap columns at 50 with a warning
- Return `(df, warnings_list)`

**`modules/schema_parser.py`:**
- Accept user-provided schema text (from `st.text_area`)
- Use OpenAI to parse free-form text into structured JSON: `{"columns": [{"name": "col_name", "type": "numerical|categorical|datetime", "description": "..."}]}`
- Validate: match parsed column names to actual CSV columns (fuzzy match)
- Return `UserSchema` dataclass: list of `UserColumnInfo(name, declared_type, description)`
- **Schema is optional** — if not provided, fall back to pure auto-detection

**`modules/schema_detector.py`:**
- **Merge two sources**: user-provided schema + auto-detected types
- Auto-detection heuristic: numeric dtype with >20 unique values → numerical; <=20 → categorical; object → try `pd.to_datetime` then categorical; bool → categorical
- **User schema takes priority**: overrides auto-detection
- Return `SchemaInfo` dataclass with: `n_rows`, `n_cols`, `numerical_cols`, `categorical_cols`, `datetime_cols`, per-column metadata (name, dtype, semantic_type, **description**, null_count, pct_missing, n_unique)

**`modules/chart_helpers.py`:**
- `configure_plot_style()`: set `seaborn-v0_8-whitegrid`, `Set2` palette, `dpi=100`
- `PlotResult` dataclass: `figure`, `title`, `plot_type`, `description_for_ai`, `column_names`
- `save_plot(plot_result, subfolder)`: save a `PlotResult`'s figure to `OUTPUT_DIR/<subfolder>/<sanitized_title>.png`
  - Creates `OUTPUT_DIR/<subfolder>/` directory if it doesn't exist (`os.makedirs(..., exist_ok=True)`)
  - Sanitizes title for filename: lowercase, replace spaces/special chars with underscores
  - Saves with `fig.savefig(path, dpi=PLOT_SAVE_DPI, bbox_inches="tight")`
  - Stores the saved file path on `PlotResult.saved_path` (new optional field)
  - Returns the saved file path

**`components/tab_summary.py`, `tab_univariate.py`, `tab_bivariate.py` (skeletons):**
- Each file exports a single `render(df, schema_info)` function
- Skeleton implementation renders the same placeholder content from Phase 1 (e.g., `st.info("Summary statistics will appear here...")`)
- These files will be independently updated by the Phase 3 workstreams without touching `app.py`

**Update `app.py`:**
- Wire file uploader + schema text area to loading/parsing logic
- Tab 1 "Schema": replace placeholder with real headline metrics (`st.metric` in 4 columns: Rows, Columns, Numerical, Categorical) and schema table (`st.dataframe` with Column, Type, Description, Null %, Unique #)
- **Refactor tabs 2, 3, 4** to delegate rendering to component files:
  ```python
  from components.tab_summary import render as render_summary
  from components.tab_univariate import render as render_univariate
  from components.tab_bivariate import render as render_bivariate

  with tab2:
      render_summary(df, schema_info)
  with tab3:
      render_univariate(df, schema_info)
  with tab4:
      render_bivariate(df, schema_info)
  ```
- Tab 5 "AI Insights" remains as inline placeholder (updated in Phase 4)

**How to test:**
1. `streamlit run dashboard_generator/app.py`
2. Upload a CSV (e.g., Iris) — Schema tab shows real column info, metrics
3. Upload with schema text pasted — verify descriptions appear in table, type overrides work
4. Upload without schema text — verify auto-detection works alone
5. Upload empty CSV — verify `st.error` message
6. Upload large CSV (>10K rows) — verify sampling warning appears
7. Verify `chart_helpers.py` imports cleanly: `from modules.chart_helpers import PlotResult, configure_plot_style`

---

### Phase 3: Summary Statistics + Univariate Plots + Bivariate Plots (PARALLEL)

**Goal:** Implement all three analysis tabs in parallel. Each workstream produces an independent module and updates its own component file (no shared file conflicts). They share only the `SchemaInfo` output from Phase 2 and the `chart_helpers.py` utilities.

---

#### Workstream 3A: Summary Statistics

**Files to create:**
- `modules/summary_stats.py`

**Files to modify:**
- `components/tab_summary.py` (owns this file — no other workstream touches it)

**`modules/summary_stats.py`:**
- Numerical columns: mean, median, std, min, max, 25th/75th percentiles, skewness
- Categorical columns: unique count, mode, mode frequency, top 5 values
- Return structured dicts for rendering

**Update `components/tab_summary.py`:**
- Replace placeholder with real rendering in the `render(df, schema_info)` function
- Subheader "Numerical Columns" + `st.dataframe` (rows=columns, cols=mean/median/std/min/max/25%/75%/skewness)
- Subheader "Categorical Columns" + `st.dataframe` (rows=columns, cols=unique/mode/mode_freq/top_5)

**How to test 3A:**
1. Upload Iris CSV — verify numerical stats table with 4 numerical columns, values match expected (e.g., sepal_length mean ~5.84)
2. Upload Titanic CSV — verify both numerical and categorical stats tables appear
3. Dataset with only categorical columns — verify numerical section shows `st.info("No numerical columns")`, categorical table still works

---

#### Workstream 3B: Univariate Plots

**Files to create:**
- `modules/univariate_plots.py`

**Files to modify:**
- `components/tab_univariate.py` (owns this file — no other workstream touches it)

**`modules/univariate_plots.py`:**
- **Capped at 9 total plots** (`MAX_UNIVARIATE_PLOTS=9`)
  - Split: up to 5 numerical + 4 categorical (adjusted if one type has fewer)
  - Numerical: rank by variance (descending), pick top columns
  - Categorical: rank by unique count (descending), pick top columns
- Numerical: `sns.histplot` with KDE overlay
- Categorical: horizontal bar chart of value counts (top 15 categories, rest as "Other")
- `description_for_ai` includes stats (mean, median, etc.) — stored but not used yet

**Update `components/tab_univariate.py`:**
- Replace placeholder with real rendering in the `render(df, schema_info)` function
- 3x3 grid: loop through `PlotResult` list, place into `st.columns(3)` cells
- Each cell: `st.pyplot(fig)` + placeholder text "AI commentary will appear here" (greyed `st.caption`)
- Save each plot: `save_plot(plot_result, "univariate")` → writes to `output/univariate/`
- `plt.close(fig)` after rendering and saving

**Example output files:**
```
output/univariate/
├── hist_sepal_length.png
├── hist_sepal_width.png
├── hist_petal_length.png
├── hist_petal_width.png
└── bar_species.png
```

**How to test 3B:**
1. Upload Iris CSV — verify 4 histograms + 1 bar chart (species) in grid layout
2. Upload a wide dataset (>9 plottable columns) — verify exactly 9 plots shown
3. Verify plots render correctly: histograms have KDE curves, bar charts are horizontal
4. Check no matplotlib memory warnings (figures are closed after rendering)
5. Verify `output/univariate/` contains PNG files matching the rendered plots

---

#### Workstream 3C: Bivariate Plots

**Files to create:**
- `modules/bivariate_plots.py`

**Files to modify:**
- `components/tab_bivariate.py` (owns this file — no other workstream touches it)

**`modules/bivariate_plots.py`:**
- **Capped at 9 total plots** (`MAX_BIVARIATE_PLOTS=9`):
  - 1 correlation heatmap (always included if >=2 numerical cols)
  - Up to 4 scatter plots: top correlated numerical pairs (|r| >= 0.3), sorted by |r| descending
  - Up to 4 grouped bar charts: top categorical-vs-numerical pairs ranked by eta-squared (between-group variance / total variance)
  - If fewer of one type, remaining slots go to the other
- **Correlation heatmap**: `sns.heatmap`, annotated if <=15 columns, `cmap="RdBu_r"`, centered at 0
- **Scatter plots**: `sns.scatterplot` with alpha=0.6
- **Grouped bar charts**: mean of numerical grouped by categorical, top 15 categories

**Update `components/tab_bivariate.py`:**
- Replace placeholder with real rendering in the `render(df, schema_info)` function
- Full-width heatmap at top + "AI commentary will appear here" caption
- Remaining plots in 3-column grid, each with placeholder commentary caption
- Save each plot: `save_plot(plot_result, "bivariate")` → writes to `output/bivariate/`

**Example output files:**
```
output/bivariate/
├── heatmap_correlation.png
├── scatter_sepal_length_vs_petal_length.png
├── scatter_sepal_width_vs_petal_width.png
├── grouped_bar_species_vs_sepal_length.png
└── ...
```

**How to test 3C:**
1. Upload Iris CSV — verify heatmap of 4 numerical cols, scatter plots for top correlated pairs
2. Upload Titanic CSV — verify grouped bar charts (e.g., Pclass vs Fare) appear alongside scatter plots
3. Dataset with only 1 numerical column — verify "Not enough numerical columns for correlation" message, no heatmap
4. Dataset with no categorical columns — verify all 8 non-heatmap slots used for scatter plots
5. Verify `output/bivariate/` contains PNG files matching the rendered plots

---

#### Phase 3 — Integration & Combined Test

Merge all three branches. Since each workstream only touches its own files, merges are conflict-free:

| Workstream | Creates | Modifies |
|---|---|---|
| 3A | `modules/summary_stats.py` | `components/tab_summary.py` |
| 3B | `modules/univariate_plots.py` | `components/tab_univariate.py` |
| 3C | `modules/bivariate_plots.py` | `components/tab_bivariate.py` |

**No changes to `app.py` needed** — it already imports and calls the component `render()` functions from Phase 2.

**Combined tests after merge:**
1. Upload Iris CSV — verify tabs 2, 3, and 4 all show real content simultaneously
2. Upload Titanic CSV — verify all three tabs handle mixed numerical/categorical data
3. Verify no import conflicts between modules (all use `chart_helpers.PlotResult`)
4. Verify `app.py` tab rendering order is consistent (Schema → Summary → Univariate → Bivariate → AI Insights)

---

### Phase 4: AI Insights (Questions + Plots)

**Goal:** The AI Insights tab shows 3 AI-generated questions with corresponding plots.

**Files to create:**
- `modules/ai_insights.py`
- `prompts/insightful_questions.txt`

**`modules/ai_insights.py` (question generation + insight plots only, no commentary yet):**
- `generate_questions(schema_info, df_sample, api_key)`:
  - Build prompt with schema text + user-provided column descriptions + 5-row CSV sample + column stats
  - Call OpenAI (`gpt-4o-mini`, `response_format=json_object`) → JSON with 3 questions, each having: question text, chart_type (histogram/scatter/bar_chart/box_plot/grouped_bar), x_column, y_column, group_column
  - Validate all column names against `df.columns`, skip questions with invalid columns
- `generate_insight_plots(df, questions)`:
  - Map each question's chart spec to matplotlib figure
  - Return list of `PlotResult`

**Update `app.py`:**
- Sidebar API key now functional: required for this tab
- Tab 5 "AI Insights": replace placeholder with:
  - `st.spinner("Generating AI insights...")`
  - For each question: `st.subheader(question_text)` + `st.pyplot(fig)` + placeholder "AI commentary will appear here"
- If no API key: `st.warning("Enter your OpenAI API key in the sidebar to enable AI insights.")`
- Save each insight plot: `save_plot(plot_result, "ai_insights")` → writes to `output/ai_insights/`
- Use `@st.cache_data` on the OpenAI question generation call (keyed on schema hash + api_key)

**Example output files:**
```
output/ai_insights/
├── insight_1_relationship_between_x_and_y.png
├── insight_2_how_does_x_vary.png
└── insight_3_distribution_of_z.png
```

**How to test:**
1. Upload Iris CSV + provide API key — verify 3 questions appear with relevant plots
2. Upload without API key — verify warning message, no crash
3. Verify questions reference real columns (not hallucinated)
4. Verify each question has a plot that makes sense for the question
5. Verify `output/ai_insights/` contains PNG files for each generated insight

---

### Phase 5: AI Commentary for All Plots

**Goal:** Every plot across all tabs gets an AI-generated commentary below it.

**Files to create:**
- `prompts/chart_commentary.txt`

**Update `modules/ai_insights.py` — add batch commentary:**
- `generate_batch_commentary(plot_results, api_key, batch_size=10)`:
  - Collect ALL `PlotResult` objects from univariate + bivariate + insight plots
  - Build batched prompt: each chart's title, type, columns, `description_for_ai`
  - Call OpenAI per batch → JSON `{"1": "commentary...", "2": "..."}`
  - Return dict mapping chart title → commentary string
- `response_format={"type": "json_object"}` for reliable parsing
- Retry once on `RateLimitError` with exponential backoff
- Total: ~3-5 API calls for entire dashboard

**Update `app.py`:**
- After generating all plots, call `generate_batch_commentary()` with all `PlotResult` objects
- Replace all "AI commentary will appear here" placeholders with actual `st.info(f"**AI Commentary:** {text}")`
- Tab 3 (Univariate): commentary below each plot in the 3x3 grid
- Tab 4 (Bivariate): commentary below heatmap and each plot in grid
- Tab 5 (AI Insights): commentary below each insight plot
- If no API key: plots still render, commentary slots show `st.caption("Provide an API key to enable AI commentary")`
- Use `@st.cache_data` on commentary call (keyed on plot descriptions hash + api_key)

**How to test:**
1. Upload Iris CSV + API key — verify commentary appears below every plot in tabs 3, 4, and 5
2. Verify commentary is specific (references actual values, column names) not generic
3. Upload without API key — verify all plots still render, commentary slots show fallback message
4. Upload a different dataset — verify commentary is relevant to the new data, not cached from previous
5. Test edge cases: empty CSV, single-column CSV, all-null columns, large CSV (>10K rows)

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| 5 phases (3 sequential + 1 parallel + 1 sequential) | Phases 3A/3B/3C are independent; parallelizing them reduces wall-clock implementation time |
| `chart_helpers.py` created in Phase 2 | Shared dependency for both plot workstreams; must exist before parallel phase begins |
| `gpt-4o-mini` for all AI calls | Commentary/questions are simple tasks; 10x cheaper than gpt-4o, easy to upgrade in `constants.py` |
| Batch commentary (groups of 10) | Minimizes API calls (3-5 total) while staying within token limits |
| Eta-squared for cat-vs-num pairs | Principled statistical measure of association; avoids random pair selection or full enumeration |
| 9-plot cap per section | Keeps dashboard scannable; 3x3 grid fits naturally on screen |
| Cache data, not figures | Matplotlib figures aren't serializable; data computation and API calls are the expensive parts |
| Save all plots to `output/` as PNG | Enables offline review, sharing, and embedding; `save_plot()` in `chart_helpers.py` centralizes save logic |
| Graceful degradation without API key | Dashboard is fully functional (stats + all plots) without OpenAI; AI features are additive |
| OpenAI parses user schema text | Handles any format (markdown tables, bullet lists, prose) without brittle regex; falls back to auto-detection on parse failure |
| User schema overrides auto-detection | User knows their domain — if they say zip_code is categorical, that trumps pandas inferring int64 |
| Schema is optional | App works with just a CSV; schema text enriches type detection and AI quality but isn't required |

---

## Error Handling

- **Data loading**: catch `ParserError`, `EmptyDataError`, `UnicodeDecodeError` → `st.error`
- **Schema parsing**: OpenAI fails to parse user text → warn and fall back to auto-detection only; user mentions columns not in CSV → ignore with warning; no schema provided → pure auto-detection
- **Schema edge cases**: 0 numerical cols → skip numerical sections with `st.info`; single column → skip bivariate; single-unique-value columns → exclude
- **Plot failures**: wrap each plot in try/except, skip failed plots with a warning
- **OpenAI errors**: missing key → warn and skip AI; rate limit → retry once; JSON parse failure → skip commentary; hallucinated columns → skip that insight question
