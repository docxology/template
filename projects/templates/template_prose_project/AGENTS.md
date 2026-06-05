# template_prose_project — Agent Guide

## Purpose

Prose-focused exemplar demonstrating end-to-end use of
`infrastructure/prose/` and `infrastructure/reference/`. Standalone editorial
workflow — fast and offline by default. Exemplar roster:
[`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on).

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## Layout

```mermaid
flowchart TB
    P[/projects/templates/template_prose_project/]
    P --> SRC[/src<br/>domain orchestration/]
    P --> T[/tests<br/>real-data tests · no mocks/]
    P --> SC[/scripts<br/>thin orchestrators/]
    P --> M[/manuscript/]
    P --> DOCS[/docs/]
    P --> OUT[/output<br/>regeneratable/]
    P --> META[pyproject.toml · README.md ·<br/>AGENTS.md · .gitignore]
    P --> OVERLAY[domain_profile.yaml · experiment_plan.yaml ·<br/>data/claim_ledger.yaml<br/>advisory controls · evidence validation]

    SRC --> SRC_F[config.py · pipeline.py · figures.py ·<br/>manuscript_variables.py · report.py]
    SC --> SC_F[run_prose_pipeline.py ·<br/>y_generate_prose_figures.py ·<br/>z_generate_manuscript_variables.py]
    M --> M_F[config.yaml · preamble.md ·<br/>00_abstract → 06_reproducibility.md ·<br/>99_references.md · references.bib]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef pkg fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef f fill:#0f766e,stroke:#0f172a,color:#fff
    class P d
    class SRC,T,SC,M,DOCS,OUT pkg
    class SRC_F,SC_F,M_F,META,OVERLAY f
```

## Key contracts

* `src/config.py::ProjectConfig` — every knob is here. Add a new check
  by adding a field to `ProseAnalysisConfig`, parsing it in
  `from_dict`, and wiring it into `pipeline.run_prose_pipeline`.
* `src/pipeline/__init__.py::run_prose_pipeline` — the only function that
  touches `infrastructure.prose.*` or
  `infrastructure.reference.citation.*`. Returns a
  :class:`ProseRunArtifacts` so the script knows where every artefact
  landed.
* `src/figures.py` — pure matplotlib; takes a `ManuscriptReport` and a
  `Path`, returns the saved file paths.
* `src/manuscript_variables.py` — derives substitution variables from
  the JSON report; no project-specific knowledge embedded.
* `src/report.py::write_review_report` — single function that takes a
  `ManuscriptReport` + `CheckResult`s and writes markdown.
* `domain_profile.yaml` and `experiment_plan.yaml` — declarative advisory
  overlays for review gates, source policy, artifact expectations, benchmark
  rubric weights, validation conditions, primary metric, baseline, and ablation.
* `data/claim_ledger.yaml` — file-backed registry of numeric claims that are
  intentionally sourced from project code, manuscript examples, or generated
  reports rather than manuscript variables.

These files are validation inputs only and do not run autonomous review agents.

## Run modes

| Command | Behaviour |
|---|---|
| `python scripts/run_prose_pipeline.py` | Default config; reads `manuscript/`, writes everything. |
| `… --strict` | Exit non-zero if any configured check fails. |
| `… --config other.yaml` | Use an alternative config file. |
| `… --project-root path` | Run against an isolated project root. |

## Testing

```bash
uv run pytest projects/templates/template_prose_project/tests/ -v
```

All tests run offline. Real prose inputs, real BibTeX files, real
`tmp_path` directories, real subprocess invocation of the scripts. No
mocks.

## Extending

To add a new check:

1. Edit `src/config.py::ProseAnalysisConfig` to add the new field.
2. Add a `_check_<name>` function in `src/pipeline/checks.py`.
3. Wire it into `run_prose_pipeline` so it appears in `artifacts.checks`.
4. Add a test in `tests/test_pipeline.py` covering both `passed=True`
   and `passed=False` outcomes (the existing `TestCheckUnits` class
   shows the pattern).
5. Optionally surface its result in `src/report.py::write_review_report`.

To add a new figure:

1. Add a `plot_<name>` function in `src/figures.py`.
2. Append it to `generate_all_figures`.
3. Reference the output PNG in `manuscript/03_results.md` if desired.

To target a different manuscript:

1. Edit `manuscript_dir` in `manuscript/config.yaml`.
2. Adjust `prose.target_grade_level_*` and `bibliography.fail_on_*` to
   match the target audience.
3. Re-run the pipeline.

## See also

* [`README.md`](README.md) — quick reference.
* [Publishing guide](../../../docs/guides/publishing-guide.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md)
* [`docs/architecture.md`](docs/architecture.md) — module dependency graph.
* [`docs/quickstart.md`](docs/quickstart.md) — getting started.
* [`infrastructure/prose/AGENTS.md`](../../../infrastructure/prose/AGENTS.md) —
  underlying module agent guide.
* [`infrastructure/reference/AGENTS.md`](../../../infrastructure/reference/AGENTS.md) —
  bibliography agent guide.
