# CSV Dashboard Generator

A Streamlit application that lets you upload a CSV dataset and optionally provide a schema description to automatically generate a comprehensive analytics dashboard with summary statistics, univariate plots, bivariate plots, and AI-generated insights.
## Demo


https://github.com/user-attachments/assets/8c17ff46-4fb4-4e11-8e31-ed5aa2f945d5



## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- An OpenAI API key (optional — needed only for AI-powered features)

## Setup

### 1. Create a virtual environment and install dependencies

```bash
cd dashboard_generator
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Configure environment variables (optional)

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-key-here
```

Alternatively, you can enter the API key directly in the app sidebar.

## Running the App

```bash
uv run streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Usage

1. Upload a CSV file using the file uploader.
2. Optionally paste a schema description in the text area to enrich column type detection and AI quality.
3. Browse the five tabs:
   - **Schema** — column types, descriptions, null percentages, unique counts
   - **Summary Statistics** — descriptive stats for numerical and categorical columns
   - **Univariate Analysis** — histograms and bar charts (up to 9 plots)
   - **Bivariate Analysis** — correlation heatmap, scatter plots, grouped bar charts (up to 9 plots)
   - **AI Insights** — 3 AI-generated analytical questions with corresponding plots and commentary
4. Enter an OpenAI API key in the sidebar to enable AI-powered features (schema parsing, insight generation, plot commentary).
