# docs/ — template_data_descriptor

## What this repo is

A public exemplar for **FAIR-style data descriptor papers and dataset release
packets**. It treats the dataset, schema, provenance chain, licensing, and
validation report as the research object under test. It ships a small public
synthetic demonstration dataset (CSV fixtures under `data/`), a
machine-readable descriptor (`data/example_descriptor.json`) with media types,
sha256 checksums, row counts, and a typed six-field data dictionary, plus a
tested validation library. See the repo [`README.md`](../README.md).

## Directory map

| Path | Role |
| --- | --- |
| `src/data_descriptor/` | Descriptor schema, verification (checksum/row-count recompute), registry, and figure-data modules |
| `scripts/` | Thin orchestrators: `generate_figures.py`, `generate_release_artifacts.py` |
| `tests/` | Zero-mock tests incl. mismatch/verification negative controls |
| `manuscript/` | Section sources (`00_abstract.md` … `99_references.md`), config, references |
| `data/` | Demonstration dataset fixtures and the example descriptor |
| `output/` | Generated figures and release artifacts (never hand-edited) |

## How to run / test

From the template monorepo root:

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_data_descriptor --project-only
uv run pytest projects/templates/template_data_descriptor/tests \
    --cov=projects/templates/template_data_descriptor/src --cov-fail-under=90
```

Project-local scripts (see `scripts/README.md`):

```bash
uv run python projects/templates/template_data_descriptor/scripts/generate_figures.py
uv run python projects/templates/template_data_descriptor/scripts/generate_release_artifacts.py
```

Forks: copy `manuscript/config.yaml.example` to `manuscript/config.yaml` and
keep template-integrity checks green (per repo README).

## Documentation in this tree

- [`AGENTS.md`](AGENTS.md) — agent-facing layout and conventions.

## Status

Publication-track exemplar: `manuscript/` is complete and gate-guarded; this
docs/ tree was added by the docs-audit pass of 2026-08-29.
