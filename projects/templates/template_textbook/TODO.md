# template_textbook TODO

Forward-only integrity backlog for the modular fillable textbook scaffold.
Keep this focused on book-scale structure, configurability, and validation.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_textbook/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_textbook/tests/ --cov=projects/templates/template_textbook/src --cov-fail-under=90`
- Structural integrity is driven by `manuscript/config.yaml`, chapter stubs, figure generation, and manuscript-integrity tests.
- Repo drift gate: `uv run python scripts/check_template_drift.py --strict`
- Stage 04 warning snapshot, 2026-06-20: generated figure registry passes; evidence registry still reports 123 unsupported pedagogical numbers; artifact manifest reports advisory drift after single-stage regeneration.

## Integrity and template-status gaps

- Keep `manuscript/config.yaml` as the only source of truth for parts, chapters, appendices, labs, and question banks.
- Add a generated scaffold audit that reports missing stubs, disabled chapters, orphan files, and stale figure references.
- Keep finished chapters clearly separated from fillable stubs.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` small enough to copy while preserving required book, render, units, and appendix schema.
- Add migration tests if `units:` or appendix keys change.

## Documentation and signposting gaps

- Keep README, AGENTS, and manuscript docs clear about worked exemplars versus stubs.
- Link any new structural config keys from the README, AGENTS, and visualization guide.

## Test and validator gaps

- Add negative controls for orphan chapter files, missing labs/questions, stale Mermaid diagrams, and unresolved stub markers in finished chapters.
- Add deterministic checks for generated cover art and diagrams when visual styles change.
- Register textbook worked-example numbers, percentages, and appendix-gallery constants as configured facts, or mark them as documentation-only examples, before treating Stage 04 as warning-free.
- Add or document a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks.
- The 2026-06-21 ast-grep audit found the intentional Mermaid `subprocess.run`
  renderer boundary; future hardening should keep a single timeout/cwd/error
  policy for optional external diagram tools and document the fallback path.

## Ordered improvement ladder

1. Keep scaffold, figure, diagram, and manuscript-integrity tests green.
2. Add structured scaffold audit output and stale-file detection.
3. Add copy-and-customize examples for short course notes and full textbook shapes.
4. Promote a filled textbook fork only after unresolved stub markers and placeholder chapters are blocked by validation.
