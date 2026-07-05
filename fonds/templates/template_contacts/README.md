# template_contacts

**Type:** contacts  
**Version:** 1.0  
**License:** CC0-1.0

A research contacts registry — exemplar template for managing collaborators, advisors, and institutional contacts.

---

## Contents

```
template_contacts/
├── fonds.yaml              ← manifest
├── AGENTS.md               ← agent documentation
├── README.md               ← this file
├── .gitignore
└── data/
    ├── contacts.yaml       ← YAML contact list (source of truth)
    └── contacts.json       ← JSON mirror
```

---

## Usage

### As a template

```bash
cp -r fonds/templates/template_contacts fonds/my_contacts
# Edit fonds.yaml and replace data/ with real contacts
```

### Reading contacts in Python

```python
import yaml, pathlib

contacts = yaml.safe_load(
    pathlib.Path("fonds/my_contacts/data/contacts.yaml").read_text()
)
for c in contacts:
    print(c["name"], c["email"])
```

---

## Contact schema

| Field | Required | Description |
|---|---|---|
| `id` | ✓ | Unique slug (e.g. `jane-doe`) |
| `name` | ✓ | Full name |
| `email` | ✓ | Primary email |
| `affiliation` | | Institution or organisation |
| `role` | | `collaborator`, `advisor`, `reviewer`, `contact` |
| `tags` | | List of topic tags |
| `orcid` | | ORCID identifier |
| `website` | | Personal or lab URL |
| `notes` | | Free-form notes |

---

## Sample data

See `data/contacts.yaml` for 5 example contacts with placeholder data.

> **Privacy note:** Never commit real personal data to a public repository without explicit consent. Use placeholder data in public exemplar fonds and keep real contacts in a git-ignored private fond.
