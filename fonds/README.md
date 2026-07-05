# fonds/

**Fonds** are passive data resource pools — curated, versioned, reusable collections of structured data that projects draw from but do not own.

The word *fonds* comes from archival science, where it refers to the complete body of records created by a single entity. Here it denotes a managed data collection with a defined type, schema, and lifecycle.

---

## Concept

Unlike `projects/`, which contain active research workflows, a fond is:

- **Passive** — data at rest, not under active transformation
- **Reusable** — shared across multiple projects
- **Typed** — each fond declares a schema (`bibliography`, `contacts`, `datasets`, `literature`, `generic`)
- **Self-describing** — carries a `fonds.yaml` manifest

A fond is *referenced* by projects, not duplicated. Projects import from fonds; fonds accumulate over time.

---

## Directory layout

```
fonds/
├── README.md              ← this file
├── AGENTS.md              ← agent documentation
├── templates/             ← public exemplars (git-tracked)
│   ├── template_bibliography/
│   ├── template_contacts/
│   └── template_datasets/
└── <name>/                ← your fonds (may be git-ignored locally)
    ├── fonds.yaml
    ├── AGENTS.md
    ├── README.md
    ├── data/
    └── .gitignore
```

---

## Fond manifest (`fonds.yaml`)

Every fond must contain a `fonds.yaml` at its root:

```yaml
type: bibliography         # bibliography | contacts | datasets | literature | generic
description: "..."         # human-readable description
version: "1.0"
tags:
  - curated
creator: "docxology/template"
license: "CC0-1.0"
```

---

## Types

| Type | Purpose | Typical data files |
|---|---|---|
| `bibliography` | Curated reference lists | `.bib`, `.csv`, `.json` |
| `contacts` | Research contacts and collaborators | `.yaml`, `.json` |
| `datasets` | Dataset registry with metadata | `.yaml`, `.json`, `.csv` |
| `literature` | Literature notes and annotations | `.md`, `.yaml` |
| `generic` | Anything not covered above | any |

---

## Creating a new fond

```bash
# 1. Copy the matching template
cp -r fonds/templates/template_bibliography fonds/my_bibliography

# 2. Edit the manifest
$EDITOR fonds/my_bibliography/fonds.yaml

# 3. Populate data/
# ...

# 4. Reference from a project
#    See projects/README.md for the fonds_ref convention
```

---

## Git policy

- `fonds/templates/` — always tracked (exemplars)
- `fonds/<private>/` — add to `.gitignore` if data is sensitive or too large
- Large binary data should be managed with Git LFS or DVC, not committed directly
