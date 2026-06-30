# docs/ — Agent-Facing Documentation Hub

## Overview

Technical guide for `template_methods_paper/docs/` — the
operational rulebook for AI agents and developers working inside the
`template_methods_paper` exemplar.

## File Inventory

| File | Purpose |
|---|---|
| `README.md` | Quick navigation and audience-targeted entry points |
| `AGENTS.md` | This index — technical overview of `docs/` |
| `agent_instructions.md` | Behavioral constraints for AI agents (read first) |
| `architecture.md` | Thin orchestrator flow: layers, dependencies, forbidden patterns |
| `testing_philosophy.md` | Zero-mock policy; coverage mechanics; test-file inventory |
| `faq.md` | Frequently asked questions about the DSL, testing, manuscript |
| `troubleshooting.md` | Symptom-driven recipes for common failures |
| `quickstart.md` | 5-minute first-run walkthrough |
| `output_conventions.md` | `output/` layout and regeneration |
| `output_inventory.md` | Producer/stage graph for pipeline artifacts |
| `forking_guide.md` | Fork workflow and drift checker |
| `rendering_pipeline.md` | Manuscript → PDF flow; `{{TOKEN}}` controls |
| `style_guide.md` | Code-style rules for the methods-DSL library |
| `syntax_guide.md` | Markdown links, citation syntax, token + figure registry |

## Key Conventions

**Read-first protocol**: read `agent_instructions.md` before modifying any
project file. The most common errors are introducing mocks, putting gate or
compilation logic in scripts, and importing `infrastructure.*` into
`src/methods_dsl/` outside the one declared exception.

**Architecture isolation**: the DSL library in `src/methods_dsl/` is pure
model/validation/compilation logic — no plotting, no file I/O, and (with one
declared exception) no `infrastructure.*` imports. `scripts/` is glue (plots
+ writes files + resolves tokens). The dependency arrow is one-directional:
`scripts/` → `src/`; `tests/` → `src/`. Nothing imports upward. The library
purity is the load-bearing claim: `src/methods_dsl/` can be lifted into any
Python environment with only the standard library installed.

**Zero-mock enforcement**: no `unittest.mock`, `MagicMock`, `@patch`, or
`create_autospec` anywhere in `tests/`. Mock tests can pass even when the
real gate or compiler logic is wrong — they test call signatures, not
results.

## Verification Commands

```bash
# Test suite passes + coverage >= 90%
uv run pytest projects/templates/template_methods_paper/tests \
    --cov=projects/templates/template_methods_paper/src --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" \
    projects/templates/template_methods_paper/tests/ || echo "Clean"

# src/methods_dsl/ has no unsanctioned infrastructure imports
grep -rnE "^(from|import) infrastructure" \
    projects/templates/template_methods_paper/src/methods_dsl/ \
    | grep -v "_logging.py" \
    || echo "Clean — only _logging.py's declared exception imports infrastructure"
```

## REQUIRED vs AESTHETIC

| Path | Status | Enforcing gate / source of truth |
|------|--------|---------------------------------|
| `src/methods_dsl/*.py` | REQUIRED | Coverage gate; the matching `tests/test_*.py` |
| `src/__init__.py` | REQUIRED | Public re-export surface |
| `src/project_paths.py` | REQUIRED | Output dir helpers; `tests/test_project_paths.py` |
| `src/manuscript_variables.py` | REQUIRED | `{{TOKEN}}` generation; `tests/test_manuscript_variables.py` |
| `tests/` (all `test_*.py`) | REQUIRED | 90% coverage gate (per-project and root pipeline) |
| `tests/conftest.py` | REQUIRED | Shared `Method` fixtures + `sys.path` setup |
| `scripts/methods_analysis.py` | REQUIRED | Pipeline analysis entry point; writes exports + reports + figure |
| `scripts/z_generate_manuscript_variables.py` | REQUIRED | Resolves every `{{TOKEN}}` before rendering |
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
- [`../tests/conftest.py`](../tests/conftest.py) — `sys.path` setup and shared fixtures.
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript directory rules.
