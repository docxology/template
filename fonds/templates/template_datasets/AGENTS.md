# AGENTS.md — template_datasets

Agent documentation for the `template_datasets` exemplar fond.

---

## Purpose

This fond stores a dataset registry with provenance, licensing, and access metadata as YAML (source of truth) and JSON (mirror). It is the canonical exemplar for `type: datasets` fonds.

---

## Files

| File | Role |
|---|---|
| `fonds.yaml` | Manifest — type, version, tags |
| `data/datasets.yaml` | YAML dataset registry (source of truth) |
| `data/datasets.json` | JSON mirror |
| `README.md` | Human documentation |
| `AGENTS.md` | This file |
| `.gitignore` | Standard ignores |

---

## Reading

```python
import yaml, json, pathlib

datasets = yaml.safe_load(pathlib.Path("data/datasets.yaml").read_text())
# or
datasets = json.loads(pathlib.Path("data/datasets.json").read_text())
```

---

## Schema

Each dataset entry:

```yaml
id: mnist-2010                         # slug, unique dedup key
name: "MNIST Handwritten Digits"       # full name
version: "1.0"                         # dataset version
license: "CC0-1.0"                     # SPDX identifier
description: "..."                     # optional
url: "http://yann.lecun.com/exdb/mnist" # optional download / landing page
doi: "10.1234/example"                 # optional DOI
size_gb: 0.05                          # optional, in gigabytes
format:                                # optional list
  - binary
tasks:                                 # optional list
  - image-classification
tags:                                  # optional list
  - vision
  - benchmark
notes: "..."                           # optional free-form notes
```

---

## Adding datasets

1. Append a new entry to `data/datasets.yaml`.
2. Update `data/datasets.json` to match.
3. Ensure `id` is a unique slug.
4. Bump `version` in `fonds.yaml` if the schema changes.

---

## Deduplication

```python
import yaml, collections, pathlib

datasets = yaml.safe_load(pathlib.Path("data/datasets.yaml").read_text())
ids = [d["id"] for d in datasets]
dupes = [k for k, n in collections.Counter(ids).items() if n > 1]
assert not dupes, f"Duplicate dataset ids: {dupes}"
```

---

## Sync YAML → JSON

```python
import yaml, json, pathlib

datasets = yaml.safe_load(pathlib.Path("data/datasets.yaml").read_text())
pathlib.Path("data/datasets.json").write_text(
    json.dumps(datasets, indent=2, ensure_ascii=False)
)
```

---

## Validation checklist

- [ ] Every entry has `id`, `name`, `version`, `license`
- [ ] `id` values are unique slugs
- [ ] `datasets.json` is in sync with `datasets.yaml`
- [ ] `license` is a valid SPDX identifier or `"Proprietary"`
- [ ] No actual dataset binaries committed (only metadata)
