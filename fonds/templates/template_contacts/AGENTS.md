# AGENTS.md — template_contacts

Agent documentation for the `template_contacts` exemplar fond.

---

## Purpose

This fond stores a research contacts registry as YAML (source of truth) and JSON (mirror). It is the canonical exemplar for `type: contacts` fonds.

---

## Files

| File | Role |
|---|---|
| `fonds.yaml` | Manifest — type, version, tags |
| `data/contacts.yaml` | YAML contact list (source of truth) |
| `data/contacts.json` | JSON mirror |
| `README.md` | Human documentation |
| `AGENTS.md` | This file |
| `.gitignore` | Standard ignores |

---

## Reading

```python
import yaml, json, pathlib

contacts = yaml.safe_load(pathlib.Path("data/contacts.yaml").read_text())
# or
contacts = json.loads(pathlib.Path("data/contacts.json").read_text())
```

---

## Schema

Each contact entry:

```yaml
id: jane-doe                      # slug, unique dedup key
name: "Jane Doe"                  # full name
email: "jane@example.org"         # primary email
affiliation: "University of X"    # optional
role: "collaborator"              # collaborator | advisor | reviewer | contact
tags:                             # optional list
  - ml
  - vision
orcid: "0000-0000-0000-0000"      # optional
website: "https://janedoe.org"    # optional
notes: "Met at NeurIPS 2023."     # optional
```

---

## Adding contacts

1. Append a new entry to `data/contacts.yaml`.
2. Update `data/contacts.json` to match.
3. Ensure `id` is unique (slug, lowercase, hyphens).
4. Bump `version` in `fonds.yaml` if the schema changes.

---

## Deduplication

```python
import yaml, collections, pathlib

contacts = yaml.safe_load(pathlib.Path("data/contacts.yaml").read_text())
ids = [c["id"] for c in contacts]
dupes = [k for k, n in collections.Counter(ids).items() if n > 1]
assert not dupes, f"Duplicate contact ids: {dupes}"
```

---

## Sync YAML → JSON

```python
import yaml, json, pathlib

contacts = yaml.safe_load(pathlib.Path("data/contacts.yaml").read_text())
pathlib.Path("data/contacts.json").write_text(
    json.dumps(contacts, indent=2, ensure_ascii=False)
)
```

---

## Validation checklist

- [ ] Every entry has `id`, `name`, `email`
- [ ] `id` values are unique slugs
- [ ] `contacts.json` is in sync with `contacts.yaml`
- [ ] No real PII committed without consent (use placeholder data in public fonds)
