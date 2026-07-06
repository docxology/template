# AGENTS - `template_storybook`

`template_storybook` is a public, standalone exemplar for full-page creative
PDFs. It renders a deterministic illustrated storybook from `content/story.yaml`
using project-local source code and thin Stage-02 scripts.

## Contract

- `content/story.yaml` owns the story text, cast, page order, overlay choice,
  and palettes.
- `src/storybook/` owns character generation, page validation, illustration,
  text overlay, manifest writing, and PDF assembly.
- `scripts/` may only select a page or final artifact and call `src/storybook/`.
- `output/` is generated; regenerate it through scripts rather than editing it.

Configuration entry points are `content/story.yaml` and
`manuscript/config.yaml`; keep `manuscript/config.yaml.example` aligned for
forks.

For project-scale decisions and negative controls, follow the repository memory
and decision-record rule in
[`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md).

## Verification

Run from the repository root:

```bash
uv run pytest projects/templates/template_storybook/tests/ --cov=projects/templates/template_storybook/src --cov-fail-under=90
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_storybook
uv run python scripts/pipeline/stage_03_render.py --project templates/template_storybook
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_storybook
uv run python scripts/pipeline/stage_05_copy.py --project templates/template_storybook
```

After illustration changes, inspect `projects/templates/template_storybook/output/pdf/the-shape-between.pdf`.

## Publishing

This project is public and forkable, but the bundled story is illustrative
fiction. Do not present it as a sourced children's book, field study, or real
child-development intervention.
