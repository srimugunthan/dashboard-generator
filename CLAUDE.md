# CLAUDE.md — Streamlit App

This file defines instructions and constraints for Claude Code when working in this repository.

---

## 🚨 Critical Constraints (Read First)

- **Never run any terminal command without explicit user approval.** Always show the command and wait for a "go ahead" before executing.
- **Never install packages, libraries, or tools** (no `pip install`, `pip uninstall`, `uv add`, `conda install`, or equivalent). If a new dependency is needed, propose it and let the user install it.
- **Never delete files or directories** without explicit approval.
- **Never modify `.env`, `.env.*`, or any secrets/config file** without explicit approval.
- **Never commit to git** or push to any remote without explicit approval.
- **Keep `requirements.txt` manually managed.** Do not auto-update it. If a new dependency is needed, mention it and let the user decide.

---

## Project Overview

This is a Python + Streamlit application. The entry point is `app.py` (or as specified in the project).

Assume the following structure unless told otherwise:

```
.
├── app.py                  # Main Streamlit entry point
├── pages/                  # Multi-page app pages (if applicable)
├── components/             # Reusable UI components
├── utils/                  # Helper functions and utilities
├── data/                   # Static or sample data files
├── requirements.txt        # Dependencies (manually managed)
├── .env                    # Environment variables (do not touch)
└── CLAUDE.md               # This file
```

---

## Python Style & Syntax Rules

### General

- Follow **PEP 8** strictly for all Python code.
- Maximum line length: **88 characters** (Black-compatible).
- Use **4 spaces** for indentation. Never use tabs.
- Use **double quotes** for strings (Black default), unless a string itself contains double quotes.
- Always add a **blank line at the end of every file**.

### Type Hints

- Use type hints on all function signatures (parameters and return types).
- Use `from __future__ import annotations` at the top of files when needed for forward references.
- Use `Optional[X]` or `X | None` (Python 3.10+) for nullable types — pick one style and stay consistent per file.
- Use `list`, `dict`, `tuple` (lowercase) instead of `List`, `Dict`, `Tuple` from `typing` for Python 3.9+.

```python
# Good
def load_data(filepath: str) -> pd.DataFrame:
    ...

def get_label(value: float | None = None) -> str:
    ...

# Bad
def load_data(filepath, df):
    ...
```

### Docstrings

- All public functions, classes, and modules must have docstrings.
- Use **Google-style docstrings**.

```python
def compute_metric(values: list[float], threshold: float = 0.5) -> float:
    """Compute a summary metric from a list of values.

    Args:
        values: A list of numeric values to aggregate.
        threshold: Cutoff threshold for filtering. Defaults to 0.5.

    Returns:
        The computed metric as a float.

    Raises:
        ValueError: If values is empty.
    """
    if not values:
        raise ValueError("values must not be empty.")
    ...
```

### Imports

- Organize imports in this order, each group separated by a blank line:
  1. Standard library
  2. Third-party libraries
  3. Local/project modules
- Use absolute imports. Avoid wildcard imports (`from module import *`).

```python
# Good
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.helpers import format_label
```

### Naming Conventions

| Entity | Convention | Example |
|---|---|---|
| Functions | `snake_case` | `load_data()` |
| Variables | `snake_case` | `df_filtered` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_ROWS = 1000` |
| Classes | `PascalCase` | `DataLoader` |
| Streamlit pages | `snake_case` filenames | `pages/1_overview.py` |
| Private helpers | leading underscore | `_validate_input()` |

---

## Streamlit-Specific Guidelines

- Place all `st.*` calls in the main script or page files. Keep business logic in `utils/` or `components/`.
- Use `@st.cache_data` for functions that load or transform data.
- Use `@st.cache_resource` for loading models, DB connections, or other heavy singleton resources.
- Avoid putting long-running logic directly in the top-level script body — wrap it in cached functions.
- Use `st.session_state` for stateful interactions. Initialize keys with a guard:

```python
if "selected_item" not in st.session_state:
    st.session_state.selected_item = None
```

- Prefer `st.columns()` and `st.container()` for layout rather than deeply nested conditionals.
- Always handle empty/null data states gracefully with `st.warning()` or `st.info()` rather than letting errors surface to the user.

---

## Error Handling

- Use specific exception types. Avoid bare `except:` clauses.
- Log errors to the console with `print()` or Python's `logging` module. Do not silently swallow exceptions.
- In Streamlit UI code, catch expected errors and surface them with `st.error()` or `st.warning()`.

```python
# Good
try:
    df = pd.read_csv(filepath)
except FileNotFoundError:
    st.error(f"Data file not found: {filepath}")
    st.stop()

# Bad
try:
    df = pd.read_csv(filepath)
except:
    pass
```

---

## What Claude Should Always Do

- **Propose before acting.** For any non-trivial change, describe what you plan to do before writing code.
- **Show diffs or summaries** when editing existing files, especially multi-function modules.
- **Ask for clarification** if a request is ambiguous rather than making assumptions.
- **Prefer editing existing files** over creating new ones unless a new module is clearly warranted.
- **Keep functions small and focused.** If a function exceeds ~40 lines, consider breaking it up.

## What Claude Should Never Do

- Run `streamlit run` or any shell command without approval.
- Auto-format the entire codebase without being asked.
- Rename files or refactor module structure without explicit instruction.
- Add new dependencies to `requirements.txt` automatically.
- Modify any test files unless explicitly asked to do so.
