# Part III — Applications and Synthesis

Part III is where the book pays off. Having established methods (Part 0),
fundamentals (Part I), and core systems (Part II), this part turns the machinery
outward: it applies the formalisms to concrete models, grounds them in worked
case studies, and surveys the open edge of the field. Treat it as the
"so what" of the textbook — the place where a reader sees the theory do work and
decides what to study next.

This part contains three chapters. Chapter numbers run sequentially across the
whole book, so Part III holds **Chapters 10–12**. Each chapter ships with a
matching hands-on **lab** and a **question bank**; fill all three together so the
chapter, its practice, and its assessment stay in sync.

> **This is a template.** Every chapter below is a stub built from
> [`../config.yaml`](../config.yaml). The prose, objectives, figures, and
> citations are placeholders marked with `<!-- STUB -->`, `TODO:`, or `TKTK`.
> Your job as author is to replace them. Start with the
> [Authoring Guide](../appendix_authoring_guide.md), keep the per-chapter
> contract in [`AGENTS.md`](AGENTS.md) open, and verify your work with
> `scripts/audit_textbook_quality.py`.

## Chapters in this part

| # | Chapter | Stub theme | Chapter | Lab | Question bank |
| - | ------- | ---------- | ------- | --- | ------------- |
| 10 | Applied Models | Put the formalisms to work: parameterise, fit, and interpret models on real problems. | [applied_models.md](applied_models.md) | [lab_applied_models.md](../labs/part_III/lab_applied_models.md) | [q_applied_models.md](../questions/part_III/q_applied_models.md) |
| 11 | Case Studies | End-to-end worked examples that carry a problem from data to defended conclusion. | [case_studies.md](case_studies.md) | [lab_case_studies.md](../labs/part_III/lab_case_studies.md) | [q_case_studies.md](../questions/part_III/q_case_studies.md) |
| 12 | Frontiers and Open Problems | Survey the unsettled edge: what is unknown, why it is hard, and where to push next. | [frontiers.md](frontiers.md) | [lab_frontiers.md](../labs/part_III/lab_frontiers.md) | [q_frontiers.md](../questions/part_III/q_frontiers.md) |

## How this part fits together

- **Applied Models** reuses the worked formalisms from `src/textbook/models.py`
  (logistic growth, saturating response, exponential decay, linear fits,
  descriptive statistics) and shows them solving a stated problem rather than
  illustrating a definition.
- **Case Studies** chains those models into complete narratives — each study
  should reference earlier chapters with `[@sec:...]` so the synthesis is
  explicit, not implied.
- **Frontiers** deliberately leaves questions open. It is the one chapter where
  honest "we don't know" is the correct content; cite the literature with
  `[@key]` and point readers toward the further-reading trail.

## Authoring this part

1. Read the shared contract in [`AGENTS.md`](AGENTS.md) before editing any
   chapter — it lists every required section and label.
2. Materialise any missing stub files with
   `uv run python scripts/scaffold_chapter.py` (it reads `config.yaml` and
   creates chapter/lab/question stubs in the correct shape).
3. Generate this part's figures with
   `uv run python scripts/generate_figures.py`; per-chapter placeholders are
   named `part_III_<stem>.png`.
4. Validate with `uv run python scripts/audit_textbook_quality.py` and run the
   suite with `uv run --extra dev python -m pytest`.

See also: [`../README.md`](../README.md) (book-level overview) and the other
parts — [Part 0](../part_0/README.md), [Part I](../part_I/README.md),
[Part II](../part_II/README.md).
