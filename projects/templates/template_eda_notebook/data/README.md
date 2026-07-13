# template_eda_notebook/data

Project-maintained **inputs** for the EDA exemplar (not pipeline outputs).

## Quick reference

| File | Role |
| --- | --- |
| `measurements.csv` | Shipped, deterministic dataset (120 subject records) the EDA library loads |
| `claim_ledger.yaml` | Source-backed numeric and artifact claims for evidence validation |

`measurements.csv` is a static, committed fixture with fixed content (no
generator script ships in this tree); it is the source of truth for every
statistic in the manuscript. Generated analysis outputs (figures, summary CSV)
belong under `output/` during pipeline runs, not here.

Schema and edit protocol: [`AGENTS.md`](AGENTS.md).
