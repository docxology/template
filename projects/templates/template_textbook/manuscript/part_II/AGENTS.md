# AGENTS — Part II (Core Systems)

Authoring contract for the three chapters in this directory:
[`systems_overview.md`](systems_overview.md),
[`dynamics_and_change.md`](dynamics_and_change.md),
[`regulation_and_control.md`](regulation_and_control.md).

This restates the book-wide contract as it applies to Part II. The structural
rules below are checked by [`scripts/audit_textbook_quality.py`](../../scripts/audit_textbook_quality.py)
and `tests/test_manuscript_integrity.py`; keep them intact while you replace the
`<!-- STUB -->`, `TODO:`, and `TKTK` markers with real content.

## Per-chapter required elements

Every chapter in this part MUST contain, in order:

1. **Labelled H1** — `# <Chapter Title> {#sec:part_II_<stem>}` where `<stem>` is the
   file name without `.md` (e.g. `# Systems Overview {#sec:part_II_systems_overview}`).
2. **Metadata badge** — the `<!-- chapter-metadata-badge -->` marker.
3. **Study Blueprint** — opened by `<!-- curriculum-scaffold-start -->`.
4. **Learning Objectives** — a short objective list for the chapter.
5. **One figure** — a `![alt text](../../output/figures/part_II_<stem>.png){#fig:part_II_<stem>}` reference with real
   alt text, pointing at the chapter's generated image (see filename convention).
6. **A worked formalism** — a numbered equation `{#eq:...}` plus a parameter table
   `{#tbl:...}`. Reuse the tested formalisms in
   [`src/textbook/models.py`](../../src/textbook/models.py) where they fit this part
   (e.g. `logistic_growth`, `exponential_decay`, `half_life`, `saturating_response`).
7. **An inline Mermaid diagram** — a fenced ```mermaid block.
8. **Closing sections** — `Summary`, `Key Terms`, `Further Reading`, `Practice`.

## Label and reference conventions

- **Section labels:** `{#sec:part_II_<stem>}` on the H1.
- **Figure labels:** `{#fig:part_II_<stem>}`; **table labels** `{#tbl:...}`;
  **equation labels** `{#eq:...}`.
- **Cross-references use pandoc-crossref only** — `[@fig:..]`, `[@tbl:..]`,
  `[@eq:..]`, `[@sec:..]`. Never hand-number figures, tables, equations, or sections.
- **Lab files:** `../labs/part_II/lab_<stem>.md`. **Question banks:**
  `../questions/part_II/q_<stem>.md`. The display titles for both are derived from
  the parent chapter title by [`src/textbook/toc.py`](../../src/textbook/toc.py); do
  not retitle them by hand.

## Figure filename convention

Each chapter's figure is `<part>_<stem>.png` — for Part II:

| Chapter stem | Figure file |
| --- | --- |
| `systems_overview` | `part_II_systems_overview.png` |
| `dynamics_and_change` | `part_II_dynamics_and_change.png` |
| `regulation_and_control` | `part_II_regulation_and_control.png` |

These placeholders are generated deterministically by
[`scripts/generate_figures.py`](../../scripts/generate_figures.py). When you replace
a placeholder with a real figure, keep the exact `<part>_<stem>.png` name so the
`[@fig:part_II_<stem>]` reference and the audit gate continue to resolve.

## Citations and glossary

- **Citations** use `[@key]` and MUST resolve in [`../references.bib`](../references.bib).
  Available keys: `smith2020foundations`, `doe2019methods`, `lee2021systems`,
  `garcia2022dynamics`, `patel2018models`, `nguyen2023synthesis`, `kim2020data`,
  `brown2017principles`, `wilson2021analysis`, `taylor2019theory`.
- **Glossary links** use `[**term**](#gl:<anchor>)` against the anchors defined in
  [`../glossary.md`](../glossary.md): `system`, `model`, `parameter`, `variable`,
  `equilibrium`, `feedback`, `gradient`, `threshold`, `network`, `dynamics`,
  `emergence`, `regulation`, `boundary`, `state`, `observable`. The Part II chapters
  lean naturally on `system`, `state`, `dynamics`, `equilibrium`, `feedback`,
  `regulation`, `threshold`, and `boundary`.

## Tooling

- Use `uv` only — never `pip`/`npm`.
- Run tests with `uv run --extra dev python -m pytest`.
- Regenerate figures and diagrams through the scripts in
  [`../../scripts/`](../../scripts/), not by editing generated PNGs directly.
- Add or reorder chapters by editing [`../config.yaml`](../config.yaml), then run
  [`scripts/scaffold_chapter.py`](../../scripts/scaffold_chapter.py) to create any
  missing stubs in the correct shape.

Markdown only; the sole permitted raw HTML is `<details>`. Use relative links
between manuscript documents, as above.
