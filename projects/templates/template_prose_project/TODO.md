# template_prose_project TODO

Forward-only integrity backlog for the prose-review exemplar. Keep this file
about template status, validation depth, and forkability.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_prose_project/manuscript --repo-root .` — **pass** (no render-blocking pitfalls or undefined citations).
- Project tests and coverage (live counts in
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md), not pinned here):
  `uv run pytest projects/templates/template_prose_project/tests/ --cov=projects/templates/template_prose_project/src --cov-fail-under=90`
  — **134 passed, 99.58% coverage** (measured 2026-08-02 with an isolated
  `--cov-config` datafile; the repo-root coverage config merges concurrent
  agents' `.coverage` data, so re-measure with `COVERAGE_FILE` isolation).
- Prose analysis is offline by default and uses real markdown and BibTeX fixtures.
- Canonical pipeline (analysis → render → validate → copy) for
  `templates/template_prose_project`: **green**; all five configured checks
  pass; combined PDF renders with **0 LaTeX errors, 0 unresolved `??`,
  14 pages**, no unresolved `{{TOKEN}}`.
- Determinism recipe (run twice, diff): `run_prose_pipeline.py` run twice into
  an isolated `--project-root` produces **byte-identical** `manuscript_report.json`,
  `checks.json`, `evidence_summary.json`, `run_summary.json` (verified 2026-08-02).
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_prose_project --strict` — **no drift detected**.
- Style + type gates over public source paths:
  `uv run python -m infrastructure.project.public_scope source-paths` piped to ruff and mypy.

## Integrity and template-status gaps

- Keep editorial metrics framed as diagnostics, not publication approval.
- **Shipped:** `output/evidence_summary.json` separates readability, citation
  density, bibliography consistency, structural outline results, and quality
  flags under a versioned diagnostic-only schema.
- Keep prose pipeline orchestration thin over `src/` and `infrastructure/prose`.
- **Fixed (2026-08-02 pass 1 — accuracy):** the manuscript and docs claimed the
  bibliography cross-check used `infrastructure.reference.citation.parse_bibfile`;
  the code uses the project-owned `src/prose_facade.parse_bib_keys` regex.
  All affected surfaces now describe the real seam: `src/` is
  `infrastructure`-free; the thin `scripts/` layer calls
  `infrastructure.prose.analyze_manuscript` / `load_report_json` /
  `manuscript_injection`. `data/claim_ledger.yaml` dead source fixed;
  `docs/output_conventions.md` producer/consumer rows corrected;
  `.agents/` catalog completed with READMEs.
- **Shipped (2026-08-02 pass 2 — capability):** named editorial presets.
  `prose.preset: lenient|strict` seeds defaults for any knob not set
  explicitly; explicit keys win; unknown presets raise `ValueError`.
  Bundled config declares `lenient`; `config.yaml.example` declares `strict`.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` stricter than the bundled exemplar config so forks see realistic editorial defaults — now **enforced by test** (`test_example_config_parses_and_is_stricter_than_bundled`).
- Add migration tests if prose threshold names or report output keys change — check-name and schema-shape assertions live in `tests/test_pipeline.py`.

## Documentation and signposting gaps

- Keep README and AGENTS clear that no LLM or Ollama dependency is required for the default review.
- Link any new report sections from `docs/architecture.md` and `docs/quickstart.md`.
- `docs/AGENTS.md` per-file line-count inventory re-verified 2026-08-02 against `wc -l` (README 118, AGENTS 169, agent_instructions 203, architecture 80, style_guide 268, syntax_guide 209, testing_philosophy 169, rendering_pipeline 258, output_conventions 66, quickstart 81, troubleshooting 191, faq 237). Re-check after any doc edit.

## Test and validator gaps

- Keep negative controls for skipped heading levels, citation-density
  regressions, and missing bibliography entries as the suite grows.
- **Shipped (2026-08-02):** `tests/test_claim_ledger.py` — every
  `data/claim_ledger.yaml` claim's `source` must resolve to a real file and
  its `value` must bind to live code/prose (would have caught the dead
  `src/pipeline.py` reference); `tests/test_manuscript_structure.py` —
  `{#sec:...}` labels unique, every `[@sec:...]` reference resolves, no
  `[@fig:...]` references; preset + example-sync tests in `tests/test_config.py`.
- Add report-schema tests before downstream docs depend on new report fields.
- Add or document a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks. **Documented:** `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest` serves this role.

## Ordered improvement ladder

1. Keep offline prose checks green under project coverage. **Done.**
2. Add structured evidence summary output if report consumers need stable machine-readable fields. **Done** — `output/evidence_summary.json` (schema `template-prose/evidence-summary/1`).
3. Add stricter editorial profiles only as named config presets with tests. **Done** — `prose.preset: lenient|strict` with preset tests.
4. Add optional LLM review only behind explicit config and offline-safe defaults. **Open** — the natural next fork-level extension; keep it out of the default run.
