# EDA Notebook — Exploratory Data Analysis Exemplar

**This is an active project** in the `projects/` directory, discovered and
executed by infrastructure discovery functions. Public exemplar roster:
[`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on).
Publication DOI layout:
[`docs/guides/zenodo-doi-strategy.md`](../../../docs/guides/zenodo-doi-strategy.md).
Manuscript semantics:
[`docs/guides/manuscript-semantics.md`](../../../docs/guides/manuscript-semantics.md).

Decision memory and verifier hardening follow
[`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md):
use nearby `WHY:` comments only for surprising local choices, keep volatile
counts generated, and add negative controls for verifier-like gates.

This exemplar demonstrates the **exploratory-data-analysis / computational
notebook** archetype: an interactive walkthrough notebook
([`notebooks/eda_walkthrough.ipynb`](notebooks/eda_walkthrough.ipynb)) that
imports a small, fully-tested library instead of burying logic in cells. The
notebook is the fast entry point a researcher reaches for first; the library is
what keeps that exploration reproducible, covered, and reusable.

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/eda/` (domain) | Pure pandas/numpy data transforms — **no** plotting, no file I/O, **no** `infrastructure` imports |
| `notebooks/` | Thin walkthrough; cells only call `src` functions (no `def`/`class` in cells) |
| `scripts/` | Thin orchestrators; may import `infrastructure/` and `src/`; the only place matplotlib + file writes live |
| Live counts | Link [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md); **do not** hardcode measured test totals or coverage % |

The boundary is enforced by `check_project_src_infrastructure_boundary` via
`scripts/check_template_drift.py --strict` and
[`manuscript/layer_contract.yaml`](manuscript/layer_contract.yaml).

## Configuration as the source of truth

`manuscript/config.yaml` is the configuration single source of truth for paper
title, authors, keywords, version, and publication metadata; it is mirrored by a
sanitized [`manuscript/config.yaml.example`](manuscript/config.yaml.example) with
the same top-level sections. The dataset schema (which columns are numeric) is
declared in `src/eda/dataset.py::DatasetSchema`. No absolute paths are hardcoded
in code — the shipped CSV (`data/measurements.csv`) resolves relative to the
project root.

## Key capabilities

- **Deterministic dataset**: a shipped CSV fixture with a designed correlation
  structure and a handful of missing cells, so every statistic is reproducible.
- **Tested EDA library** (`src/eda/`): `load_dataset`, `clean_dataset`,
  `normalize_numeric`, `summary_statistics`, `group_means`,
  `correlation_matrix`, `strongest_pairs`, and figure-data preparers.
- **Notebook -> tested src extraction**: the workflow this template teaches —
  when a cell grows beyond a one-line call, extract it into `src/eda/` with a
  test first (TDD).
- **Thin analysis script**: [`scripts/eda_analysis.py`](scripts/eda_analysis.py)
  runs the EDA headless (`MPLBACKEND=Agg`), writes figures + a summary CSV to
  `output/`, and prints output paths for manifest collection.

## Run via the template monorepo

```bash
# From the repository root — run the analysis pipeline (thin orchestrator)
uv run python projects/templates/template_eda_notebook/scripts/eda_analysis.py
# Writes output/figures/*.png and output/data/summary_statistics.csv

# Open the walkthrough notebook (calls the same tested src functions)
#   notebooks/eda_walkthrough.ipynb
```

## Testing

```bash
# Run project tests with the 90% coverage gate (configuration source of truth: pyproject.toml)
uv run pytest projects/templates/template_eda_notebook/tests \
    --cov=projects/templates/template_eda_notebook/src --cov-fail-under=90

# Single class
uv run pytest projects/templates/template_eda_notebook/tests -k "TestCorrelationMatrix"
```

Live test count and achieved coverage:
[`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) — do not copy
the numbers here.

## Advisory research overlays (validation inputs, not autonomous agents)

- [`domain_profile.yaml`](domain_profile.yaml) — declares the `eda_notebook`
  domain, preferred outputs, review gates, source policy, and artifact
  expectations.
- [`experiment_plan.yaml`](experiment_plan.yaml) — declares the raw / cleaned /
  normalized conditions, the primary metric, expected figures/tables, a
  baseline, and an ablation.
- [`data/claim_ledger.yaml`](data/claim_ledger.yaml) — registers sourced numeric
  claims for evidence-registry validation.

## Protocol for AI agents

**Critical Directive**: Before modifying this project, reference the rules in
`docs/`:

- [`docs/agent_instructions.md`](docs/agent_instructions.md) — operational constraints.
- [`docs/testing_philosophy.md`](docs/testing_philosophy.md) — zero-mock policy, before touching any test.
- [`docs/architecture.md`](docs/architecture.md) — the thin-orchestrator boundary, before altering `scripts/`/`src/`.

## See Also

- [Root projects AGENTS.md](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on) — public exemplar roster.
- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md).
- [`manuscript/SYNTAX.md`](manuscript/SYNTAX.md) — Pandoc citation/cross-reference syntax.
- [`src/AGENTS.md`](src/AGENTS.md) — EDA library API reference.
- [`TODO.md`](TODO.md) — template-status gaps and improvement ladder.
