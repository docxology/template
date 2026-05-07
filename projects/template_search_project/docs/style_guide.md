# Style Guide

This document defines the coding and communication style for the `search_project` exemplar. Every rule below has a concrete consequence for test correctness, reproducibility, or manuscript accuracy.

---

## 1. Zero-Mock Policy (and the LLM-as-Callable Corollary)

The most critical style rule is the absolute prohibition of mocking. The following are **forbidden** anywhere inside `projects/template_search_project/tests/`:

- `import unittest.mock`
- `from unittest.mock import MagicMock, patch, create_autospec, Mock, AsyncMock`
- `@patch(...)` decorators
- `monkeypatch.setattr(...)` when used to substitute a real function with a fake callable

**Why this is achievable here**: the modules in `src/` that touch external systems do so through a small, well-defined surface — `infrastructure.search.literature.LiteratureClient`, `AbstractFetcher`, `FulltextFetcher`, and a duck-typed `llm: Callable[[str], str]` argument in `src/synthesis.py`. Tests substitute the search backend with `infrastructure.search.literature.LocalBackend` against a temp-dir corpus, and substitute the LLM with a deterministic local function.

**LLM corollary**: `src/synthesis.py::synthesise_per_paper` and `synthesise_corpus` accept `llm` as a positional callable. Tests pass a function; never a mock.

**Forbidden pattern**:
```python
# BAD — tests behaviour, not output
from unittest.mock import MagicMock
fake_llm = MagicMock(return_value="canned response")
result = synthesise_per_paper(paper, "key2024", llm=fake_llm)
assert fake_llm.call_count == 1
```

**Correct pattern** (from `tests/test_synthesis.py`):
```python
# GOOD — test the real prompt assembly + callable contract
def deterministic_llm(prompt: str) -> str:
    return f"CONTRIBUTION: stub for {prompt[:40]}"

result = synthesise_per_paper(paper, "key2024", llm=deterministic_llm)
assert result.kind == "per_paper"
assert "CONTRIBUTION:" in result.text
```

**Verify cleanliness**:
```bash
grep -rE "unittest\.mock|MagicMock|@patch" projects/template_search_project/tests/ || echo "Clean"
```

---

## 2. Infrastructure Delegation

Project code delegates cross-cutting concerns to `infrastructure/`. Unlike `template_code_project`, the search exemplar's `src/` does import from `infrastructure/`, but only along a narrow, documented surface.

| File | May Import | Must NOT Import |
|---|---|---|
| `src/config.py` | `dataclasses`, `pathlib`, `yaml`, stdlib `typing` | Anything from `infrastructure.*` |
| `src/pipeline.py` | `infrastructure.search.literature`, `infrastructure.reference.citation` | `infrastructure.llm.*`, `infrastructure.rendering.*`, `infrastructure.reporting.*` |
| `src/deep_search.py` | `infrastructure.search.literature`, `infrastructure.reference.citation` | Same as above |
| `src/synthesis.py` | `infrastructure.search.literature` (for `Paper`) | `infrastructure.llm.*` directly — receives a callable |
| `src/llm_runtime.py` | `infrastructure.llm` | `infrastructure.search.*`, `infrastructure.reference.*` |
| `src/figures.py` | `matplotlib`, `numpy` | `infrastructure.*` |
| `src/manuscript_variables.py` | stdlib only | `infrastructure.*` |
| `src/report.py` | `infrastructure.search.literature` (for `Paper`) | Anything that writes files itself outside the function's `output_path` arg |
| `src/analysis.py` | stdlib only (`re`, `pathlib`, `subprocess`) | `infrastructure.*` |
| `src/search_invariants.py` | stdlib only | `infrastructure.*` |
| `src/dotenv.py` | stdlib only | Anything else |
| `scripts/run_search_pipeline.py` | `src/*`, `infrastructure.search.*`, `infrastructure.reference.*`, `infrastructure.llm` (via `src/llm_runtime`) | Re-implementing pipeline logic |
| `scripts/run_deep_search.py` | `src/deep_search`, `src/config`, `src/llm_runtime`, `infrastructure.search.*` | Same as above |
| `scripts/s_compose_literature_review.py` | `src/*`, `infrastructure.reference.citation` | Search backends |
| `tests/test_*.py` | `src/*`, `infrastructure.search.literature.LocalBackend` (only) | `unittest.mock.*` in any form |

