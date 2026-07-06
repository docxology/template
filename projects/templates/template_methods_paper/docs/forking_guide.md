# Forking Guide — template_methods_paper

> A 5-minute walkthrough for copying this exemplar into a new methods-DSL
> project. The point is to make every decision explicit: what's required vs
> aesthetic, what's enforced vs convention, and what you'll hit friction on.

## TL;DR

```bash
# 0. From the repo root, install deps once
uv sync

# 1. Clean-copy the exemplar to your new project name
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_methods_paper \
  --dest projects/working/my_methods_project \
  --new-name my_methods_project

# 2. Run the tests against your fork
uv run pytest projects/working/my_methods_project/tests \
    --cov=projects/working/my_methods_project/src --cov-fail-under=90 -q

# 3. Run the analysis against your fork
uv run python projects/working/my_methods_project/scripts/methods_analysis.py
```

**⚠️ Confidentiality invariant.** The repo `.gitignore` is configured so that
only the public canonical exemplars under `projects/templates/` are ever
git-tracked. Your fork (`projects/working/my_methods_project/`) is local-only
and won't be pushed even if you `git add -f` it. Read
[`../../../../CLAUDE.md`](../../../../CLAUDE.md) "CONFIDENTIALITY INVARIANT" for
the full fence.

## What you're forking

A **controlled-method specification DSL skeleton**: pure model/validation/
compilation/export logic in `src/methods_dsl/`, a thin analysis script,
real-fixture `tests/`, and a manuscript whose subject is the methodology
itself. The two included worked examples (`PBSPreparation`,
`SensorCalibrationSweep`) are throwaway scaffolding for the **transferable
pattern**: a controlled vocabulary expressed as typed dataclasses, staged
validation gates, and deterministic compilation. Your fork should preserve
that discipline regardless of the controlled procedure you specify.

## REQUIRED vs AESTHETIC

The full inventory lives in [`AGENTS.md`](AGENTS.md); the short version:

| Class | Examples | Action |
|---|---|---|
| REQUIRED — pipeline gate | `src/methods_dsl/*.py`, `src/__init__.py`, all `tests/test_*.py`, `pyproject.toml`, `manuscript/config.yaml`, `manuscript/*.md`, `manuscript/references.bib`, `manuscript/preamble.md` | Keep them; the 90% coverage gate + LaTeX render depend on them |
| REQUIRED — orchestration | `scripts/methods_analysis.py`, `scripts/z_generate_manuscript_variables.py` | The analysis entry point and the token-injection step this template demonstrates |
| AESTHETIC | `docs/*.md`, `*/STYLE.md`, `*/PATTERNS.md`, `*/CONVENTIONS.md`, `*/AGENTS.md`, `*/README.md` | Drift detected only by `scripts/audit/check_template_drift.py`; update them when code changes |

## Concrete first steps after fork

### 1. Replace the worked examples

Replace or extend `src/methods_dsl/examples_methods.py` with your own
`Method` declarations, built from `model.py`'s dataclasses. Keep
`src/methods_dsl/` **infrastructure-free** outside the one declared
`_logging.py` exception.

### 2. Extend the controlled vocabulary only if you must

Add a `StepKind` to `vocabulary.py` or a `Dimension`/unit to `units.py` only
if your domain genuinely needs one the existing controlled vocabulary
cannot express — a controlled vocabulary generalizes by restraint, not by
expansion (see `manuscript/04_conclusion.md`'s key insights).

### 3. Update the test suite

`tests/` enforces the [Zero-Mock Policy](testing_philosophy.md): real
`Method`/`Step`/`Quantity` fixtures, no `unittest.mock` / `MagicMock` /
`@patch`. Reuse or extend `conftest.py`'s shared fixtures (one per
gate-failure mode) when adding coverage for a new method.

### 4. Update the analysis script

Point `scripts/methods_analysis.py` at your new method(s) — add them to the
list it compiles, exports, and tallies into `compiled_plans.json` and
`gate_report.json`.

### 5. Run the drift checker before pushing

```bash
uv run python scripts/audit/check_template_drift.py --strict
```

## Common friction points (and fixes)

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: src` | Running a script from inside `src/` | `cd` to the repo root and use the full `projects/.../scripts/methods_analysis.py` path |
| `MethodValidationError: ... failed validation` | A constructed `Method` fails one of the four staged gates | Read the gate name + issues in the message; fix the `Method`, never suppress the exception |
| `DimensionError: unknown unit ...` | A `Quantity` uses a unit string not in `units.py`'s controlled table | Add the unit to the table with a test, or use an existing controlled unit |
| Unresolved `{{TOKEN}}` after rendering | Manuscript references a token name `generate_variables()` does not emit | Add it to `src/manuscript_variables.py` + a test, or fix the typo |
| Stale `*.egg-info/` after rename | editable install under the old name | `rm -rf src/*.egg-info/`; `.gitignore` already covers future occurrences |

## See also

- [`AGENTS.md`](AGENTS.md) — full doc inventory and reading order.
- [`agent_instructions.md`](agent_instructions.md) — hard rules.
- [`architecture.md`](architecture.md) — module boundaries.
- [`testing_philosophy.md`](testing_philosophy.md) — zero-mock standard.
- [`output_inventory.md`](output_inventory.md) — producer/stage graph.
- [`troubleshooting.md`](troubleshooting.md) — symptom-driven fixes.
