# Script Conventions — template_prose_project

Orchestration rules for `scripts/` in the `template_prose_project`
exemplar. Sibling of
[`template_code_project/scripts/CONVENTIONS.md`](../../template_code_project/scripts/CONVENTIONS.md);
the same Thin-Orchestrator rule applies, adapted for prose/BibTeX
delegation.

## Thin Orchestrator Rule

Scripts **coordinate**; they never **analyze**:

```python
# CORRECT — script loads config and calls into src/
from src.config import load_project_config
from src.pipeline import run_prose_pipeline

def main() -> int:
    args = parse_args()
    config = load_project_config(Path(args.config))
    artifacts = run_prose_pipeline(config, project_root=Path(args.project_root))
    if args.strict and not artifacts.all_passed:
        return 1
    return 0
```

```python
# WRONG — script implements analysis inline
def main():
    config = yaml.safe_load(Path("manuscript/config.yaml").read_text())
    text = (Path("manuscript") / "00_abstract.md").read_text()
    words = len(re.findall(r"\b\w+\b", text))   # BAD — analysis in script
    if words < 100:
        sys.exit(1)
```

If a script line evaluates a manuscript property (readability,
heading hierarchy, citation density, BibTeX coverage), the work belongs
in `src/pipeline/checks.py` as a `_check_<name>` function — write it there and
test it.

## File Naming Convention

| Prefix | Meaning | Ordering hint |
|--------|---------|---------------|
| (no prefix) | Primary analysis script. Runs first. | `run_prose_pipeline.py` |
| `y_*` | Secondary stage; depends on primary outputs. | `y_generate_prose_figures.py` |
| `z_*` | Final stage; depends on everything above. | `z_generate_manuscript_variables.py` |

The alphabetical prefixes (`y_`, `z_`) are **human-readable hints** for
manual invocation order. The canonical pipeline (`scripts/runner/execute_pipeline.py`
at repo root) enforces ordering via its stage definitions, not via
filename. A forker introducing a new script that should run between
analysis and figures should name it `y_<verb>.py`.

## Import Patterns

```python
import sys
from pathlib import Path

# 1. Standard library
import argparse
import json
import logging

# 2. Third-party
# (this project does not use numpy in scripts; figures.py uses matplotlib via src/)

# 3. Path bootstrapping (per project — not a uv workspace member)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent
for p in (REPO_ROOT, PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# 4. Project source imports
from src.config import load_project_config
from src.pipeline import run_prose_pipeline

# 5. Infrastructure import
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)
```

The three bundled scripts import `get_logger` directly (see
`run_prose_pipeline.py:24`): after the `sys.path` bootstrap above,
`infrastructure/` is always importable, so no fallback is needed. If you
fork a script to run in an environment where `infrastructure/` may be
absent, wrap the import as optional hardening:

```python
try:
    from infrastructure.core.logging.utils import get_logger

    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
```

The triple `sys.path.insert` is required because `template_prose_project`
is not a `[tool.uv.workspace]` member at the repo root — the project
runs from the repo root via `uv run` but its `src/` is not on the
import path until the script adds it. This is intentional (keeps the
template easily forkable without a workspace package), not a defect.

## CLI Argument Patterns

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("projects/templates/template_prose_project/manuscript/config.yaml"),
        help="Path to project config YAML.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("projects/templates/template_prose_project"),
        help="Project root directory (for isolated runs in tests).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any check fails.",
    )
    return parser.parse_args(argv)
```

The `--project-root` flag is what makes `test_scripts.py` able to run
the script against an isolated `tmp_path` copy of `manuscript/` without
touching the project's real `output/`.

## Output Layout

Scripts must write to the standard `output/` layout (paths relative to
`--project-root`):

| Path | Producer | Notes |
|---|---|---|
| `output/manuscript_report.json` | `run_prose_pipeline.py` | Aggregate `ManuscriptReport` |
| `output/checks.json` | `run_prose_pipeline.py` | `List[CheckResult]` |
| `output/review_report.md` | `run_prose_pipeline.py` | Human-readable review |
| `output/run_summary.json` | `run_prose_pipeline.py` | One-line metadata |
| `output/figures/*.png` | `y_generate_prose_figures.py` | 3 diagnostic PNGs |
| `output/data/manuscript_variables.json` | `z_generate_manuscript_variables.py` | Substitution map |
| `output/manuscript/*.md` | `z_generate_manuscript_variables.py` | Token-resolved sections (renderer input) |

## Exit Code Contract

| Exit code | Meaning |
|---|---|
| `0` | Script ran successfully; all checks passed (or `--strict` not set). |
| `1` | `--strict` was set and at least one check failed. |
| `2` | A precondition was not met (e.g., `y_generate_prose_figures.py` requires `manuscript_report.json` to exist). |

Test these exit codes in `test_scripts.py` via `subprocess.run` (see
[`../tests/PATTERNS.md`](../tests/PATTERNS.md)).

## Error Handling

```python
try:
    artifacts = run_prose_pipeline(config, project_root=project_root)
except FileNotFoundError as e:
    logger.error("Manuscript not found: %s", e)
    logger.info("Did you set --project-root correctly?")
    sys.exit(2)
```

- Log errors via `logger.error()` (or `print(..., file=sys.stderr)` if
  infrastructure unavailable).
- Provide actionable recovery suggestions.
- Use `sys.exit(N)` for fatal errors per the exit-code contract above.

## Infrastructure Integration Checklist

Before submitting a new or modified script:

- [ ] All analysis lives in `src/pipeline/` or `infrastructure/`, not
  in the script.
- [ ] Uses `logger`, never bare `print()` (except for stdout output paths
  consumed by the pipeline manifest collector).
- [ ] Imports `get_logger` from infrastructure (optionally guarded by
  `try/except ImportError` for environments where it may be absent).
- [ ] Writes output under the documented layout above.
- [ ] Supports `--project-root` for test isolation.
- [ ] Returns/sets the documented exit code.
- [ ] Has a subprocess test in `tests/test_scripts.py`.

## See Also

- [AGENTS.md](AGENTS.md) — full script inventory and API
- [../src/STYLE.md](../src/STYLE.md) — style guide for code scripts import
- [../tests/PATTERNS.md](../tests/PATTERNS.md) — testing patterns including subprocess tests
- [`../../template_code_project/scripts/CONVENTIONS.md`](../../template_code_project/scripts/CONVENTIONS.md) — sibling conventions
