# Reference Module

## Purpose

The Reference module provides utilities for working with bibliographic
references in the format consumed by the template's PDF rendering pipeline
(`infrastructure/rendering/_pdf_combined_renderer.py` calling Pandoc with
`--natbib` plus the `pandoc-crossref` filter). It
sits opposite [`infrastructure/search/`](../search/) in the literature
workflow:

```mermaid
flowchart LR
    D[discover<br/>search] --> N[normalise<br/>Paper]
    N --> E[export<br/>citation]
    E --> PDF[PDF]

    classDef stage fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef out fill:#0f766e,stroke:#0f172a,color:#fff
    class D,N,E stage
    class PDF out
```

## Architecture

### `citation/` — BibTeX I/O

| File | Role |
|---|---|
| `models.py` | `BibEntry` and `BibDatabase` — ordered, validated records preserving field order for byte-stable round trips. |
| `escape.py` | LaTeX-special-character helpers; single-pass to avoid re-escaping inserted commands. |
| `bibtex_writer.py` | Render entries / databases. Pins the format to match `references.bib` exactly (2-space indent, trailing-comma rule, `--` page ranges, verbatim DOIs). |
| `bibtex_parser.py` | Hand-rolled state-machine parser. Forgiving about whitespace / quoting style; supports `{…}`, `"…"`, and bare numeric values; tolerates trailing commas; preserves field order. |
| `converter.py` | Bridge from `infrastructure.search.literature.Paper` to `BibEntry`. Generates citation keys in the exemplar's `<author><year><title-word>` style; routes venue → `journal` / `booktitle` / nothing based on entry type. |
| `cli.py` | `validate` / `format` / `convert` subcommands. |

## Key Features

### Byte-compatible BibTeX format

```python
from infrastructure.reference.citation import (
    BibEntry, BibDatabase, render_database, parse_bibfile
)

# Round-trip the exemplar — output matches input format byte-for-byte.
db = parse_bibfile("projects/template_code_project/manuscript/references.bib")
text = render_database(db)
# text contains: "@article{cauchy1847methode,\n  title={Méthode...},\n  ..."
```

### Paper → BibEntry conversion

```python
from infrastructure.reference.citation import paper_to_bibentry
from infrastructure.search.literature import Paper

paper = Paper(
    id="doi:10.1126/science.1213847",
    title="Reproducible research in computational science",
    authors=["Roger D Peng"],
    year=2011, doi="10.1126/science.1213847",
    venue="Science", venue_type="journal",
    volume="334", issue="6060", pages="1226-1227",
)
entry = paper_to_bibentry(paper)
# entry.citation_key == "peng2011reproducible"
# entry.entry_type   == "article"
# entry.fields["pages"] -> "1226-1227" (will be rendered as "1226--1227")
```

### Citation key generation

```python
from infrastructure.reference.citation import generate_citation_key

# Stop-words skipped, unicode folded.
generate_citation_key(
    authors=["Cauchy, Augustin-Louis"],
    year=1847,
    title="Méthode générale",
)
# → "cauchy1847methode"
```

## Testing

```bash
uv run pytest tests/infra_tests/reference/ -v
```

The test suite (105+ assertions) covers:

* Real round-trip through `projects/template_code_project/manuscript/references.bib`.
* Byte-exact format pinning so the writer cannot drift from the exemplar.
* Citation-key generation on stop-words, unicode, missing authors.
* CLI subcommands via real subprocess + direct `main()` calls.

No mocks — the CLI tests shell out, the parser tests use real file I/O.

## Configuration

No environment variables are required. The module is pure Python with no
external dependencies.

## Integration

The Reference module is consumed by:

* PDF rendering pipeline (Pandoc reads the emitted `.bib` via `--natbib`).
* Literature workflows (`infrastructure.search.literature` → `paper_to_bibentry`).
* Manuscript curation (validate / format `references.bib` in CI).

## Troubleshooting

### Round-trip drift

**Issue**: `render_database(parse_bibfile(path))` differs from the input file.

**Solutions**:
- Field values containing escaped LaTeX commands (e.g. user-typed `\\textbf{…}`)
  are unescaped on parse and re-escaped on render. The output is *equivalent*
  but may not be byte-identical to hand-formatted input.
- Commas / whitespace inside braced values are preserved literally.
- Open an issue with the offending entry — the parser is intentionally tight
  but pragmatic.

### Wrong entry type for source

**Issue**: An arXiv paper exported as `@article` when you wanted `@misc`.

**Solutions**:
- Pass `entry_type="misc"` to `paper_to_bibentry()` to override.
- For batch overrides, set `paper.venue_type` before conversion (see the
  `_SOURCE_TO_ENTRY_TYPE` table in `converter.py`).

### Citation key collision

**Issue**: Two papers in the same year with the same first author + title-word
produce identical keys.

**Solutions**:
- Pass `citation_key="custom"` to `paper_to_bibentry()`.
- Suffix manually after generation (e.g. `entry.citation_key += "a"`).

### Special characters in author names

**Issue**: Non-ASCII characters in `\author{…}` break LaTeX compilation.

**Solutions**:
- The exemplar uses bare unicode (`Méthode générale`) and relies on XeLaTeX /
  Pandoc to handle it. If you compile with classic pdfLaTeX, add
  `\usepackage[utf8]{inputenc}` to the preamble.

## Best Practices

### Prefer round-tripping over hand-editing

When sharing a `.bib` across multiple authors, run
`python -m infrastructure.reference.citation.cli format refs.bib` in a
pre-commit hook so style drift cannot hide real semantic conflicts in diffs.

### Treat citation keys as immutable

Once a key appears in a manuscript, don't regenerate it; pass the existing
key through `paper_to_bibentry(paper, citation_key=existing_key)` instead.

### Validate in CI

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/$PROJECT/manuscript/references.bib --strict
```

The `--strict` flag exits non-zero when entries are missing required fields
(per type — e.g. `article` requires title/author/year).

## See Also

- [README.md](README.md) — quick reference
- [SKILL.md](SKILL.md) — agent-oriented API
- [`citation/`](citation/) — BibTeX submodule
- [`infrastructure/search/`](../search/) — discovery side of the workflow
- [`infrastructure/publishing/`](../publishing/) — APA / MLA / human-facing
  citations
