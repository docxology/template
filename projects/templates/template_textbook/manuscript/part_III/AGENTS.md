# Part III — Authoring Contract (Applications and Synthesis)

This file restates the per-chapter authoring contract for the three chapters in
Part III: **Applied Models** (`applied_models.md`), **Case Studies**
(`case_studies.md`), and **Frontiers and Open Problems** (`frontiers.md`). The
contract is identical for every chapter in the book; the structure is defined in
[`../config.yaml`](../config.yaml) and enforced by
`scripts/audit_textbook_quality.py` plus `tests/test_manuscript_integrity.py`.
The structural constants live in `src/textbook/constants.py`.

Do **not** edit `config.yaml`, the `src/` engine, `references.bib`, or
`glossary.md` — those are frozen. Author the prose and the placeholders inside
the chapter, lab, and question files only.

## Required elements in every Part III chapter

Each chapter must contain all of the following (the audit gate checks for them):

1. **Labelled H1** — the chapter title plus its section anchor:
   `# <Title> {#sec:part_III_<stem>}`.
2. **One figure** with a Pandoc-crossref label and alt text:
   `![caption](../../output/figures/part_III_<stem>.png){#fig:part_III_<stem> width=90%}`
   followed by an `<!-- alt: ... -->` comment.
3. **Metadata badge** — the `<!-- chapter-metadata-badge -->` marker and its
   level / read-time / prerequisites line.
4. **Study Blueprint** — opened by `<!-- curriculum-scaffold-start -->`.
5. **Learning Objectives** — a numbered list of measurable objectives.
6. **A worked formalism** — an equation with a label `{#eq:...}` and an
   accompanying parameter table labelled `{#tbl:...}`. Reuse the tested
   formalisms in `src/textbook/models.py` rather than inventing untested math.
7. **An inline ` ```mermaid ` diagram** describing the chapter's structure or
   workflow.
8. **Closing sections** — `Summary`, `Key Terms`, `Further Reading`, and
   `Practice`.

Stub markers that must be replaced before a chapter is considered filled:
`<!-- STUB -->`, `TODO:`, and `TKTK`.

## Label and filename patterns (Part III)

`<stem>` is the chapter file name without `.md` — one of `applied_models`,
`case_studies`, `frontiers`.

| Element | Pattern | Part III examples |
| ------- | ------- | ----------------- |
| Section anchor | `{#sec:part_III_<stem>}` | `sec:part_III_applied_models`, `sec:part_III_case_studies`, `sec:part_III_frontiers` |
| Figure label | `{#fig:part_III_<stem>}` | `fig:part_III_applied_models`, … |
| Figure file | `part_III_<stem>.png` (in `../figures/`) | `part_III_applied_models.png`, `part_III_case_studies.png`, `part_III_frontiers.png` |
| Equation label | `{#eq:part_III_<stem>_<name>}` | `eq:part_III_applied_models_growth` |
| Table label | `{#tbl:part_III_<stem>_<name>}` | `tbl:part_III_applied_models_params` |
| Lab file | `../labs/part_III/lab_<stem>.md` | `lab_applied_models.md`, … |
| Question bank | `../questions/part_III/q_<stem>.md` | `q_applied_models.md`, … |

## Cross-references, citations, and glossary

- **Never hand-number.** Refer to elements with pandoc-crossref syntax:
  `[@fig:...]`, `[@tbl:...]`, `[@eq:...]`, `[@sec:...]`. Synthesis chapters
  especially should cite earlier chapters by `[@sec:...]`.
- **Citations** use `[@key]` and must resolve in `references.bib`. Available
  keys: `smith2020foundations`, `doe2019methods`, `lee2021systems`,
  `garcia2022dynamics`, `patel2018models`, `nguyen2023synthesis`, `kim2020data`,
  `brown2017principles`, `wilson2021analysis`, `taylor2019theory`.
- **Glossary terms** link as `[**term**](#gl:<anchor>)`. Valid anchors:
  `system`, `model`, `parameter`, `variable`, `equilibrium`, `feedback`,
  `gradient`, `threshold`, `network`, `dynamics`, `emergence`, `regulation`,
  `boundary`, `state`, `observable`.

## Verify before you commit

```bash
uv run python scripts/scaffold_chapter.py          # create missing stubs
uv run python scripts/generate_figures.py          # produce part_III_<stem>.png
uv run python scripts/audit_textbook_quality.py    # structural gate
uv run --extra dev python -m pytest                # full suite
```

For the full how-to, see the [Authoring Guide](../appendices/appendix_authoring_guide.md)
and the part overview in [`README.md`](README.md).