**Verify the boundary**:
```bash
# src/ never imports from rendering / reporting / scientific
grep -rE "from infrastructure\.(rendering|reporting|scientific)" \
    projects/template_search_project/src/ || echo "Clean"
```

---

## 3. The Thin-Orchestrator Pattern

Files in `scripts/` are **thin orchestrators**: they parse CLI flags, load configuration, call a single `src/` entry point, and write to `output/`. They do not re-implement search, deduplication, BibTeX serialisation, or LLM prompt assembly.

**Forbidden** — search loop re-implemented in `scripts/`:
```python
# BAD — pagination + dedup belongs in src/pipeline.py
for source in sources:
    for paper in client.search_one(source, query):
        if paper.id not in seen:
            seen.add(paper.id)
            papers.append(paper)
```

**Correct** — `scripts/` calls `src/`:
```python
# GOOD
from src.pipeline import run_literature_pipeline
artifacts = run_literature_pipeline(config, project_root=project_root)
```

### Alphabetical script-order convention

The infrastructure pipeline runner discovers `scripts/*.py` in lexical order. The project relies on this:

| Order | Script | Purpose |
|---|---|---|
| 1 | `scripts/run_deep_search.py` | Multi-keyword fan-out; writes `manuscript/references_deep.bib` |
| 2 | `scripts/run_search_pipeline.py` | Single-query pipeline; writes `manuscript/references.bib` |
| 3 | `scripts/s_compose_literature_review.py` | Composes `manuscript/S01_literature_review.md` from deep-search outputs |
| 4 | `scripts/y_generate_search_figures.py` | Writes the three diagnostic PNGs |
| 5 | `scripts/z_generate_manuscript_variables.py` | Resolves `{{TOKEN}}` markers; copies `*.md` + `*.bib` to `output/manuscript/` |
| 6 | `scripts/zz_generate_review_report.py` | Aggregates review-stage outputs |
| 7 | `scripts/zzz_build_dashboard.py` | Reads `output/corpus.json` + `output/deep_search/aggregate.json`; writes the interactive HTML dashboard last |

`run` < `s` < `y` < `z` < `zz` < `zzz` is **load-bearing**: the composer must run before the resolver so the freshly written `S01_literature_review.md` is in `manuscript/` when `z_generate_manuscript_variables.py` mirrors it into `output/manuscript/`, and the dashboard must run last so its corpus / aggregate inputs already exist. `tests/test_script_order.py` codifies this.

`scripts/review` is out-of-band — it is a CLI executable, not a `*.py` file, and is invoked by `zz_generate_review_report.py`.

---

## 4. Manuscript "Show, Not Tell"

When editing `manuscript/*.md`, refer to concrete file paths and APIs.

**Forbidden (vague)**:
```markdown
The pipeline retrieves papers from major literature sources and stores them.
```

**Correct (concrete, from `02_methodology.md`)**:
```markdown
`src/pipeline.py::run_literature_pipeline` queries the backends listed in
`config.search.sources` (default `{{CONFIG_SOURCES}}`) via
`infrastructure.search.literature.LiteratureClient`, deduplicates on `paper.id`,
and writes `{{RESULT_NUM_PAPERS}}` entries to `manuscript/references.bib`
through `infrastructure.reference.citation.paper_to_bibentry`.
```

Two further BAD/GOOD pairs:

