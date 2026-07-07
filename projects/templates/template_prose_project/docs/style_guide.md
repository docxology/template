# Style Guide

This document defines the coding and communication style for the
`template_prose_project` exemplar. Every rule has a concrete consequence for
test correctness, reproducibility, or manuscript accuracy.

---

## 1. Zero-Mock Policy

The most critical style rule is the absolute prohibition of mocking. The
following are **forbidden** anywhere inside
`projects/templates/template_prose_project/tests/`:

- `import unittest.mock`
- `from unittest.mock import MagicMock, patch, create_autospec, Mock, AsyncMock`
- `@patch(...)` decorators
- `monkeypatch.setattr(...)` when used to substitute a real function with a
  fake callable

**Why**: every function under `src/` is either pure (config parsing,
figure rendering, variable derivation, report assembly) or a thin orchestration
shell over `infrastructure/prose/` and `infrastructure/reference/citation/`,
both of which are themselves pure. Tests can always pass real Markdown,
real BibTeX, and real `tmp_path` directories — there is nothing legitimate
to mock.

**Forbidden pattern**:
```python
# BAD — tests call behavior, not real analysis output
from unittest.mock import MagicMock
mock_report = MagicMock()
mock_report.aggregate.metrics.flesch_kincaid_grade = 12.0
result = _check_grade_level(mock_report, config)
assert result.passed
```

**Correct pattern** (from `tests/test_pipeline.py`):
```python
# GOOD — uses a real ManuscriptReport produced by infrastructure.prose
manuscript_dir = tmp_path / "manuscript"
manuscript_dir.mkdir()
(manuscript_dir / "01_intro.md").write_text("# Intro\n\nReal prose here.\n")
report = analyze_manuscript(manuscript_dir)
result = _check_grade_level(report, config)
assert isinstance(result, CheckResult)
```

**Verify cleanliness**:
```bash
grep -r "unittest.mock\|MagicMock\|@patch" projects/templates/template_prose_project/tests/ \
    || echo "Clean"
```

The current repository state passes this check with no matches.

---

## 2. Infrastructure Delegation

Project code must delegate the operational work — reading the manuscript,
computing readability, parsing BibTeX — to `infrastructure/`. The rule the
suite actually enforces is "**no module under `src/` re-implements analysis
that already exists in `infrastructure/`**". Modules may import infrastructure
types, pure helpers, and operations as needed; logic must stay in
`infrastructure/`, not be inlined under `src/`.

| File | May import from infrastructure | Must NOT do |
|---|---|---|
| `src/config.py` | (does not currently import infrastructure) | re-implement YAML parsing or schema validation |
| `src/pipeline/` | `infrastructure.prose.{ManuscriptReport, analyze_manuscript, write_report}`, `infrastructure.reference.citation.parse_bibfile` | I/O outside the documented `write_outputs=True` branch |
| `src/figures.py` | `infrastructure.prose.ManuscriptReport` (top-level type only) | re-implement readability/structure analysis; plot over a typed report, never recompute metrics |
| `src/report.py` | `src.prose_facade.{ManuscriptReportLike, render_outline}` (project-owned Protocol + pure helper, no infrastructure import) | `analyze_*`, `parse_*`, `write_*` |
| `src/prose_facade.py` | (does not import infrastructure — project-owned report Protocols plus `render_outline`/`parse_bib_keys`, deliberately decoupled from `infrastructure.prose`/`infrastructure.reference`) | call into `infrastructure.*`; re-implement `infrastructure.reference.citation.parse_bibfile` (its `parse_bib_keys` is a deliberately minimal cross-check helper, not a replacement) |
| `src/manuscript_variables.py` | `load_report_payload` (raw JSON dict) and `infrastructure.rendering.manuscript_injection.{substitute_manuscript_text, write_resolved_manuscript_tree}` for the {{TOKEN}} substitution path | re-implement substitution; reads JSON written by `pipeline/`, delegates writes to infrastructure |
| `scripts/y_generate_prose_figures.py` | `infrastructure.prose.report.load_report_json` → typed `ManuscriptReport` for `src/figures.py` | inline analysis logic |
| `scripts/run_prose_pipeline.py` | `src.pipeline`, `src.config`, `src.report` | inline analysis logic, regex over prose, BibTeX parsing |
| `scripts/z_generate_manuscript_variables.py` | `src.manuscript_variables` (`load_report_payload`) | inline analysis logic |
| `tests/test_*.py` | `src.*`, `infrastructure.*` (real) | `unittest.mock.*` |

