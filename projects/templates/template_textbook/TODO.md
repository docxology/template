# template_textbook TODO

Forward-only backlog for the modular, fillable book-length manuscript scaffold
(config-driven parts, chapters, and labs).

## Current validation evidence

- Manuscript pre-render gate:
  `uv run python -m infrastructure.validation.cli prerender projects/templates/template_textbook/manuscript --repo-root .`
  → **clean** (no render-blocking pitfalls, no undefined citations).
- Project tests and coverage:
  `uv run pytest projects/templates/template_textbook/tests/ --cov=projects/templates/template_textbook/src --cov-fail-under=90`
  → **192 passed, coverage 96.19%** (last measured run; ≥90% floor met).
- Canonical pipeline stages (2026-08-02 pass):
  - `stage_02_analysis.py` → 3/3 scripts, exit 0 (figures, diagrams, worked-model summary).
  - `stage_03_render.py` → `template_textbook_combined.pdf`, 98 pages,
    0 LaTeX errors (`^! ` in logs), **0 unresolved `??`** in extracted text.
  - `stage_04_validate.py` → clean; `stage_05_copy.py` → outputs copied.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_textbook --strict`
  → **no drift detected**.
- Structural integrity is driven by `manuscript/config.yaml`, chapter stubs,
  figure generation, and the unified audit gate
  (`textbook.audit.run_manuscript_audit`): default mode validates the fillable
  scaffold, while `--require-complete` fails on nonzero per-section stub
  counts and reports the total.
- Live test counts and coverage snapshots belong in
  `../../../docs/_generated/COUNTS.md`, not hardcoded here.

## Pass 2026-08-02 — accuracy and docs-completeness fixes

- `manuscript/config.yaml.example` re-synced to the live `config.yaml` shape:
  4 units × 3 chapters, appendices `reference`/`labs`/`questions` blocks,
  `publication.published_artifacts`, `front_matter` page-two quote and
  acknowledgements, placeholder-safe values; `validate_config(example)` is
  clean and the key shape matches the live config exactly.
- `tests/AGENTS.md` and `docs/testing_guide.md` now list all 11 test modules on
  disk (added `test_analysis.py`, `test_audit.py`, `test_gallery.py`).
- `scripts/AGENTS.md` now names `_bootstrap.py` and `__init__.py` as the
  remaining module files, so the listing matches the on-disk inventory.
- Cross-reference fix: the saturating-response discussion lives in
  `appendix_math_review`, but `part_III/case_studies.md` and
  `labs/part_III/lab_case_studies.md` pointed at `part_I_first_principles`;
  both now cite `[@sec:appendix_math_review]`.
- Render-quality fix: the `{#tbl:gallery_alignment}` caption was separated from
  its table by a paragraph, so pandoc-crossref could not bind it and the
  rendered PDF showed `??` in two places; the caption now sits directly above
  the table and the PDF extracts with **0 `??`**.
- Added `.agents/README.md` and `.agents/skills/README.md` (skill catalog
  files required by the shared `.agents/` contract).
- Verified worked numbers against `src/textbook/models.py` and
  `assets/data/sample_dataset.csv`: logistic growth `[5.00, 20.68, 74.18,
  99.37]`; linear fit slope 1.375, intercept 2.175, R² 0.999; population SD
  1.13. No mismatches found.

## Integrity and template-status gaps

- Keep `manuscript/config.yaml` as the only source of truth for parts, chapters,
  appendices, labs, and question banks.
- Keep finished chapters clearly separated from fillable stubs.
- Keep the structured scaffold audit (`textbook.audit.run_manuscript_audit`)
  covering orphan part markdown, unit intros, and strict-CLI failures.

## Configurable-surface gaps

- `manuscript/config.yaml.example` now mirrors the live shape; add migration
  tests if `units:` or appendix keys change (the example is currently
  shape-checked by hand, not by a test).
- Add a test that pins the example config's key shape to the live config so a
  future divergence is caught automatically.

## Documentation and signposting gaps

- Keep README, AGENTS, and manuscript docs clear about worked exemplars versus
  stubs.
- Link any new structural config keys from the README, AGENTS, and the
  visualization guide.

## Test and validator gaps

- Add negative controls for orphan chapter files, missing labs or questions,
  and stale Mermaid diagrams. Zero-stub completeness now has library and real
  CLI negative controls through `--require-complete`.
- Add deterministic checks for generated cover art and diagrams when visual
  styles change.
- Register textbook worked-example numbers, percentages, and appendix-gallery
  constants as configured facts, or mark them as documentation-only examples,
  before treating Stage 04 as warning-free.
- Add or document a stable final artifact-manifest refresh path for
  single-stage analysis, render, and copy checks. **Documented:**
  `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest`
  serves this role — it writes a current-output snapshot manifest labeled
  `current-output-snapshot` without requiring a full `PipelineExecutor` run.
- **Shipped:** the optional external Mermaid `mmdc` boundary uses a bounded
  timeout, isolated process group, descendant cleanup, and a deterministic
  `.mmd` fallback; keep the policy synchronized with infrastructure Mermaid
  renderers.

## Ordered improvement ladder

1. Keep scaffold, figure, diagram, and manuscript-integrity tests green.
2. Add structured scaffold audit output and stale-file detection.
3. Add copy-and-customize examples for short course notes and full textbook
   shapes.
4. Promote a filled textbook fork only after
   `audit_textbook_quality.py --require-complete` reports zero stubs.
