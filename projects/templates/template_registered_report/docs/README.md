# docs/ — template_registered_report

## What this repo is

A public exemplar for **registered reports, preregistration, replication, and
robustness-audit workflows**. It makes the planned analysis, frozen hypothesis
ledger, deviations, and post-run claims auditable. This template demonstration
locks a preregistration, validates its completeness, executes the registered
analysis plan against deterministic demonstration data (seeded two-group
dataset), and reports confirmatory and exploratory claims through an explicit
deviation ledger. See the repo [`README.md`](../README.md) and
`manuscript/00_abstract.md`.

## Directory map

| Path | Role |
| --- | --- |
| `src/registered_report/` | Preregistration schema/lock, protocol validation, registered analysis, deviation ledger, robustness audit, and figure-data modules |
| `scripts/` | Thin orchestrators: `generate_figures.py`, `generate_review_artifacts.py` |
| `tests/` | Zero-mock tests incl. the demonstration study and protocol checks |
| `manuscript/` | `00_abstract.md` … `99_references.md`, config, references, `figures/` |
| `data/` | Preregistration fixture registration (`example_registration.json`), claim ledger, and fixture docs |
| `output/` | Generated figures and review artifacts (never hand-edited) |

## How to run / test

From the template monorepo root:

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_registered_report --project-only
uv run pytest projects/templates/template_registered_report/tests \
    --cov=projects/templates/template_registered_report/src --cov-fail-under=90
```

Project scripts, still invoked below from the **monorepo root** (see `scripts/README.md`):

```bash
uv run python projects/templates/template_registered_report/scripts/generate_figures.py
uv run python projects/templates/template_registered_report/scripts/generate_review_artifacts.py
```

In a prepared standalone checkout, the actual local entry points are
`python scripts/generate_figures.py` and
`python scripts/generate_review_artifacts.py`, with
`python -I -m pytest tests/ --cov=src --cov-fail-under=90` for the full suite.
See [`README.md`](../README.md#standalone-project-commands) for genuine SDK/dev
preparation and the still-unchecked `RR-STANDALONE-FIGURES-1` acceptance
obligation; no vendored fallback or monorepo ancestor is the declared SDK.

Forks: copy `manuscript/config.yaml.example` to `manuscript/config.yaml` and
keep template-integrity checks green (per repo README).

## Documentation in this tree

- [`AGENTS.md`](AGENTS.md) — agent-facing layout and conventions.

## Status

Publication-track exemplar: `manuscript/` is complete and gate-guarded; this
docs/ tree was added by the docs-audit pass of 2026-08-29.
