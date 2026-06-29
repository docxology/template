# docs/ — Agent-Facing Documentation Hub

## Overview

Technical guide for `projects/templates/template_eda_notebook/docs/` — the
operational rulebook for AI agents and developers working inside the
`template_eda_notebook` exemplar.

## File Inventory

| File | Purpose |
|---|---|
| `README.md` | Quick navigation and audience-targeted entry points |
| `AGENTS.md` | This index — technical overview of `docs/` |
| `agent_instructions.md` | Behavioral constraints for AI agents (read first) |
| `architecture.md` | Thin orchestrator flow: layers, dependencies, forbidden patterns |
| `testing_philosophy.md` | Zero-mock policy; coverage mechanics; class inventory |
| `faq.md` | Frequently asked questions about architecture, testing, manuscripts |
| `troubleshooting.md` | Symptom-driven recipes for common failures |
| `quickstart.md` | 5-minute first-run walkthrough |
| `output_conventions.md` | `output/` layout and regeneration |
| `output_inventory.md` | Producer/stage graph for pipeline artifacts |
| `forking_guide.md` | Fork workflow and drift checker |
| `rendering_pipeline.md` | Manuscript → PDF flow; config.yaml controls |
| `style_guide.md` | Code-style rules for the EDA library |
| `syntax_guide.md` | Markdown links, citation syntax, figure label registry |

## Key Conventions

**Read-first protocol**: read `agent_instructions.md` before modifying any
project file. The most common errors are introducing mocks, putting analysis
logic in notebook cells or scripts, and importing `infrastructure.*` into
`src/eda/`.

**Architecture isolation**: the EDA library in `src/eda/` is pure data logic —
no plotting, no file I/O, and no `infrastructure.*` imports. `scripts/` is glue
(plots + writes files); notebook cells only call the library. The dependency
arrow is one-directional: `scripts/`/`notebooks/` → `src/`; `tests/` → `src/`.
Nothing imports upward. The library purity is the load-bearing claim: `src/eda/`
can be lifted into any Python environment with only numpy and pandas installed.

**Zero-mock enforcement**: no `unittest.mock`, `MagicMock`, `@patch`, or
`create_autospec` anywhere in `tests/`. Mock tests can pass even when the real
computation is wrong — they test call signatures, not results.

## Verification Commands

```bash
# Test suite passes + coverage >= 90%
uv run pytest projects/templates/template_eda_notebook/tests \
    --cov=projects/templates/template_eda_notebook/src --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" \
    projects/templates/template_eda_notebook/tests/ || echo "Clean"

# src/ has no infrastructure imports
grep -rnE "^(from|import) infrastructure" \
    projects/templates/template_eda_notebook/src/ \
    || echo "Clean — the EDA library is infrastructure-free"
```

## REQUIRED vs AESTHETIC

| Path | Status | Enforcing gate / source of truth |
|------|--------|---------------------------------|
| `src/eda/*.py` | REQUIRED | Coverage gate; the matching `tests/test_*.py` |
| `src/__init__.py` | REQUIRED | Public re-export surface; `tests/test_notebook.py` checks the notebook binds to it |
| `src/project_paths.py` | REQUIRED | Output dir helpers; `tests/test_project_paths.py` |
| `data/measurements.csv` | REQUIRED | The dataset the library loads; every statistic derives from it |
| `tests/` (all `test_*.py`) | REQUIRED | 90% coverage gate (per-project and root pipeline) |
| `tests/conftest.py` | REQUIRED | Pins `MPLBACKEND=Agg` + `src/` `sys.path` |
| `scripts/eda_analysis.py` | REQUIRED | Pipeline analysis entry point; writes figures + summary CSV |
| `notebooks/eda_walkthrough.ipynb` | REQUIRED (exemplar) | The archetype this template demonstrates; `tests/test_notebook.py` |
| `manuscript/config.yaml` | REQUIRED | Loaded by `infrastructure.rendering`; pipeline aborts without it |
| `manuscript/*.md` | REQUIRED | Pandoc reads these during the PDF stage |
| `manuscript/references.bib` | REQUIRED | Pandoc citeproc reads it |
| `manuscript/preamble.md` | REQUIRED | Injected at PDF compile |
| `manuscript/SYNTAX.md`, `config.yaml.example`, `AGENTS.md` | AESTHETIC | Authoring/agent guides; pipeline never reads them |
| `docs/*.md` | AESTHETIC | Agent + human documentation |
| `src/STYLE.md`, `tests/PATTERNS.md`, `scripts/CONVENTIONS.md` | AESTHETIC | Per-subdir conventions |
| `pyproject.toml` | REQUIRED | Coverage gate config, pytest options, dependencies |
| `.gitignore` | REQUIRED | Public-repo confidentiality invariant |

"AESTHETIC" does NOT mean throwaway — drift in an aesthetic file silently
misleads future contributors; it just means no pre-commit hook catches it.

## Cross-References

- [`README.md`](README.md) — Quick reference.
- [`../AGENTS.md`](../AGENTS.md) — Project-level documentation.
- [`../pyproject.toml`](../pyproject.toml) — Coverage gate settings.
- [`../tests/conftest.py`](../tests/conftest.py) — `sys.path` setup and `MPLBACKEND=Agg`.
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript directory rules.
