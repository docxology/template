# Manuscript Editing Contract

This file is the contract for **editing manuscript content** (chapters, labs,
question banks, glossary). It restates the rules the engine and tests enforce.
Violating any of them fails `scripts/audit_textbook_quality.py` or
`tests/test_manuscript_integrity.py`. The structure of the book lives in
[`config.yaml`](config.yaml); the syntax for each element lives in
[`SYNTAX.md`](SYNTAX.md).

## Golden Rules

1. **`config.yaml` is the single source of truth.** To add or remove a chapter,
   part, lab, or question bank, edit `config.yaml` first, then run
   `scripts/scaffold_chapter.py` to materialise any missing stub files.
2. **Never hand-number.** Chapters, figures, tables, equations, sections, labs,
   and question banks are referenced by label and numbered at render time by
   `pandoc-crossref`.
3. **Never retype mathematics in prose or scripts.** Each worked equation is a
   tested function in `textbook.models` (e.g. `logistic_growth`,
   `saturating_response`, `exponential_decay`, `half_life`, `linear_fit`,
   `descriptive_statistics`, `normalize_unit_interval`). Show the equation, then
   call the function.
4. **Stubs are tracked.** Author-specific gaps are marked `<!-- STUB -->`,
   `TODO:`, or `TKTK`. The quality audit counts them; a finished chapter has none.
5. **Markdown only.** No raw HTML except `<details>`. HTML comments
   (`<!-- ... -->`) are used for stubs, alt text, and metadata badges.

## Required Elements of Every Chapter

A chapter file (`part_<label>/<stem>.md`) MUST contain, in roughly this order:

- **A labelled H1 heading:** `# Title {#sec:<part>_<stem>}`
- **One figure** with descriptive caption and an `<!-- alt: ... -->` comment:
  `![caption](../output/figures/<part>_<stem>.png){#fig:<part>_<stem> width=90%}`
- **A metadata badge:** the `<!-- chapter-metadata-badge -->` marker followed by a
  blockquote (level, read time, lecture time, prerequisites).
- **A Study Blueprint** wrapped in
  `<!-- curriculum-scaffold-start -->` … `<!-- curriculum-scaffold-end -->`.
- **Learning Objectives:** a `## Learning Objectives` section with a numbered
  list.
- **A worked formalism:** a display equation `$$ … $$ {#eq:<part>_<stem>_model}`
  plus a parameter table `{#tbl:<part>_<stem>_parameters}`, with prose pointing to
  the tested function in `textbook.models`.
- **An inline Mermaid diagram:** a fenced ` ```mermaid ` block.
- **Closing sections:** `## Summary`, `## Key Terms`, `## Further Reading`,
  `## Practice` (the Practice section links to the chapter's lab and question
  bank).

Labs and question banks have their own required headings (`{#sec:lab_<part>_<stem>}`
and `{#sec:q_<part>_<stem>}`); scaffold them with `scripts/scaffold_chapter.py`
rather than by hand.

## Cross-Reference Rules (pandoc-crossref)

- Reference figures with `[@fig:...]`, tables with `[@tbl:...]`, equations with
  `[@eq:...]`, and sections with `[@sec:...]`.
- Define the target before (or near) you reference it: a `[@fig:x]` reference with
  no `{#fig:x}` definition renders as a dangling `??`. The integrity test requires
  the **definition**, not merely the reference.
- Labels follow the pattern `<part>_<stem>` (e.g. `part_II_dynamics_and_change`).

## Citation Rules

- Cite with `[@key]`; multiple citations with `[@a; @b]`.
- Every `[@key]` MUST resolve in [`references.bib`](references.bib). The valid keys
  are: `smith2020foundations`, `doe2019methods`, `lee2021systems`,
  `garcia2022dynamics`, `patel2018models`, `nguyen2023synthesis`, `kim2020data`,
  `brown2017principles`, `wilson2021analysis`, `taylor2019theory`.
- To cite a new source, add the entry to `references.bib` first.

## Glossary Rules

- Link a glossary term with `[**term**](#gl:<anchor>)`.
- Valid anchors: `system`, `model`, `parameter`, `variable`, `equilibrium`,
  `feedback`, `gradient`, `threshold`, `network`, `dynamics`, `emergence`,
  `regulation`, `boundary`, `state`, `observable`.
- These anchors must match `src/textbook/constants.py:GLOSSARY_ANCHORS`. To add a
  term, add it to [`glossary.md`](glossary.md) **and** to `constants.py`.

## Before You Commit

```bash
uv run python scripts/audit_textbook_quality.py --project templates/template_textbook
uv run --extra dev python -m pytest projects/templates/template_textbook/tests/ -v
```
