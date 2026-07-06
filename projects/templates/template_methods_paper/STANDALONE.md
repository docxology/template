# Standalone Fork Guide

## Purpose

`template_methods_paper` is the canonical methods-paper exemplar: a small,
tested domain language for specifying controlled methods
(`src/methods_dsl/`), a thin analysis script, and a manuscript whose subject
is the methodology itself rather than results from running it.

## Copy This When

Use it when you are writing a paper that describes a methodology,
procedure, or specification language — and want every claim about that
methodology (vocabulary size, gate count, determinism, plan hashes) traced
to tested, deterministic code rather than asserted in prose.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_methods_paper \
  --dest projects/working/my_methods_paper \
  --new-name my_methods_paper
```

Fallback when the helper is unavailable (rsync with explicit exclusions):

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  template_methods_paper/ projects/working/my_methods_paper/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, `codemeta.json`, and `pyproject.toml`.
- Replace or extend the controlled vocabulary in `src/methods_dsl/units.py`
  and `vocabulary.py` to match your domain's units and step kinds.
- Replace `src/methods_dsl/examples_methods.py`'s worked examples with your
  own methods, and update their tests.
- Re-run `scripts/methods_analysis.py` and regenerate manuscript claims
  before publishing — every `{{TOKEN}}` in the manuscript is sourced from
  `output/data/compiled_plans.json` and `output/reports/*.json`, never
  hand-typed.

## Validation Commands

From the template repository root after copying into `projects/working/`:

```bash
uv run pytest projects/working/my_methods_paper/tests \
  --cov=projects/working/my_methods_paper/src --cov-fail-under=90
uv run python projects/working/my_methods_paper/scripts/methods_analysis.py
```

For the public exemplar:

```bash
uv run pytest template_methods_paper/tests \
  --cov=template_methods_paper/src --cov-fail-under=90
```

## Standalone By Design

`src/methods_dsl/` is standalone except one sanctioned exception: the
logging adapter (`_logging.py`) reaches into the repository's unified
logging system, declared in `manuscript/layer_contract.yaml`. Every other
module imports only the Python standard library, so the DSL itself is
forkable as an infrastructure-free package; the thin analysis script and the
manuscript-rendering pipeline are the only places that touch shared
infrastructure beyond that one adapter.

## What Not To Claim

Do not claim new methods or guarantees from a renamed fork until
`scripts/methods_analysis.py` has been re-run against your replaced
`examples_methods.py` and the manuscript's `{{TOKEN}}` values (step counts,
plan hashes, gate pass counts, the live determinism check) regenerated from
that run.
