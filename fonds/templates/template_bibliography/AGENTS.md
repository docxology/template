# AGENTS.md — template_bibliography

Agent documentation for the `template_bibliography` exemplar fond.

---

## Purpose

This fond stores a curated bibliography as both BibTeX (`.bib`) and flat CSV (`.csv`). It is the canonical exemplar for `type: bibliography` fonds.

---

## Files

| File | Role |
|---|---|
| `fonds.yaml` | Manifest — type, version, tags |
| `data/references.bib` | BibTeX source of truth |
| `data/references.csv` | Flat CSV export (derived from `.bib`) |
| `README.md` | Human documentation |
| `AGENTS.md` | This file |
| `.gitignore` | Standard ignores |

---

## Reading

```python
import pathlib

bib_text = (pathlib.Path("data/references.bib")).read_text()

import csv
with open("data/references.csv") as f:
    rows = list(csv.DictReader(f))
    # columns: key, type, title, author, year, journal, doi
```

---

## Adding entries

1. Append a BibTeX block to `data/references.bib`.
2. Append the matching row to `data/references.csv`.
3. Ensure the cite key is unique.
4. Bump `version` in `fonds.yaml` if the schema changes.

---

## Deduplication

Dedup key is the BibTeX **cite key** (first column in CSV). To check for duplicates:

```python
import csv, collections

with open("data/references.csv") as f:
    keys = [row["key"] for row in csv.DictReader(f)]

dupes = [k for k, n in collections.Counter(keys).items() if n > 1]
assert not dupes, f"Duplicate cite keys: {dupes}"
```

---

## Validation checklist

- [ ] Every `.bib` entry has a unique cite key
- [ ] Every `.bib` entry has a corresponding CSV row
- [ ] CSV columns present: `key,type,title,author,year,journal,doi`
- [ ] No binary blobs committed