| BAD (vague) | GOOD (concrete) |
|---|---|
| "We searched a few hundred papers." | "The standard pipeline retrieved `{{RESULT_NUM_PAPERS}}` papers across `{{RESULT_NUM_SOURCES}}` sources (`{{RESULT_PER_SOURCE}}`)." |
| "An LLM summarises each paper." | "`src/synthesis.py::synthesise_per_paper` runs each enriched paper through the callable returned by `src/llm_runtime.py::build_llm_callable`, writing the response to `output/llm/per_paper/<safe_id>.md`." |

---

## 5. Explicit Absolute File Paths

When AI agents or humans refer to files in logs, documentation, comments, or implementation plans, always use the path relative to the **repository root** (`template/`).

**Repository-root anchors** for this project:

| Short Name | Absolute Path (from repo root) |
|---|---|
| project config | `projects/template_search_project/manuscript/config.yaml` |
| typed config | `projects/template_search_project/src/config.py` |
| standard pipeline | `projects/template_search_project/src/pipeline.py` |
| deep search | `projects/template_search_project/src/deep_search.py` |
| synthesis | `projects/template_search_project/src/synthesis.py` |
| LLM runtime | `projects/template_search_project/src/llm_runtime.py` |
| variables | `projects/template_search_project/src/manuscript_variables.py` |
| review helpers | `projects/template_search_project/src/analysis.py` |
| offline corpus | `projects/template_search_project/data/corpus.json` |
| run script | `projects/template_search_project/scripts/run_search_pipeline.py` |
| deep run script | `projects/template_search_project/scripts/run_deep_search.py` |
| composer | `projects/template_search_project/scripts/s_compose_literature_review.py` |
| review CLI | `projects/template_search_project/scripts/review` |
| standard BibTeX | `projects/template_search_project/manuscript/references.bib` |
| deep BibTeX | `projects/template_search_project/manuscript/references_deep.bib` |
| working PDF | `projects/template_search_project/output/pdf/template_search_project_combined.pdf` |
| promoted PDF | `output/template_search_project/template_search_project_combined.pdf` |

---

## 6. Dataclass and Type Hint Standards

Follow the patterns established in `src/config.py` and `src/manuscript_variables.py`:

- Use Python 3.10+ union syntax: `int | None`, `list[str]`, `dict[str, object]`.
- Mark immutable record types with `@dataclass(frozen=True)` (see `ManuscriptVariables`).
- Mutable configuration types use `@dataclass` with `field(default_factory=...)` for list/dict defaults (see `SearchConfig`, `DeepSearchConfig`).
- Aggregate run outputs in a single dataclass returned by the orchestration entry point. The conventional names are:
  - `LiteratureRunArtifacts` — returned by `src/pipeline.py::run_literature_pipeline`
  - `DeepSearchArtifacts` — returned by `src/deep_search.py::run_deep_search`
  - `SearchCache` (from infrastructure) — keyed on canonical query identity; re-runs hit the cache without code changes

**Example** (following `ManuscriptVariables` in `src/manuscript_variables.py`):
```python
@dataclass(frozen=True)
class NewArtifacts:
    output_path: Path
    paper_count: int
    citation_keys: dict[str, str]
    errors: dict[str, str]
```

---

## 7. Error Message Format

All `ValueError` and `TypeError` raises must include the actual problematic value so callers can diagnose without reading source code.

**Forbidden (no diagnostic value)**:
```python
raise ValueError("Bad config")
raise ValueError("Missing field")
```

**Correct** (following the patterns in `src/config.py` and `src/pipeline.py`):
```python
raise ValueError("ProjectConfig.search.query must be non-empty")
raise ValueError(f"Config {path} must be a YAML mapping at the top level")
raise ValueError(f"local_corpus required when sources={sources!r} contains 'local'")
raise FileNotFoundError(f"corpus path does not exist: {path}")
```

The error must name (a) the field or argument, (b) the constraint it violates, and (c) the offending value when one is available.
