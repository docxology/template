# template_bibliography

**Type:** bibliography
**Version:** 1.0
**License:** CC0-1.0

A curated research bibliography — exemplar template for managing BibTeX references alongside a flat CSV export.

---

## Contents

```
template_bibliography/
├── fonds.yaml              ← manifest
├── AGENTS.md               ← agent documentation
├── README.md               ← this file
├── .gitignore
└── data/
    ├── references.bib      ← BibTeX source of truth
    └── references.csv      ← flat CSV export
```

---

## Usage

### As a template

```bash
cp -r fonds/templates/template_bibliography fonds/my_bibliography
# Edit fonds.yaml, README.md, and replace data/ with your references
```

### Citing in a project

Projects consume the fond directly from its path — there is no `project.yaml`
front-matter mechanism. Reference the BibTeX file directly, e.g. in Pandoc:

```bash
pandoc paper.md --bibliography ../../fonds/my_bibliography/data/references.bib -o paper.pdf
```

Or in LaTeX:

```latex
\bibliography{../../fonds/my_bibliography/data/references}
```

---

## CSV columns

| Column | Description |
|---|---|
| `key` | BibTeX cite key (unique) |
| `type` | Entry type (`article`, `book`, `inproceedings`, …) |
| `title` | Full title |
| `author` | Author(s), semicolon-separated |
| `year` | Publication year |
| `journal` | Journal or venue |
| `doi` | DOI (if available) |

---

## Sample entries

See `data/references.bib` and `data/references.csv` for 8 example entries spanning foundational ML/AI papers.
