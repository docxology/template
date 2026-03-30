# One-shot LLM prompt: new `projects/{name}/`

Use this prompt when you want a model to scaffold a full project in one pass. Anchor layout and conventions on the control-positive exemplar [`projects/code_project/`](../../projects/code_project/).

**Checklist and pitfalls:** [new-project-setup.md](new-project-setup.md)

**Other active workspaces** (alternate packaging or manuscript depth) live under `projects/`; names are listed in [_generated/active_projects.md](../_generated/active_projects.md). Do not copy that list into this prompt—inspect those trees in the repo if you need a second reference.

## Positive control (read or attach in your IDE)

| Control | Path | Role |
| -------- | ----- | ----- |
| A | [projects/code_project](../../projects/code_project/) | Flat `src/` modules, `scripts/` orchestrators, standard manuscript sections, reproducible figures/data, `tests/` layout |

## Prompt (copy from below into your assistant)

```text
You are working inside the docxology/template monorepo. Create a new active project at projects/<PROJECT_SLUG>/ that matches the same shape and discipline as the control-positive exemplar projects/code_project/: flat src/ modules, analysis scripts as thin orchestrators, standard manuscript sectioning, reproducible figures/data, tests/ with conftest path and MPLBACKEND=Agg if using matplotlib, ≥90% coverage on projects/<PROJECT_SLUG>/src, no mocks.

Required layout (must exist):

projects/<PROJECT_SLUG>/
├── pyproject.toml          # name, python version, deps, pytest + coverage for src
├── src/
│   └── __init__.py         # and real module(s) implementing domain logic
└── tests/
    ├── __init__.py
    └── test_*.py           # ≥90% coverage on projects/<PROJECT_SLUG>/src; no mocks

Strongly recommended (match the exemplar):

- scripts/ — thin orchestrators only: import from src, write outputs under projects/<PROJECT_SLUG>/output/, print paths for manifests where applicable.
- manuscript/ — config.yaml, preamble.md, references.bib, ordered *.md sections.
- docs/ — small hub (architecture, testing notes) if non-obvious.
- Root AGENTS.md for the project + README.md where helpful; subdirectory AGENTS.md/README.md only where the exemplar does.

Rules:

1. No unittest.mock, MagicMock, or pytest monkeypatch of domain code — use real data, temp files, subprocess, or pytest-httpserver for HTTP.
2. Coverage: configure tool.coverage.run and fail_under in pyproject.toml like the exemplar; exercise all new src lines.
3. Imports: use from src... in scripts/tests as in code_project; infrastructure imports allowed; never import another projects/* package.
4. Determinism: fixed RNG seeds for anything stochastic; headless plotting (MPLBACKEND=Agg) where relevant.
5. Naming: <PROJECT_SLUG> is lowercase snake_case; package name in pyproject.toml aligns with repo conventions.

One-shot deliverables (do all in one pass):

1. Full directory tree and files for projects/<PROJECT_SLUG>/ as above.
2. Minimal but real domain implementation in src/ (not stubs), with typed public APIs and logging via infrastructure.core.logging.logging_utils.get_logger where appropriate.
3. Tests that prove core behavior and meet coverage.
4. At least one scripts/*.py orchestrator if the manuscript or pipeline expects figures/data (optional if the idea is purely non-computational — state that explicitly in the manuscript and skip scripts).
5. Manuscript markdown + config.yaml metadata (title, authors placeholder OK) coherent with the code and tests.
6. Short note in project README.md: how to run uv run pytest projects/<PROJECT_SLUG>/tests/ --cov=projects/<PROJECT_SLUG>/src --cov-fail-under=90 and how python3 scripts/01_run_tests.py --project <PROJECT_SLUG> applies.

Project idea — append only below this line (do not edit text above):

<PASTE THE CONTRIBUTOR'S PROJECT IDEA HERE: 1–3 sentences on topic, intended claims/artifacts, and any constraints.>
```

## After pasting

1. Replace `<PROJECT_SLUG>` in the opening instruction if you already chose a name, or leave it and let the model propose one.
2. Append the contributor’s idea in the last line only.
3. Run the checklist in [new-project-setup.md](new-project-setup.md) before relying on the full pipeline (root venv deps, matplotlib in core deps if needed, and so on).
