# AGENTS.md — fonds/

Agent documentation for the `fonds/` directory.

---

## Purpose

`fonds/` holds **passive data resource pools** — typed, versioned collections that projects reference but do not modify directly. Agents operating here curate, validate, and augment data assets.

---

## Agent entry points

### Reading a fond

```python
import yaml, pathlib

fond_root = pathlib.Path("fonds/my_bibliography")
manifest   = yaml.safe_load((fond_root / "fonds.yaml").read_text())
data_dir   = fond_root / "data"
```

### Discovering all fonds

```python
import yaml, pathlib

for manifest_path in pathlib.Path("fonds").glob("*/fonds.yaml"):
    manifest = yaml.safe_load(manifest_path.read_text())
    print(manifest_path.parent.name, "→", manifest["type"])
```

---

## Workflow conventions

| Operation | Convention |
|---|---|
| **Validate** | Check that `fonds.yaml` exists and parses cleanly before any data operation |
| **Append** | Add new entries to `data/` files; never overwrite existing entries without a version bump |
| **Version bump** | Increment `version` in `fonds.yaml` when schema changes |
| **Deduplication** | Agents are expected to deduplicate on ingest (key: `id` or canonical field) |
| **Dry-run** | Always support a dry-run mode that previews changes without writing |

---

## Fond types and their schemas

### bibliography

- `data/references.bib` — BibTeX source of truth
- `data/references.csv` — derived flat export; columns: `key,type,title,author,year,journal,doi`
- Dedup key: BibTeX cite key (first column in CSV)

### contacts

- `data/contacts.yaml` — YAML list of contact objects
- `data/contacts.json` — JSON mirror (kept in sync)
- Dedup key: `id` field (slug, e.g. `jane-doe`)

### datasets

- `data/datasets.yaml` — YAML list of dataset descriptors
- `data/datasets.json` — JSON mirror
- Dedup key: `id` field (slug, e.g. `mnist-2010`)

---

## Validation checklist

Before committing changes to a fond, verify:

- [ ] `fonds.yaml` is valid YAML and contains `type`, `description`, `version`
- [ ] `data/` contains at least one non-empty file
- [ ] Dedup key is unique across all entries
- [ ] No binary blobs > 1 MB committed without LFS annotation
- [ ] `.gitignore` is present

---

## Creating a new template fond

```bash
# Bibliography
cp -r fonds/templates/template_bibliography fonds/templates/template_<name>
# Edit fonds.yaml, AGENTS.md, README.md, and populate data/
```

---

## Cross-references

- `projects/AGENTS.md` — how projects reference fonds via `fonds_ref`
- `fonds/templates/` — canonical exemplars for each fond type
