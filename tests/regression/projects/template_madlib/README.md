# `tests/regression/projects/template_madlib/` — regression suite

> Pinned numerical regression tests for `template_madlib` manuscript
> values. Loads ground truth from
> [`../../pinned_values/template_madlib.json`](../../pinned_values/template_madlib.json).

## Layout

- `tables/` — one test file per manuscript claim cluster (currently the
  configuration/token-plan/QA/lexicon counts rendered into
  `05_experimental_setup.md` and `06_evaluation.md`)

Every value is re-derived through the deterministic token-injection
pipeline (`src.manuscript_variables.generate_variables`,
`src.config.load_madlib_config`, `src.tokens.generate_token_plan`) run
against the committed `manuscript/config.yaml` (seed 431) — never
hand-copied from the rendered manuscript.

See [`../../README.md`](../../README.md) for the philosophy.
