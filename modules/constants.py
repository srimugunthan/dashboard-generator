"""Tunable constants and default values for the dashboard generator."""

# Data loading
MAX_ROWS_DEFAULT = 10000
MAX_COLUMNS = 50
RANDOM_SEED = 42

# Schema detection
MAX_UNIQUE_FOR_CATEGORICAL = 20

# Plot limits
MAX_UNIVARIATE_PLOTS = 9
MAX_BIVARIATE_PLOTS = 9
MAX_CATEGORICAL_BARS = 15
MIN_CORRELATION_THRESHOLD = 0.3

# OpenAI
OPENAI_MODEL = "gpt-4o-mini"

# Output
OUTPUT_DIR = "output"
PLOT_SAVE_DPI = 150
