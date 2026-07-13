# template_datasets

**Type:** datasets
**Version:** 1.0
**License:** CC0-1.0

A dataset registry and metadata store — exemplar template for cataloguing ML/AI datasets with provenance, licensing, and access information.

---

## Contents

```
template_datasets/
├── fonds.yaml              ← manifest
├── AGENTS.md               ← agent documentation
├── README.md               ← this file
├── .gitignore
└── data/
    ├── datasets.yaml       ← YAML dataset registry (source of truth)
    └── datasets.json       ← JSON mirror
```

---

## Usage

### As a template

```bash
cp -r fonds/templates/template_datasets fonds/my_datasets
# Edit fonds.yaml and replace data/ with your dataset entries
```

### Reading the registry in Python

```python
import yaml, pathlib

datasets = yaml.safe_load(
    pathlib.Path("fonds/my_datasets/data/datasets.yaml").read_text()
)
for d in datasets:
    print(d["id"], d["name"], d["license"])
```

---

## Dataset entry schema

| Field | Required | Description |
|---|---|---|
| `id` | ✓ | Unique slug (e.g. `mnist-2010`) |
| `name` | ✓ | Full dataset name |
| `version` | ✓ | Dataset version string |
| `license` | ✓ | SPDX license identifier or `"Proprietary"` |
| `description` | | Short description |
| `url` | | Landing page or download URL |
| `doi` | | DOI if published |
| `size_gb` | | Approximate size in GB |
| `format` | | List of file formats (e.g. `[csv, parquet]`) |
| `tasks` | | ML tasks it supports (e.g. `[image-classification]`) |
| `tags` | | Free-form topic tags |
| `notes` | | Usage notes, access instructions, caveats |

---

## Sample data

See `data/datasets.yaml` for 5 example entries covering common benchmark datasets.

> **Note:** This fond stores *metadata only*. Actual dataset files should be downloaded separately and are excluded via `.gitignore`. Use DVC or Git LFS if you need to version large files.
