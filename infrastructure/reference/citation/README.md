# `infrastructure/reference/citation/`

BibTeX read/write/convert that round-trips byte-stable through the same
format as
[`projects/template_code_project/manuscript/references.bib`](../../../projects/template_code_project/manuscript/references.bib).

```mermaid
flowchart LR
    PARSE[parse_bibfile<br/>parse_bibtex] --> DB[BibDatabase<br/>list of BibEntry]
    PAPER[Paper] --> CONV[paper_to_bibentry] --> ENTRY[BibEntry] --> DB
    DB --> RENDER[render_database<br/>write_bibfile] --> BIB[references.bib]
    BIB -. Pandoc natbib .-> PDF[rendered PDF]

    classDef io fill:#0f766e,stroke:#0f172a,color:#fff
    classDef proc fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef ext fill:#7c2d12,stroke:#0f172a,color:#fff
    class PAPER,BIB,PDF io
    class PARSE,CONV,RENDER,DB,ENTRY proc
    class PDF ext
```

## Files

| File | Role |
|---|---|
| `models.py` | `BibEntry`, `BibDatabase`, `CANONICAL_ENTRY_TYPES` |
| `escape.py` | LaTeX-special escape / unescape (single-pass) |
| `bibtex_writer.py` | Render entries with the project's house format |
| `bibtex_parser.py` | Forgiving state-machine parser; preserves field order |
| `converter.py` | `paper_to_bibentry`, `generate_citation_key` |
| `cli.py` | `validate` / `format` / `convert` subcommands |

## Quick reference

```python
from infrastructure.reference.citation import (
    parse_bibfile, render_database, write_bibfile,
    paper_to_bibentry, generate_citation_key,
)
```

For the API surface and worked examples see
[SKILL.md](SKILL.md); for architectural context, see the parent module's
[`AGENTS.md`](../AGENTS.md).
