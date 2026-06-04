---
name: infrastructure-reference-citation
description: BibTeX read/write/convert that matches the syntax/semantics of projects/templates/template_code_project/manuscript/references.bib (consumed by Pandoc with --natbib -- see infrastructure/rendering/_pdf_combined_renderer.py). Provides BibEntry/BibDatabase models, parse_bibfile/render_database functions, paper_to_bibentry conversion from literature search results, generate_citation_key in the project's house style (firstauthorlastname+year+firsttitleword), LaTeX-special-character escape helpers, and a CLI (validate/format/convert). Use when reading or writing .bib files, exporting search results to BibTeX, or generating citation keys.
---

# Citation Submodule

BibTeX I/O matching `projects/templates/template_code_project/manuscript/references.bib`.

## Reading

```python
from infrastructure.reference.citation import parse_bibfile, parse_bibtex

db = parse_bibfile("projects/templates/template_code_project/manuscript/references.bib")
print(len(db))                      # 8
print(db.keys())                    # ['nocedal2006numerical', ...]
entry = db.find("boyd2004convex")
print(entry.entry_type)             # 'article'
print(entry.get("author"))          # 'Boyd, Stephen and Vandenberghe, Lieven'
print(db.preamble)                  # The @comment{...} block
```

## Writing

```python
from collections import OrderedDict
from infrastructure.reference.citation import (
    BibEntry, BibDatabase, render_database, write_bibfile
)

db = BibDatabase()
db.add(BibEntry(
    "article", "smith2024example",
    OrderedDict([
        ("title", "An Example Paper"),
        ("author", "Smith, Alice and Jones, Bob"),
        ("journal", "Cambridge UP"),
        ("year", "2024"),
        ("pages", "1-10"),       # auto-normalised to "1--10"
        ("doi", "10.1234/example"),
    ]),
))
print(render_database(db))
write_bibfile("output/refs.bib", db)
```

## Convert from a search result

```python
from infrastructure.reference.citation import paper_to_bibentry, generate_citation_key
from infrastructure.search.literature import Paper

paper = Paper(id="x", title="Adam", authors=["Kingma, Diederik P", "Ba, Jimmy"], year=2014, venue="ICLR", venue_type="conference")
entry = paper_to_bibentry(paper)        # entry_type → "inproceedings", key → "kingma2014adam"

# Override either field:
entry = paper_to_bibentry(paper, citation_key="my_custom_key", entry_type="misc")

# Or generate a key without converting:
key = generate_citation_key(authors=["Cauchy, Augustin-Louis"], year=1847, title="Méthode générale")
# → "cauchy1847methode"
```

## CLI

```bash
# Validate
uv run python -m infrastructure.reference.citation.cli validate refs.bib --strict

# Re-format in canonical layout
uv run python -m infrastructure.reference.citation.cli format refs.bib

# Convert literature-search JSON → BibTeX
uv run python -m infrastructure.reference.citation.cli convert papers.json refs.bib
```

## LaTeX escaping

```python
from infrastructure.reference.citation import escape_latex, unescape_latex
escape_latex("Smith & Co")            # 'Smith \\& Co'
unescape_latex(r"Smith \& Co")        # 'Smith & Co'
```

The writer applies escaping automatically; you only need these helpers when
constructing values manually.

## Format Guarantees

The writer's output round-trips through the parser without semantic loss
and matches the exemplar `references.bib` byte-for-byte:

* 2-space field indent
* Trailing comma after every field except the last
* `pages={N--M}` (BibTeX em-dash) regardless of input form
* DOIs / URLs / years / volumes emitted verbatim
* Unicode preserved (Pandoc / XeLaTeX handle it natively)
* `book` / `phdthesis` / `techreport` / `misc` entries never get a stray
  `journal=` field
