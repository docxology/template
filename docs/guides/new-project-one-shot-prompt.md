# One-shot LLM prompt: new `projects/{name}/`

Use this prompt when you want a model to scaffold a full project in one pass. Attach or reference the positive controls so layout and conventions stay aligned with the repo.

**Checklist and pitfalls:** [new-project-setup.md](new-project-setup.md)

## Positive controls (read or attach in your IDE)

| Control | Path | Use when |
| -------- | ----- | -------- |
| A | [projects/code_project](../../projects/code_project/) | Flat `src/` modules, analysis `scripts/`, shorter manuscript arc, figures and reproducible outputs |
| B | [projects/template](../../projects/template/) | Package under `src/<slug>/`, long multi-section manuscript, script-driven metrics or visualization |
| C | [projects/area_handbook](../../projects/area_handbook/) | Flat `src/` as importable `src` package, YAML fixture corpus, synthesis-to-handbook narrative, coverage figure |

## Prompt (copy from below into your assistant)

```text
You are working inside the docxology/template monorepo. Create a new active project at projects/<PROJECT_SLUG>/ that matches the same shape and discipline as the positive controls:

- projects/code_project — reference for flat src/ modules, analysis scripts, standard manuscript sectioning, reproducible figures/data, and tests/ layout (conftest.py path and MPLBACKEND=Agg if using matplotlib).
- projects/template — reference when the domain needs a named Python package under src/<PROJECT_SLUG>/, multi-chapter manuscripts, and script-orchestrated metrics or visualization with zero domain logic in scripts/.
- projects/area_handbook — reference for a committed YAML/JSON corpus, section coverage synthesis, gap lists, and handbook-style multi-section prose with `from src.*` imports in scripts (prepend `PROJECT_DIR` to `sys.path`).

Required layout (must exist):

projects/<PROJECT_SLUG>/
├── pyproject.toml          # name, python version, deps, pytest + coverage for src
├── src/
│   └── __init__.py         # and real module(s) implementing domain logic
└── tests/
    ├── __init__.py
    └── test_*.py           # ≥90% coverage on projects/<PROJECT_SLUG>/src; no mocks

Strongly recommended (match the exemplars):

- scripts/ — thin orchestrators only: import from src or src.<package>, write outputs under projects/<PROJECT_SLUG>/output/, print paths for manifests where applicable.
- manuscript/ — config.yaml, preamble.md, references.bib, ordered *.md sections consistent with scope (short paper like code_project vs long form like template).
- docs/ — small hub (architecture, testing notes) if non-obvious.
- Root AGENTS.md for the project + README.md where helpful; subdirectory AGENTS.md/README.md only where the exemplars do.

Rules:

1. No unittest.mock, MagicMock, or pytest monkeypatch of domain code — use real data, temp files, subprocess, or pytest-httpserver for HTTP.
2. Coverage: configure tool.coverage.run and fail_under in pyproject.toml like the exemplars; exercise all new src lines.
3. Imports: use from src... in scripts/tests as in existing projects; infrastructure imports allowed; never import another projects/* package.
4. Determinism: fixed RNG seeds for anything stochastic; headless plotting (MPLBACKEND=Agg) where relevant.
5. Naming: <PROJECT_SLUG> is lowercase snake_case; package name in pyproject.toml aligns with repo conventions.

One-shot deliverables (do all in one pass):

1. Full directory tree and files for projects/<PROJECT_SLUG>/ as above.
2. Minimal but real domain implementation in src/ (not stubs), with typed public APIs and logging via infrastructure.core.logging_utils.get_logger where appropriate.
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
