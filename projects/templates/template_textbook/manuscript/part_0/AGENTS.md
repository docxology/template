# Part 0 — Authoring Contract (agents & authors)

This file restates the **per-chapter authoring contract** for the three chapters
in Part 0 (Orientation and Methods): [`orientation.md`](orientation.md),
[`core_methods.md`](core_methods.md), and
[`quantitative_foundations.md`](quantitative_foundations.md). The contract is
identical book-wide; only the labels and filenames differ per part. The
structural requirements are enforced by `src/textbook/constants.py`
(`REQUIRED_SECTION_HEADINGS`, `REQUIRED_TOKENS`, `STUB_MARKERS`) and checked by
`validate_chapter` plus `tests/test_manuscript_integrity.py`. Do not edit the
frozen engine; author the markdown to satisfy it.

## Every chapter in this part must contain

- **Labelled H1** with the section anchor: `# Title {#sec:part_0_<stem>}`.
- **A metadata badge:** `<!-- chapter-metadata-badge -->`.
- **A Study Blueprint** opened by `<!-- curriculum-scaffold-start -->`.
- **Learning Objectives** section.
- **One figure** with alt text and a crossref label: `{#fig:part_0_<stem>...}`.
- **A worked formalism:** a labelled equation `{#eq:...}` plus a parameter table
  `{#tbl:...}`.
- **An inline diagram:** a fenced ```mermaid block.
- **Closing sections:** Summary, Key Terms, Further Reading, Practice.

When drafting, leave nothing as `<!-- STUB -->`, `TODO:`, or `TKTK` — those are
the stub markers the quality gate counts and must reach zero in a filled chapter.

## Label and filename patterns for Part 0

| Item | Pattern | Examples (stems: `orientation`, `core_methods`, `quantitative_foundations`) |
|------|---------|------|
| Chapter file | `manuscript/part_0/<stem>.md` | `part_0/orientation.md` |
| Section anchor | `{#sec:part_0_<stem>}` | `{#sec:part_0_core_methods}` |
| Figure file | `part_0_<stem>.png` | `part_0_quantitative_foundations.png` |
| Figure label | `{#fig:part_0_<stem>}` | `{#fig:part_0_orientation}` |
| Equation label | `{#eq:part_0_<stem>...}` | `{#eq:part_0_quantitative_foundations}` |
| Table label | `{#tbl:part_0_<stem>...}` | `{#tbl:part_0_core_methods}` |
| Lab file | `manuscript/labs/part_0/lab_<stem>.md` | `labs/part_0/lab_orientation.md` |
| Question bank | `manuscript/questions/part_0/q_<stem>.md` | `questions/part_0/q_core_methods.md` |

**Figure filename convention:** every per-chapter figure is named
`<part>_<stem>.png` — here `part_0_<stem>.png` — produced by
[`scripts/generate_figures.py`](../../scripts/generate_figures.py) into the
project figures output. The crossref label `{#fig:part_0_<stem>}` must match the
generated filename's stem so the reference resolves.

## Cross-reference & linking rules

- **Crossrefs are pandoc-crossref only:** `[@fig:...]`, `[@tbl:...]`,
  `[@eq:...]`, `[@sec:...]`. Never hand-number a figure, table, equation, or
  section.
- **Citations** use `[@key]` and must resolve in
  [`../references.bib`](../references.bib). Available keys: `smith2020foundations`,
  `doe2019methods`, `lee2021systems`, `garcia2022dynamics`, `patel2018models`,
  `nguyen2023synthesis`, `kim2020data`, `brown2017principles`,
  `wilson2021analysis`, `taylor2019theory`.
- **Glossary links** use `[**term**](#gl:<anchor>)`. Valid anchors: `system`,
  `model`, `parameter`, `variable`, `equilibrium`, `feedback`, `gradient`,
  `threshold`, `network`, `dynamics`, `emergence`, `regulation`, `boundary`,
  `state`, `observable`.
- **Worked formalisms** should draw on the tested functions in
  `src/textbook/models.py` (e.g. `logistic_growth`, `saturating_response`,
  `exponential_decay`, `half_life`, `linear_fit`, `descriptive_statistics`,
  `normalize_unit_interval`) rather than introducing untested math.

## Tooling

- Use **uv**, never pip/npm.
- Tests: `uv run --extra dev python -m pytest`.
- Generate figures/diagrams via the thin orchestrators in
  [`../../scripts/`](../../scripts/); do not put computation in scripts.
- Run the chapter gate with
  [`scripts/audit_textbook_quality.py`](../../scripts/audit_textbook_quality.py).

See also: this part's [README](README.md), the repo-wide
[Authoring Guide](../appendices/appendix_authoring_guide.md), and the
[Notation appendix](../appendices/appendix_notation.md).
