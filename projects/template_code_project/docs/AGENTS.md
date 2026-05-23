# docs/ — Agent-Facing Documentation Hub

## Overview

Technical guide for `projects/template_code_project/docs/` — the operational rulebook for AI agents and developers working inside the `template_code_project` exemplar. Every document in this directory is a hard constraint, not a suggestion.

## File Inventory

| File | Purpose | Lines | Status |
|---|---|---|---|
| `README.md` | Quick navigation and audience-targeted entry points | ~45 | Current |
| `AGENTS.md` | This index — technical overview of `docs/` | ~100 | Current |
| `agent_instructions.md` | Behavioral constraints for AI agents (read-first priority) | ~80 | Comprehensive |
| `architecture.md` | Thin orchestrator flow: layers, dependencies, forbidden patterns, how-to-add-algorithm | ~100 | Comprehensive |
| `testing_philosophy.md` | Zero-mock policy; coverage mechanics; class inventory (live counts in `docs/_generated/canonical_facts.md`) | ~110 | Comprehensive |
| `faq.md` | Frequently asked questions about architecture, testing, manuscripts | ~130 | Comprehensive |
| `troubleshooting.md` | Symptom-driven recipes for common failures | ~170 | Comprehensive |
| `quickstart.md` | 5-minute first-run walkthrough | ~90 | Comprehensive |
| `output_conventions.md` | `output/` directory layout and regeneration | ~120 | Comprehensive |
| `output_inventory.md` | Producer/consumer graph for pipeline artifacts | ~80 | Comprehensive |
| `forking_guide.md` | Fork workflow, drift checker, friction-point table | ~130 | Comprehensive |
| `rendering_pipeline.md` | 4-phase manuscript→PDF flow; config.yaml controls; troubleshooting | ~80 | Comprehensive |
| `style_guide.md` | 7 rules: Zero-Mock, Infrastructure Delegation, Thin Orchestrator, Show-Not-Tell, Explicit Paths, Type Hints, Error Messages | ~120 | Comprehensive |
| `syntax_guide.md` | Markdown links, LaTeX refs, all 28 `{{VARIABLE}}` tokens, figure label registry, adding variables/figures | ~130 | Comprehensive |

## Key Conventions

**Read-first protocol**: AI agents must read `agent_instructions.md` before modifying any project file. Skipping this document is the most common source of errors in this project — agents who skip it tend to: introduce mocks (violating Rule 1), write math in `scripts/` (violating Rule 3), or hardcode numbers in manuscript prose (violating Rule 4 of `style_guide.md`). The consequence of any one violation is a CI failure or a misleading exemplar for future users.

**Architecture isolation**: the **mathematical primitives** in `src/` (`optimizer.py`, `invariants.py`) are pure logic with no `infrastructure.*` imports; the **orchestration modules** (`analysis.py`, `figures.py`, `dashboard.py`, `manuscript_variables.py`) live in `src/` for testability but may import `infrastructure.*` behind try/except fallbacks; `scripts/` is glue (no math); `infrastructure/` is operations (cross-cutting). The dependency arrow remains one-directional: `scripts/` → `src/`; `scripts/` → `infrastructure/`; `tests/` → `src/`. Nothing imports upward. The math-primitive purity is the load-bearing claim: `optimizer.py` and `invariants.py` can be lifted into any Python environment without the pipeline installed.

**Zero-mock enforcement**: No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in `tests/`. CI enforces this via `scripts/verify_no_mocks.py` before the test stage runs. The enforcement exists because mock tests can pass even when the actual mathematical logic is wrong — they test call signatures, not convergence.

**Show-not-tell**: Manuscript references must use explicit file paths and function names, not vague descriptions. A reader of `02_methodology.md` should be able to open `src/optimizer.py` and find the exact function being discussed within 10 seconds. Vague descriptions like "the test suite validates accuracy" cannot be verified or linked.

## Reading Order

This sequence is intentional. Each document provides context that the next document assumes:

1. **`agent_instructions.md`** — Start here. 7 hard rules; consequence of violating each; verification checklist you run before submitting.
2. **`architecture.md`** — Understand layer boundaries before touching any file. Contains the forbidden-patterns table and the 5-step algorithm-addition protocol.
3. **`testing_philosophy.md`** — Understand the zero-mock constraint and test class inventory before writing or modifying any test. Contains the coverage run command.
4. **`rendering_pipeline.md`** — Understand the 4-phase pipeline before editing manuscript or output paths. Contains all config.yaml controls and troubleshooting steps.
5. **`style_guide.md`** — Understand the 7 style rules before writing any source code. Rules 1–3 govern code; Rules 4–5 govern documentation; Rules 6–7 govern type hints and error messages.
6. **`syntax_guide.md`** — Understand the complete `{{VARIABLE}}` token list and figure label registry before editing any manuscript `.md` file.

## Verification Commands

These three commands verify the most critical constraints. Run all three before submitting any change:

```bash
# Test suite passes + coverage ≥90%
uv run pytest projects/template_code_project/tests/ \
    --cov=projects/template_code_project/src \
    --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" \
    projects/template_code_project/tests/ || echo "Clean"

# Mathematical primitives (optimizer.py, invariants.py) have no infrastructure imports
# (orchestration modules analysis.py / dashboard.py / manuscript_variables.py are allowed
# to import infrastructure behind try/except fallbacks — see src/AGENTS.md).
grep -nE "^(from|import) infrastructure" \
    projects/template_code_project/src/optimizer.py \
    projects/template_code_project/src/invariants.py \
    || echo "Clean — math primitives are infrastructure-free"
```

