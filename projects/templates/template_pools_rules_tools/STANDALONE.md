# STANDALONE.md — template_pools_rules_tools

Instructions for using this project **outside the monorepo** as a
self-contained package.

---

## What this project does

`template_pools_rules_tools` reads from three sibling resource directories
(`fonds/`, `rules/`, `tools/`) and returns typed, structured results. It is
primarily an exemplar for the [template repository](https://github.com/nousresearch/template)
but the `src/` package is fully forkable.

---

## Directory layout (standalone copy)

When forking, replicate this layout:

```
my_project/
├── pyproject.toml          # copy from this exemplar, adjust name/version
├── STANDALONE.md           # this file
├── CLAUDE.md               # agent guidance
├── fonds/
│   └── templates/
│       ├── template_bibliography/
│       │   ├── fonds.yaml
│       │   └── data/
│       │       ├── references.bib
│       │       └── references.csv
│       ├── template_contacts/
│       │   ├── fonds.yaml
│       │   └── data/
│       │       └── contacts.yaml
│       └── template_datasets/
│           ├── fonds.yaml
│           └── data/
│               └── datasets.yaml
├── rules/
│   └── templates/
│       ├── template_project_rules/
│       │   ├── rules.yaml
│       │   ├── soft/           # *.md guideline files
│       │   └── strong/         # *.yaml constraint files
│       └── template_manuscript_rules/
│           ├── rules.yaml
│           ├── soft/
│           └── strong/
├── tools/
│   └── templates/
│       └── template_code_executor/
│           └── tools.yaml
└── src/
    ├── __init__.py
    ├── types.py
    ├── fonds_reader.py
    ├── rules_applier.py
    ├── tools_invoker.py
    └── integration.py
```

---

## Adjusting repo-root resolution

The `src/` modules resolve the repo root using:

```python
pathlib.Path(__file__).resolve().parents[4]
```

This assumes the source file sits at depth 5 from the repo root:
`projects/templates/template_pools_rules_tools/src/<module>.py`.

**When you fork**, if your layout is different (e.g. `src/<module>.py` sits
only 1 level deep), update the `_repo_root()` helper in each module to use
the correct parent index, or replace it with an environment variable:

```python
import os

def _repo_root() -> pathlib.Path:
    env = os.environ.get("POOLS_RULES_TOOLS_ROOT")
    if env:
        return pathlib.Path(env).resolve()
    # fallback: <depth> levels above this file
    return pathlib.Path(__file__).resolve().parents[1]
```

Set `POOLS_RULES_TOOLS_ROOT=/path/to/my_project` before running.

---

## Installation

```bash
# Minimal — runtime only
pip install pyyaml

# Development (tests + type-checking)
pip install pyyaml pytest pytest-cov mypy
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

---

## Quick start

```python
from src.integration import run_integration_demo

result = run_integration_demo()

print(result["summary"])
# {
#   "fonds_loaded": 3,
#   "rules_sets_ok": 2,
#   "rules_sets_total": 2,
#   "tools_discovered": 1,
#   "tools_valid": 1,
#   "bib_entries": 42,
#   "contacts": 5,
#   "datasets": 3,
# }

from src.integration import generate_figure_data
rows = generate_figure_data(result)
for row in rows:
    print(row["label"], row["count"], row["status"])
```

---

## Running tests

```bash
# From the project root (standalone copy):
pytest tests/ -v --cov=src --cov-fail-under=90
```

---

## Type-checking

```bash
mypy src/ --strict
```

Expected output with a complete resource layout: **0 errors**.

---

## Minimal fonds.yaml schema

```yaml
name: my_bibliography
version: "1.0"
description: "My references fond"
```

---

## Minimal rules.yaml schema

```yaml
name: my_project_rules
version: "1.0"
description: "My governance rules"
```

---

## Minimal tools.yaml schema

```yaml
name: my_tool
version: "1.0"
description: "My executable tool"
entrypoints:
  - scripts/run.py
```

---

## Resilience guarantees

- All reader functions return `None` or empty collections when files are absent.
- No function raises on missing paths — they log a `WARNING` and return a safe
  default instead.
- Check `RuleSetResult["warnings"]` for structured error reports.

---

## Licence

Same as the parent template repository. See `LICENSE` at the repo root.
