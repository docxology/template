# Data Directory — Agent Guide

Versioned project **inputs** only. Pipeline outputs must not be committed here.

## `measurements.csv`

The shipped dataset the EDA library loads via
`src/eda/dataset.py::load_dataset()`. It is a static, deterministic fixture
(120 rows; columns `subject_id`, `group`, `height_cm`, `weight_kg`,
`resting_hr_bpm`) with a designed correlation structure and a few blank numeric
cells that exercise the missing-data path. Treat it as a fixture: if it is ever
replaced, keep the replacement deterministic (fixed seed, checked in) and
update `DatasetSchema` if the columns change.

## `claim_ledger.yaml`

Evidence-registry for manuscript claims that are intentionally sourced from
code, the dataset, or generated reports rather than `{{VARIABLE}}` injection.

### Schema (preserve when adding rows)

| Field | Purpose |
| --- | --- |
| `claim_id` | Stable identifier |
| `kind` | Claim category |
| `value` | Declared numeric or textual value |
| `source` | Provenance (module, manuscript section, artifact) |
| `source_tier` | Trust tier for validation |
| `freshness` | Staleness policy |
| `artifact_path` | Optional path to backing file |

## Edit protocol

1. Edit `claim_ledger.yaml` only when manuscript claims, figure defaults, or
   source-backed numeric facts change.
2. Re-run evidence validation / pipeline stages that consume the ledger.
3. Do not store generated CSV/JSON/PNG under `data/` — those go to `output/`.

Quick orientation: [`README.md`](README.md).
