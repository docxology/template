---
name: infrastructure-reference
description: Bibliographic-reference utilities for research projects. Read, write, and convert BibTeX entries that match the syntax/semantics of projects/templates/template_code_project/manuscript/references.bib (consumed by Pandoc with --natbib during PDF render -- see infrastructure/rendering/_pdf_combined_pandoc.py). Exposes the `citation` submodule (BibTeX I/O + Paper→BibEntry conversion) and the `verification` submodule (deterministic reference-existence gate against Crossref/OpenAlex/arXiv with a persistent SQLite cache); designed to host additional reference workflows without breaking the public API.
---

# Reference Module

Bibliographic-reference workflows for the template's two-layer architecture.
Output is byte-compatible with the existing
``projects/templates/template_code_project/manuscript/references.bib`` format and round-trips
through the parser without semantic loss.

## `citation` — BibTeX read/write/convert

```python
from infrastructure.reference.citation import (
    BibEntry, BibDatabase,
    parse_bibfile, parse_bibtex, BibParseError,
    render_entry, render_database, render_entries, write_bibfile,
    paper_to_bibentry, generate_citation_key,
    escape_latex, unescape_latex,
)
```

### Read & validate an existing `.bib`

```python
db = parse_bibfile("projects/templates/template_code_project/manuscript/references.bib")
print(len(db), "entries")
boyd = db.find("boyd2004convex")
assert boyd.entry_type == "article"
assert boyd.get("author") == "Boyd, Stephen and Vandenberghe, Lieven"
```

### Build entries programmatically

```python
from collections import OrderedDict
entry = BibEntry(
    entry_type="article",
    citation_key="smith2024example",
    fields=OrderedDict([
        ("title", "An Example Paper"),
        ("author", "Smith, Alice and Jones, Bob"),
        ("journal", "Cambridge UP"),
        ("year", "2024"),
        ("pages", "1-10"),  # auto-normalised to "1--10"
        ("doi", "10.1234/example"),
    ]),
)
print(render_entry(entry))
```

Output (matches the exemplar exactly):

```bibtex
@article{smith2024example,
  title={An Example Paper},
  author={Smith, Alice and Jones, Bob},
  journal={Cambridge UP},
  year={2024},
  pages={1--10},
  doi={10.1234/example}
}
```

### Convert a literature search result to BibTeX

```python
from infrastructure.search.literature import LiteratureClient, SearchQuery, ArxivBackend
from infrastructure.reference.citation import paper_to_bibentry, render_database
from infrastructure.reference.citation.models import BibDatabase

result = LiteratureClient([ArxivBackend()]).search(SearchQuery(text="adam optimizer"))
db = BibDatabase()
for paper in result.papers:
    db.add(paper_to_bibentry(paper))
write_bibfile("output/references.bib", db)
```

### Validate / format from the CLI

```bash
# Round-trip-parse a .bib file.
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_code_project/manuscript/references.bib

# Re-emit a .bib in canonical format (overwrites in place).
uv run python -m infrastructure.reference.citation.cli format path/to/refs.bib

# Convert a JSON file of literature-search Paper records into BibTeX.
uv run python -m infrastructure.reference.citation.cli convert \
    output/papers.json output/references.bib
```

## `verification` — reference-existence anti-hallucination gate

Resolves each cited reference against Crossref → OpenAlex (DOI), arXiv (id), or
Crossref title search, and classifies it `ok` / `mismatch` / `fabricated` /
`unverifiable` / `unchecked` / `anachronism`. Offline-first (consults only the
persistent SQLite cache unless `allow_network=True`); reports `unchecked` on an
offline cache miss so a skipped check never reads as clean.

```python
from infrastructure.reference.verification import (
    ReferenceResolver, ResolutionCache, verify_bibfile, verify_database, verify_entry,
    VerificationStatus, VerificationReport, ReferenceVerdict, BLOCKING_STATUSES,
)

resolver = ReferenceResolver(cache=ResolutionCache("cache.db"), allow_network=True)
report = verify_bibfile("references.bib", resolver, as_of_year=2026)
print(report.summary_line())
assert not report.has_blocking  # no fabricated / mismatch / anachronism
```

```bash
# Offline (cache-only, CI-safe) vs live resolution; gate on blocking verdicts.
uv run python -m infrastructure.reference.verification verify references.bib
uv run python -m infrastructure.reference.verification verify references.bib --live --as-of-year 2026 --fail-on-issues
uv run python -m infrastructure.reference.verification cache-clear
```

See [`verification/SKILL.md`](verification/SKILL.md) for the full descriptor.

## Format Guarantees

* **2-space indent** on every field line.
* **Trailing comma** after every field except the last.
* **`pages={N--M}`** (BibTeX em-dash) regardless of input form (`-`, `–`, `—`).
* **Author normalisation** around ` and `.
* **Verbatim fields** (`year`, `volume`, `number`, `month`, `edition`, `isbn`,
  `issn`, `doi`, `url`) are emitted without LaTeX escaping.
* **Unicode is preserved** (Pandoc / XeLaTeX handle it natively, matching the
  exemplar's convention).
* **`book` / `phdthesis` / `techreport` / `misc`** entries never receive a
  spurious `journal=` field even when their source declared a venue.

## Related Modules

* [`infrastructure.search.literature`](../search/literature/SKILL.md) —
  discovery side of the literature workflow.
* [`infrastructure.publishing.citations`](../publishing/SKILL.md) — citation
  *string* generation (APA / MLA) for human-facing markdown sections.
