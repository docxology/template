# Source Code Style Guide — template_prose_project

Code style and design conventions for `src/` modules in the
`template_prose_project` exemplar. Sibling of
[`template_code_project/src/STYLE.md`](../../template_code_project/src/STYLE.md);
the same principles apply, but `src/` here is *project-orchestration glue
over `infrastructure/prose/` and `infrastructure/reference/citation/`*,
not its own algorithm.

## What belongs in `src/` vs `infrastructure/`

| Code shape | Belongs in |
|---|---|
| Readability metric (FKGL / FRE / Gunning Fog) implementation | `infrastructure/prose/` |
| BibTeX parsing / `BibDatabase` construction | `infrastructure/reference/citation/` |
| Token-substitution + manuscript-tree write | `infrastructure/rendering/manuscript_injection` |
| **Project-specific threshold checks** (`grade_level_in_band`, etc.) | `src/pipeline.py` (`_check_<name>` functions) |
| **Project-specific report assembly** | `src/report.py` |
| **Project-specific figure renderers** | `src/figures.py` |
| **Project-specific {{TOKEN}} derivation** | `src/manuscript_variables.py` |
| **Project-specific config schema** | `src/config.py` (dataclasses + YAML loader) |

The rule of thumb: if a module under `src/` is doing string-regex over
manuscript prose, computing readability, or parsing BibTeX, that work has
leaked from `infrastructure/`. Move it.

## Pure-by-default

Every function in `src/` should be **side-effect-free unless explicitly
documented otherwise**:

```python
# CORRECT — pure: inputs map to outputs, no I/O
def _check_grade_level(report: ManuscriptReport, lo: float, hi: float) -> CheckResult:
    g = report.avg_flesch_kincaid_grade
    return CheckResult(name="grade_level_in_band", passed=lo <= g <= hi, ...)
```

The intentional exception is `src/pipeline.py::run_prose_pipeline`
itself: it writes JSON + markdown + figures to disk when
`write_outputs=True`. That branch is the documented I/O frontier; every
other function in `src/` stays pure.

## Type Hints

Every public function has complete type annotations:

```python
def run_prose_pipeline(
    config: ProjectConfig,
    project_root: Path,
    *,
    write_outputs: bool = True,
) -> ProseRunArtifacts:
    """Run the prose review pipeline against project_root/<config.manuscript_dir>."""
```

- Use Python 3.10+ union syntax: `Path | None`, not `Optional[Path]`.
- Container fields use the same union syntax:
  `details: dict[str, object] | None = None`.
- Prefer `Path` over `str` for filesystem locations.

## Docstring Format

Google-style with Args/Returns/Raises:

```python
def write_review_report(
    report: ManuscriptReport,
    checks: list[CheckResult],
    output_path: Path,
    *,
    include_per_file_table: bool = True,
    include_outline: bool = True,
    include_quality_flags: bool = True,
) -> Path:
    """Assemble the human-readable review report.

    Args:
        report: Aggregated ManuscriptReport from infrastructure.prose.
        checks: List of CheckResult objects produced by src/pipeline.py.
        output_path: Where the markdown will be written.
        include_per_file_table: Render the per-file metrics table.
        include_outline: Render heading outlines per file.
        include_quality_flags: Render quality-flag summaries (long sentences, hedges).

    Returns:
        Resolved path to the written report.

    Raises:
        FileNotFoundError: If output_path's parent does not exist.
    """
```

## Dataclasses — Mutable for Config, Frozen for Results

Configuration containers are **mutable** because YAML loading populates
them post-construction (`load_project_config` calls `from_dict`):

```python
@dataclass
class ProjectConfig:
    manuscript_dir: Path
    prose: ProseAnalysisConfig
    bibliography: BibliographyConfig
    # mutable so from_dict() can hydrate
```

Result-type containers (substitution payloads, immutable run snapshots)
use `frozen=True`:

```python
@dataclass(frozen=True)
class ManuscriptVariables:
    config_title: str
    total_words: int
    citation_count: int
    # immutable; once computed it does not change
```

Do not freeze configuration containers — the loader path expects to
assign fields post-construction.

## Error Message Format

Every `ValueError` / `FileNotFoundError` includes the actual problematic
value so users can diagnose without reading source:

```python
raise FileNotFoundError(f"manuscript_dir does not exist: {manuscript_dir}")
raise ValueError(
    f"target_grade_level_min ({lo}) must be < target_grade_level_max ({hi})"
)
```

Tests assert on substrings of these messages, so message format is part
of the public contract.

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Public functions | `snake_case` | `run_prose_pipeline` |
| Private checks | `_check_<name>` | `_check_grade_level` |
| Result classes | `PascalCase` + `Result` suffix | `CheckResult` |
| Config classes | `PascalCase` + `Config` suffix | `ProseAnalysisConfig` |
| Frozen result | `PascalCase` + `Variables` suffix | `ManuscriptVariables` |

## Module Exports

`src/__init__.py` exports only what scripts and tests should import:

```python
from .config import ProjectConfig, load_project_config
from .pipeline import CheckResult, ProseRunArtifacts, run_prose_pipeline
from .report import write_review_report
from .figures import generate_all_figures
from .manuscript_variables import (
    compute_variables,
    write_variables,
    write_resolved_manuscript_tree,
)

__all__ = [
    "ProjectConfig",
    "load_project_config",
    "CheckResult",
    "ProseRunArtifacts",
    "run_prose_pipeline",
    "write_review_report",
    "generate_all_figures",
    "compute_variables",
    "write_variables",
    "write_resolved_manuscript_tree",
]
```

Anything not on this list is private API; tests may still touch it via
deep imports, but scripts should not.

## See Also

- [AGENTS.md](AGENTS.md) — full module reference
- [../tests/PATTERNS.md](../tests/PATTERNS.md) — how to test code written under these conventions
- [../scripts/CONVENTIONS.md](../scripts/CONVENTIONS.md) — how scripts use this code
- [../../template_code_project/src/STYLE.md](../../template_code_project/src/STYLE.md) — sibling style guide
