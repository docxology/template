# `template_prose_project/tests/`

Test-suite agent guide.

## Layout

```mermaid
flowchart TB
    T[/template_prose_project/tests//]
    T --> META[__init__.py · conftest.py]
    T --> CFG[test_config.py<br/>typed YAML loader]
    T --> PIPE[test_pipeline.py<br/>run_prose_pipeline · checks]
    T --> INTEG[test_pipeline_integration.py<br/>bundled manuscript end-to-end]
    T --> FIG[test_figures.py<br/>matplotlib renderers]
    T --> MV[test_manuscript_variables.py<br/>substitution]
    T --> REP[test_report.py<br/>markdown assembly]
    T --> SCR[test_scripts.py<br/>real subprocess invocation]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef code fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef doc fill:#0f766e,stroke:#0f172a,color:#fff
    class T d
    class CFG,PIPE,INTEG,FIG,MV,REP,SCR code
    class META doc
```

## Conventions

* **No mocks.** Every test uses real prose strings, real `tmp_path`
  files, real BibTeX content, and (for `test_scripts.py`) real
  `subprocess.run` calls.
* **`tmp_path` fixture for filesystem isolation.** Tests never write to
  the project's own `output/` directory.
* **Bundled manuscript is the integration fixture.** `test_pipeline_integration.py`
  copies `manuscript/` to a temp dir and runs the whole pipeline against it.
* **Coverage gate: 90%.** Measured coverage → [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md); reductions should be justified in the PR.

## Running

```bash
# Full suite
uv run pytest projects/templates/template_prose_project/tests/ -v

# With coverage gate
uv run pytest projects/templates/template_prose_project/tests/ \
    --cov=projects/templates/template_prose_project/src \
    --cov-fail-under=90

# A single test
uv run pytest projects/templates/template_prose_project/tests/test_pipeline.py::TestRunProsePipeline::test_passing_run -v
```

## Editing rules

* **Tests mirror src.** A new function in `src/<x>.py` deserves a class
  in `tests/test_<x>.py`.
* **Real bibliographies in tests.** When testing the bibliography
  cross-check, write a real (small) `.bib` file rather than constructing
  `BibDatabase` objects directly — this catches parser-level breakage.
* **Subprocess tests live in `test_scripts.py`.** Direct `main()` calls
  belong in script-specific test modules; subprocess tests belong here.

## See also

* [`README.md`](README.md) — quick reference.
* [`../docs/troubleshooting.md`](../docs/troubleshooting.md) — when
  things break.