## REQUIRED vs AESTHETIC

A forker copying this exemplar should know which directories and files
are pipeline-enforced (delete them and the gate fails) and which are
convention only (delete them and nothing complains automatically). The
distinction matters when you trim the template down to your minimum
viable project.

| Path | Status | Enforcing gate / source of truth |
|------|--------|---------------------------------|
| `src/optimizer.py` | REQUIRED | Coverage gate; `tests/test_optimizer.py` |
| `src/invariants.py` | REQUIRED | `tests/test_invariants.py` + dashboard invariants check |
| `src/experiment_config.py` | REQUIRED | `load_experiment_config()`; shared by analysis, figures, dashboard, manuscript_variables; `tests/test_experiment_config.py` |
| `src/analysis.py` | REQUIRED (orchestration) | Exercised by `scripts/optimization_analysis.py`; `tests/test_analysis_integration.py`, `tests/test_analysis_coverage.py` |
| `src/figures.py` | REQUIRED (orchestration) | Six `generate_*` plot functions; `tests/test_figures_orchestration.py` + stability/benchmark viz in `tests/test_analysis_integration.py` |
| `src/dashboard.py` | REQUIRED (orchestration) | Exercised by `scripts/build_dashboard.py`; `tests/test_invariants_and_dashboard.py`, `tests/test_dashboard_config.py` |
| `src/manuscript_variables.py` | REQUIRED | `tests/test_manuscript_variables.py` + live `{{TOKEN}}` cross-reference; reads config via `load_experiment_config()` |
| `tests/` (all `test_*.py`) | REQUIRED | 90% coverage gate (per-project and root pipeline) |
| `tests/conftest.py` | REQUIRED | Pins `MPLBACKEND=Agg` + `src/` `sys.path`; without it pytest cannot collect |
| `scripts/optimization_analysis.py` | REQUIRED | Pipeline stage 4 entry point; PDF stage depends on its outputs |
| `scripts/z_generate_manuscript_variables.py` | REQUIRED | Hydrates `{{TOKEN}}`s; PDF stage reads `output/manuscript/*.md` it writes |
| `scripts/build_dashboard.py` | REQUIRED | Pipeline reads `output/web/dashboard.html` |
| `scripts/generate_api_docs.py` | AESTHETIC | Auxiliary docs generator; smoke-tested by `tests/test_scripts_smoke.py`; pipeline does not consume its output |
| `scripts/00_preflight.py` | AESTHETIC | Emits a warning before PDF render; smoke-tested by `tests/test_scripts_smoke.py`; pipeline still runs without it |
| `tests/test_scripts_smoke.py` | AESTHETIC | Subprocess smoke for auxiliary scripts (`generate_api_docs.py`, `00_preflight.py`) |
| `manuscript/config.yaml` | REQUIRED | Loaded by `infrastructure.rendering.pdf_renderer`; pipeline aborts without it |
| `manuscript/*.md` | REQUIRED | Pandoc reads token-substituted copies during PDF stage |
| `manuscript/references.bib` | REQUIRED | Pandoc citeproc reads it during PDF stage |
| `manuscript/preamble.md` | REQUIRED | Injected at PDF compile; missing → LaTeX errors |
| `manuscript/SYNTAX.md` | AESTHETIC | Authoring guide for humans; pipeline never reads it |
| `manuscript/config.yaml.example` | AESTHETIC | Documentation; forkers copy → `config.yaml` |
| `manuscript/AGENTS.md` | AESTHETIC | Agent guide; pipeline never reads it |
| `docs/*.md` | AESTHETIC | Agent + human documentation; no gate parses these |
| `src/STYLE.md`, `tests/PATTERNS.md`, `scripts/CONVENTIONS.md` | AESTHETIC | Per-subdir style/test/script conventions |
| `src/AGENTS.md`, `tests/AGENTS.md`, `scripts/AGENTS.md` | AESTHETIC | Per-subdir agent guides |
| `docs/output_inventory.md` | AESTHETIC | Producer/consumer graph for `output/`; lives in `docs/` because the repo `.gitignore` excludes `output/` |
| `pyproject.toml` | REQUIRED | Coverage gate config, pytest options, dependency declarations |
| `.gitignore` | REQUIRED | Public-repo confidentiality invariant (see root `CLAUDE.md`) |
| `README.md`, `AGENTS.md` (root) | AESTHETIC (load-bearing for humans/agents) | Read by every newcomer; drift = a confused forker |

"AESTHETIC" does NOT mean "throwaway" — drift in an aesthetic file
typically rots over months and silently misleads future contributors. It
means "no pre-commit hook will tell you when it rots." Treat the
AESTHETIC list as the audit surface that lives outside automated CI.

## Cross-References

- [`README.md`](README.md) — Quick reference with audience-targeted entry points
- [`../AGENTS.md`](../AGENTS.md) — Project-level documentation (API reference, known issues, full directory map)
- [`../pyproject.toml`](../pyproject.toml) — Coverage gate settings (`fail_under = 90`, `branch = true`)
- [`../tests/conftest.py`](../tests/conftest.py) — `sys.path` setup and `MPLBACKEND=Agg`
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript directory: `{{VARIABLE}}` protocol, figure list, workflow
- [`../../../AGENTS.md`](../../../AGENTS.md) — Root template documentation (infrastructure module reference)
