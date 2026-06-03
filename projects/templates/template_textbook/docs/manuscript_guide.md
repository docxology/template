# Manuscript Guide

How the book is laid out, what every chapter must contain, and how numbering and
cross-references are computed rather than typed.

## Layout

The structure is declared in
[`manuscript/config.yaml`](../manuscript/config.yaml) and mirrored on disk:

```
manuscript/
  config.yaml        # the structure (parts → chapters → labs → questions)
  references.bib     # bibliography; every [@key] must resolve here
  glossary.md        # every [**term**](#gl:anchor) must resolve here
  part_0/            # Orientation and Methods
  part_I/            # Fundamentals
  part_II/           # Core Systems
  part_III/          # Applications and Synthesis
  labs/<part_id>/    # lab_<stem>.md, one per chapter
  questions/<part_id>/ # q_<stem>.md, one per chapter
  appendices/        # reference appendices (authoring guide, notation, …)
  assets/            # cover image, etc.
```

The current book has **four parts and twelve chapters**:

| Part | Title | Chapters |
| --- | --- | --- |
| 0 | Orientation and Methods | orientation, core_methods, quantitative_foundations |
| I | Fundamentals | first_principles, building_blocks, structure_and_form |
| II | Core Systems | systems_overview, dynamics_and_change, regulation_and_control |
| III | Applications and Synthesis | applied_models, case_studies, frontiers |

Each chapter `<stem>.md` has a matching lab
(`labs/<part_id>/lab_<stem>.md`) and question bank
(`questions/<part_id>/q_<stem>.md`). Lab and question display titles are derived
from the parent chapter title by [`src/textbook/toc.py`](../src/textbook/toc.py)
— the config lists only file names.

## The per-chapter contract

Every chapter must carry the elements below. They are enforced by
[`textbook.content.validate_chapter`](../src/textbook/content.py) against the
literal tokens and headings in
[`src/textbook/constants.py`](../src/textbook/constants.py), so this list is the
contract, not a summary of it.

- **Labelled H1** — `# <Title> {#sec:<part_id>_<stem>}`.
- **At least one figure** — `{#fig:...}` with descriptive alt text (an `<!-- alt: ... -->`
  comment alongside the `![]()` image).
- **Metadata badge** — `<!-- chapter-metadata-badge -->` followed by a level /
  read-time / lecture-time / prerequisites line.
- **Study Blueprint** — opened by `<!-- curriculum-scaffold-start -->`
  (big idea, core concepts, quantitative lens, data skill, misconception,
  primary lab, question bank, bridge to computation).
- **Learning Objectives** section.
- **A worked formalism** — at least one equation `{#eq:...}` *and* one parameter
  table `{#tbl:...}`.
- **An inline diagram** — a `` ```mermaid `` fenced block.
- **Closing sections** — `Summary`, `Key Terms`, `Further Reading`, `Practice`
  (the `REQUIRED_SECTION_HEADINGS`).

`STUB_MARKERS` (`<!-- STUB`, `TODO:`, `TKTK`) mark unwritten content; a fresh
scaffold is contract-complete but stub-heavy, and the authoring workflow is to
replace the stubs (see the [authoring guide](authoring_guide.md)).

## Numbering and cross-references

Numbering is **computed**, never hand-typed:

- Chapters number sequentially across the whole book; the order comes from the
  `parts` list in `config.yaml` and is resolved by
  [`textbook.toc.chapter_number`](../src/textbook/toc.py).
- Within the rendered document, **pandoc-crossref** assigns figure, table,
  equation, and section numbers from the `{#fig:...}`, `{#tbl:...}`,
  `{#eq:...}`, `{#sec:...}` labels.

Always reference, never number, in prose:

| To refer to a… | Write | Not |
| --- | --- | --- |
| Section / chapter | `[@sec:part_I_first_principles]` | "Chapter 4" |
| Figure | `[@fig:part_I_first_principles]` | "Figure 4.1" |
| Table | `[@tbl:...]` | "Table 2" |
| Equation | `[@eq:...]` | "Equation 3" |

If you hand-number, the rendered book will show dangling `??` once numbers
shift; the cross-ref keeps prose correct as the book grows.

## Citations and glossary

- Citations use `[@key]` and must resolve in
  [`references.bib`](../manuscript/references.bib). The contract keys are the ten
  in `CITATION_KEYS`: `smith2020foundations`, `doe2019methods`, `lee2021systems`,
  `garcia2022dynamics`, `patel2018models`, `nguyen2023synthesis`, `kim2020data`,
  `brown2017principles`, `wilson2021analysis`, `taylor2019theory`. Add real
  references to `references.bib` and keep `CITATION_KEYS` in sync as you replace
  the placeholders.
- Glossary links use `[**term**](#gl:<anchor>)` and must resolve in
  [`glossary.md`](../manuscript/glossary.md). The contract anchors are the
  fifteen `GLOSSARY_ANCHORS`: `system`, `model`, `parameter`, `variable`,
  `equilibrium`, `feedback`, `gradient`, `threshold`, `network`, `dynamics`,
  `emergence`, `regulation`, `boundary`, `state`, `observable`.

The manuscript-integrity tests fail if a chapter cites a key or links an anchor
that is not defined — see the [testing guide](testing_guide.md).

## Rendering

Rendering is handled by the monorepo's generic `infrastructure/` rendering stage
(pandoc + pandoc-crossref → PDF/HTML), driven by the same `config.yaml` for
layout, typography, and front-matter ordering. Figures must already exist under
`output/figures/` (run `generate_figures.py` first) so the chapters'
`![...](../figures/<part_id>_<stem>.png)` paths resolve. The numbering settings
live under `rendering:` in `config.yaml` (`number_chapters`, `number_figures`,
`number_equations`, `number_tables`, `toc_depth`).
