# Reference Module

> **Bibliographic data interchange — BibTeX read / write / convert.**

**Location:** `infrastructure/reference/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [Literature Workflow](../../guides/literature-workflow-guide.md) | [Code Review Checklist](../../development/code-review-checklist.md)

---

## Key Features

- **BibTeX I/O** — `parse_bibtex` / `parse_bibfile`, `render_entry` / `render_database`, `write_bibfile`.
- **Entry model** — `BibEntry`, `BibDatabase` order-preserving dataclasses; `BibParseError` for malformed input.
- **Conversion** — `paper_to_bibentry()` turns a `Paper` (from the [search module](search-module.md)) into a stable `BibEntry`.
- **Citation key generation** — `generate_citation_key()` produces deterministic keys in the project's house style (`<author_surname><year><title_word>`).

This module is the **export side** of the literature workflow; the discovery side lives in [`search`](search-module.md).

## Subpackages

| Subpackage | Focus |
| --- | --- |
| `reference/citation/` | BibTeX parse / render / convert utilities (`BibEntry`, `BibDatabase`, `paper_to_bibentry`) |
| `reference/verification/` | Deterministic reference-existence checks against live or cached sources |

The citation layer is the canonical BibTeX writer/parser for the repo. The
verification layer is the anti-hallucination gate that checks whether entries
actually resolve before manuscripts ship.

---

## Public API

```python
from infrastructure.reference import (
    BibEntry, BibDatabase, BibParseError,
    parse_bibtex, parse_bibfile,
    render_entry, render_database,
    write_bibfile,
    paper_to_bibentry, generate_citation_key,
)
```

---

## Usage Pattern

```python
from pathlib import Path
from infrastructure.reference import parse_bibfile, render_database

db = parse_bibfile(Path("projects/archive/template_search_project/manuscript/references.bib"))
print(render_database(db))
```

---

## Review Criteria Mapping

The reference module is reviewed primarily against criteria 2 (Composability — only depends on `core`, never on `search` directly), 3 (Functionality / SSOT — single owner of BibTeX format knowledge), and 8 (Reproducibility — `generate_citation_key` and `render_database` must be deterministic). See [Code Review Checklist](../../development/code-review-checklist.md).
