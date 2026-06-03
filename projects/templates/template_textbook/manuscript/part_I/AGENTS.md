# AGENTS — Part I (Fundamentals)

Authoring contract for the three chapters in this directory:
`first_principles.md`, `building_blocks.md`, `structure_and_form.md`. Source of
truth for the part and its chapter list is [`../config.yaml`](../config.yaml)
(`parts:` → `part_I`); this file restates the per-chapter rules so an author or
agent can fill a stub without leaving the directory. The repo-wide
[Authoring Guide](../appendix_authoring_guide.md) is the long-form companion.

## Identifier patterns for this part

`part_I`'s `id` is `part_I`; each chapter's `<stem>` is its filename without the
`.md` extension (`first_principles`, `building_blocks`, `structure_and_form`).
Build every label from that stem — never hand-number anything.

| Element | Pattern | Examples for this part |
|---------|---------|------------------------|
| Section anchor (chapter H1) | `{#sec:part_I_<stem>}` | `{#sec:part_I_first_principles}`, `{#sec:part_I_building_blocks}`, `{#sec:part_I_structure_and_form}` |
| Figure label | `{#fig:part_I_<stem>}` | `{#fig:part_I_first_principles}` |
| Equation label | `{#eq:part_I_<stem>}` | `{#eq:part_I_building_blocks}` |
| Table label | `{#tbl:part_I_<stem>}` | `{#tbl:part_I_structure_and_form}` |
| Figure image file | `<part_id>_<stem>.png` | `part_I_first_principles.png`, `part_I_building_blocks.png`, `part_I_structure_and_form.png` |
| Lab file | `../labs/part_I/lab_<stem>.md` | `lab_first_principles.md` |
| Question bank file | `../questions/part_I/q_<stem>.md` | `q_first_principles.md` |

The figure image lives under the generated figures directory and is produced by
`scripts/generate_figures.py` from `src/visualization/`; reference it from the
chapter with the `{#fig:part_I_<stem>}` label and supply alt text.

## Per-chapter required elements

Every chapter in this part must contain, in this order:

1. **Labelled H1** — `# <Chapter Title> {#sec:part_I_<stem>}`. The title must
   match the `title:` for that chapter in `config.yaml`.
2. **Metadata badge** — the `<!-- chapter-metadata-badge -->` marker.
3. **Study Blueprint** — opened with `<!-- curriculum-scaffold-start -->`.
4. **Learning Objectives** — a short list of what the reader will be able to do.
5. **Worked formalism** — at least one labelled equation (`{#eq:part_I_<stem>}`)
   accompanied by a parameter table (`{#tbl:part_I_<stem>}`). Prefer one of the
   tested models in `src/textbook/models.py` so the math is computable.
6. **One figure** — `{#fig:part_I_<stem>}` with descriptive alt text, image file
   `part_I_<stem>.png`.
7. **Inline diagram** — a fenced ```mermaid block (sources live in
   `src/mermaid/`).
8. **Closing sections** — Summary, Key Terms, Further Reading, Practice.

## Cross-references, citations, glossary

- **Cross-refs** use pandoc-crossref only: `[@sec:…]`, `[@fig:…]`, `[@eq:…]`,
  `[@tbl:…]`. Never hand-number.
- **Citations** are `[@key]` and every key must resolve in
  [`../references.bib`](../references.bib) (e.g. `smith2020foundations`,
  `doe2019methods`, `lee2021systems`, `garcia2022dynamics`, `patel2018models`,
  `nguyen2023synthesis`, `kim2020data`, `brown2017principles`,
  `wilson2021analysis`, `taylor2019theory`).
- **Glossary links** are `[**term**](#gl:<anchor>)`; valid anchors include
  `system`, `model`, `parameter`, `variable`, `equilibrium`, `feedback`,
  `gradient`, `threshold`, `network`, `dynamics`, `emergence`, `regulation`,
  `boundary`, `state`, `observable`.

## Stub markers and verification

A chapter is incomplete while it contains any `<!-- STUB -->`, `TODO:`, or
`TKTK`. Replace these with real prose as you author. Markdown only — no raw HTML
except `<details>`. Use relative links between docs.

Verify before committing:

```bash
# Quality gate for the whole book (structural contract + stub accounting)
uv run --extra dev python scripts/audit_textbook_quality.py

# Manuscript integrity + engine tests
uv run --extra dev python -m pytest
```
