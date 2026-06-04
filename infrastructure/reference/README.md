# Reference Module

Bibliographic-reference workflows: read, write, and convert BibTeX records
that match the syntax of
[`projects/templates/template_code_project/manuscript/references.bib`](../../projects/templates/template_code_project/manuscript/references.bib)
(consumed by Pandoc with `--natbib` during PDF render — see
[`infrastructure/rendering/_pdf_combined_renderer.py`](../rendering/_pdf_combined_renderer.py)
line 225).

## Submodules

| Submodule | Purpose |
|---|---|
| [`citation`](citation/) | BibTeX I/O: `parse_bibfile`, `render_database`, `paper_to_bibentry`, `generate_citation_key`. |

## Quick Start

```python
from infrastructure.reference.citation import (
    parse_bibfile, render_database, write_bibfile,
    paper_to_bibentry, BibDatabase,
)
from infrastructure.search.literature import LiteratureClient, SearchQuery, ArxivBackend

# Read an existing bibliography.
db = parse_bibfile("projects/templates/template_code_project/manuscript/references.bib")
print(f"{len(db)} entries; first key = {db.keys()[0]}")

# Search for new references and append them.
result = LiteratureClient([ArxivBackend()]).search(SearchQuery(text="adam optimizer"))
for paper in result.papers:
    db.add(paper_to_bibentry(paper))

write_bibfile("output/references.bib", db)
```

## CLI

```bash
# Validate
uv run python -m infrastructure.reference.citation.cli validate refs.bib

# Re-format in canonical layout
uv run python -m infrastructure.reference.citation.cli format refs.bib

# Convert literature-search JSON → BibTeX
uv run python -m infrastructure.reference.citation.cli convert papers.json refs.bib
```

## Format Conventions

The writer's output is **byte-compatible** with the exemplar `references.bib`:

```bibtex
@article{cauchy1847methode,
  title={Méthode générale pour la résolution des systèmes d'équations simultanées},
  author={Cauchy, Augustin-Louis},
  journal={Comptes rendus hebdomadaires des séances de l'Académie des Sciences},
  volume={25},
  pages={536--538},
  year={1847}
}
```

* 2-space field indent
* Trailing comma after every field except the last
* `pages={N--M}` BibTeX em-dash (auto-normalised from `-` / `–` / `—`)
* Unicode preserved (Pandoc / XeLaTeX handle it natively)
* DOIs / URLs / years emitted verbatim without LaTeX escaping

## Testing

```bash
uv run pytest tests/infra_tests/reference/ -v
```

Tests follow the project's no-mocks policy: real `.bib` round-trips against
the actual `projects/templates/template_code_project/manuscript/references.bib`, real
subprocess invocations of the CLI, real temp-file I/O.

See [SKILL.md](SKILL.md) for the full agent-oriented API reference and
[AGENTS.md](AGENTS.md) for architecture / troubleshooting / best practices.