**Verify the boundary** (no analysis re-implemented under `src/`):
```bash
# Operations originate from src/pipeline/ and src/manuscript_variables.py only;
# figures.py loads infrastructure types from JSON but does not call analyze_*/parse_*/write_*.
grep -nE "analyze_manuscript|parse_bibfile|write_report" \
    projects/templates/template_prose_project/src/figures.py \
    projects/templates/template_prose_project/src/report.py \
    projects/templates/template_prose_project/src/config.py \
    || echo "Clean — figures/report/config call no analysis operations"
```

---

## 3. The Thin Orchestrator Pattern

Files in `scripts/` must be CLI shims: argparse, logging, and a single call
into `src/`. They must not re-implement check evaluation, figure rendering,
or variable derivation that already exists in `src/`.

**Forbidden** — re-implementing a check inside a script:
```python
# BAD — check evaluation belongs in src/pipeline/, not in run_prose_pipeline.py
from infrastructure.prose import analyze_manuscript

def main():
    report = analyze_manuscript(Path("manuscript"))
    if report.aggregate.metrics.flesch_kincaid_grade > 18:   # BAD
        sys.exit(1)
```

**Correct** — `scripts/` calls `src/` for the orchestration:
```python
# GOOD — load config, run pipeline, surface artefacts
from projects.template_prose_project.src.config import load_project_config
from projects.template_prose_project.src.pipeline import run_prose_pipeline

def main():
    config = load_project_config(Path("projects/templates/template_prose_project/manuscript/config.yaml"))
    artifacts = run_prose_pipeline(config, project_root=Path("projects/templates/template_prose_project"))
    if args.strict and any(not c.passed for c in artifacts.checks):
        sys.exit(1)
```

**Decision rule**: if a line of code in `scripts/` evaluates a manuscript
property (heading hierarchy, citation density, FKGL band), move that logic
to a `_check_<name>` function in `src/pipeline/checks.py` and write a test for it.

---

## 4. Manuscript "Show, Not Tell"

When editing manuscript markdown (e.g., `02_methodology.md`), use explicit,
verifiable file paths instead of vague descriptions. Reviewers and future
agents must be able to find the referenced code.

**Forbidden (vague)**:
```markdown
Our pipeline computes readability and validates citations automatically.
```

**Correct (concrete, anchored to `src/pipeline/`)**:
```markdown
`projects/templates/template_prose_project/src/pipeline/__init__.py::run_prose_pipeline` computes
readability via `infrastructure.prose.analyze_manuscript` and validates
citation keys against `manuscript/references.bib` parsed by
`infrastructure.reference.citation.parse_bibfile`. The thresholds applied
to the resulting metrics are read from `manuscript/config.yaml`
(`prose.target_grade_level_min`, `prose.target_grade_level_max`,
`prose.citation_density_min_per_1000`, …).
```

Two additional BAD/GOOD pairs:

| BAD (vague) | GOOD (concrete) |
|---|---|
| "The manuscript reads at a college level." | "The manuscript's weighted Flesch-Kincaid Grade Level is `{{AVG_GRADE_LEVEL}}`, falling inside the configured band `[prose.target_grade_level_min, prose.target_grade_level_max]` defined in `manuscript/config.yaml`." |
| "We validated the bibliography." | "`_check_bibliography` in `src/pipeline/checks.py` confirmed that all `{{CITATION_COUNT}}` cited keys appear in `manuscript/references.bib`; the `bibliography_consistency` entry of `output/checks.json` records `passed: true`." |

---

## 5. Explicit Absolute File Paths

When AI agents or humans refer to files in logs, documentation, comments, or
implementation plans, always use the path relative to the **repository root**
(`template/`). This prevents ambiguity when the same filename appears in
multiple sibling exemplars.

