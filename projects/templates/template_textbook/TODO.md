# template_textbook TODO

Forward-only backlog for the modular, fillable book-length manuscript scaffold
(config-driven parts, chapters, and labs).

## Current validation evidence

- Manuscript pre-render gate:
  `uv run python -m infrastructure.validation.cli prerender projects/templates/template_textbook/manuscript --repo-root .`
- Project tests and coverage:
  `uv run pytest projects/templates/template_textbook/tests/ --cov=projects/templates/template_textbook/src --cov-fail-under=90`
- Structural integrity is driven by `manuscript/config.yaml`, chapter stubs,
  figure generation, and the unified audit gate
  (`textbook.audit.run_manuscript_audit`): default mode validates the fillable
  scaffold, while `--require-complete` fails on nonzero per-section stub
  counts and reports the total.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Live test counts and coverage snapshots belong in
  `../../../docs/_generated/COUNTS.md`, not hardcoded here.

## Integrity and template-status gaps

- Keep `manuscript/config.yaml` as the only source of truth for parts, chapters,
  appendices, labs, and question banks.
- Keep finished chapters clearly separated from fillable stubs.
- Keep the structured scaffold audit (`textbook.audit.run_manuscript_audit`)
  covering orphan part markdown, unit intros, and strict-CLI failures.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` small enough to copy while preserving
  the required book, render, units, and appendix schema.
- Add migration tests if `units:` or appendix keys change.

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
  single-stage analysis, render, and copy checks.
- Keep a single timeout, cwd, and error policy for the optional external Mermaid
  `mmdc` renderer boundary, and document its fallback path.

## Ordered improvement ladder

1. Keep scaffold, figure, diagram, and manuscript-integrity tests green.
2. Add structured scaffold audit output and stale-file detection.
3. Add copy-and-customize examples for short course notes and full textbook
   shapes.
4. Promote a filled textbook fork only after
   `audit_textbook_quality.py --require-complete` reports zero stubs.
