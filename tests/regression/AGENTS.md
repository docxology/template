# `tests/regression/` — agent guide

> Companion to [`README.md`](README.md). What agents need to know when
> working in the regression-test tier.

## Purpose

Bind every quantitative manuscript claim (figure value, table cell,
p-value, coefficient) to a pinned numerical ground-truth in
[`pinned_values/`](pinned_values/), re-derived on every CI run.
**Different from coverage**: coverage says "the code ran"; this says
"the science is still the science."

## Layout

```
tests/regression/
├── README.md            (reader entrypoint)
├── AGENTS.md            (this file)
├── __init__.py
├── conftest.py          (pinned_values fixture)
├── pinned_values/       (per-project ground-truth JSON)
└── projects/
    └── <project>/
        ├── figures/     (one test per manuscript figure)
        └── tables/      (one test per manuscript table)
```

## When you must add a test here

- You changed a `projects/<X>/scripts/y_*.py` script that emits a figure
  whose numbers appear in the manuscript.
- You changed a `projects/<X>/src/` algorithm that drives a manuscript
  claim.
- You changed a manuscript table cell — the table's regression test must
  then either pass against the new value or be updated *with a
  justification* in the same commit.

## When you must NOT add a test here

- "Smoke" tests of script execution — those belong in
  `projects/<X>/tests/test_scripts.py`.
- Coverage shimming — pinned regression tests bind *values*, not
  *coverage percent*.

## Updating a pinned value

1. Open `pinned_values/<project>.json`.
2. Change the value AND add a `_provenance.<key>` entry recording: the
   commit SHA, the date, the reason, and the script invocation that
   produced the new value.
3. Run the relevant regression test; assert it passes.
4. Update the manuscript markdown to match.
5. Commit all three in one change — the value, the provenance, and the
   prose.

## Related

- [`README.md`](README.md) — full philosophy and rationale
- [`../../docs/maintenance/regression-testing.md`](../../docs/maintenance/regression-testing.md) — long-horizon design
- [`../../docs/development/testing/`](../../docs/development/testing/) — wider testing strategy