**Repository-root anchors** for this project:

| Short Name | Absolute Path (from repo root) |
|---|---|
| pipeline orchestrator | `projects/templates/template_prose_project/src/pipeline/` |
| config loader | `projects/templates/template_prose_project/src/config.py` |
| figures module | `projects/templates/template_prose_project/src/figures.py` |
| variables module | `projects/templates/template_prose_project/src/manuscript_variables.py` |
| report module | `projects/templates/template_prose_project/src/report.py` |
| pipeline test | `projects/templates/template_prose_project/tests/test_pipeline.py` |
| integration test | `projects/templates/template_prose_project/tests/test_pipeline_integration.py` |
| script test | `projects/templates/template_prose_project/tests/test_scripts.py` |
| conftest | `projects/templates/template_prose_project/tests/conftest.py` |
| run-pipeline script | `projects/templates/template_prose_project/scripts/run_prose_pipeline.py` |
| figure script | `projects/templates/template_prose_project/scripts/y_generate_prose_figures.py` |
| variables script | `projects/templates/template_prose_project/scripts/z_generate_manuscript_variables.py` |
| config | `projects/templates/template_prose_project/manuscript/config.yaml` |
| references | `projects/templates/template_prose_project/manuscript/references.bib` |
| review report | `projects/templates/template_prose_project/output/review_report.md` |
| working PDF | `projects/templates/template_prose_project/output/pdf/template_prose_project_combined.pdf` |
| promoted PDF | `output/template_prose_project/template_prose_project_combined.pdf` |

**Forbidden (relative / ambiguous)**:
```
pipeline.py        # Which pipeline? Which project?
output/figures/    # Relative to what?
../src/pipeline    # Only valid from one directory
```

**Correct (absolute from repo root)**:
```
projects/templates/template_prose_project/src/pipeline/
projects/templates/template_prose_project/output/figures/section_word_counts.png
```

---

## 6. Dataclass and Type Hint Standards

Follow the patterns established in `src/config.py` and `src/pipeline/`:

- Use Python 3.10+ union syntax: `Path | None`, not `Optional[Path]`.
- Configuration dataclasses (`ProseAnalysisConfig`, `BibliographyConfig`, `ReportConfig`, `ProjectConfig`) are **mutable** because YAML parsing populates them after construction. `ManuscriptVariables` is `frozen=True` because it represents a fully-resolved substitution payload. The rule of thumb: freeze immutable result-types; leave config containers mutable.
- All public functions must have complete type annotations on every
  parameter and the return value.
- Container fields use the same union syntax: `details: dict[str, object] | None = None`.

**Example** (mirroring `ManuscriptVariables` in `src/manuscript_variables.py`):

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class ManuscriptVariables:
    files_analysed: int
    total_words: int
    avg_grade_level: float
    # ... immutable result type, so frozen=True is correct here.
```

For a mutable config container (matching `ProjectConfig` in `src/config.py`):

```python
@dataclass
class ProjectConfig:
    manuscript_dir: Path
    prose: ProseAnalysisConfig
    bibliography: BibliographyConfig
    # Mutable so from_dict() / loader hooks can populate fields post-construction.
```

---

## 7. Error Message Format

All `ValueError`, `TypeError`, and `FileNotFoundError` raises must include
the actual problematic value so users can diagnose the issue without reading
source code.

**Forbidden (no diagnostic value)**:
```python
raise ValueError("Config invalid")
raise FileNotFoundError("File not found")
```

**Correct** (following the pattern in `src/config.py` and `src/pipeline/`):
```python
raise FileNotFoundError(f"manuscript_dir does not exist: {manuscript_dir}")
raise ValueError(
    f"target_grade_level_min ({lo}) must be < target_grade_level_max ({hi})"
)
raise ValueError(
    f"references_path is set but file is missing: {bib_path}"
)
```

The format `f"<what was expected>: <what was actually received>"` is the
default. Tests assert on substrings of these messages
(`tests/test_config.py`, `tests/test_pipeline.py`), so message stability is
part of the public contract.
