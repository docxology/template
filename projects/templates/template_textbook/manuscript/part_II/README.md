# Part II — Core Systems

> Theme (from [`../config.yaml`](../config.yaml)): the working heart of the book. Part I established the fundamentals; **Part II assembles them into whole systems and shows how those systems behave, change, and stay within bounds.** Each chapter moves from describing a system, to tracing how it evolves over time, to explaining how it is kept stable.

This part is the third of four (`part_0` → `part_I` → **`part_II`** → `part_III`). Chapters are numbered automatically across the whole book by [`src/textbook/toc.py`](../../src/textbook/toc.py) from the order in `config.yaml`; never hand-number them here.

## Chapters in this part

Each chapter ships as a fillable stub carrying the full authoring contract (labelled H1, figure, metadata badge, Study Blueprint, Learning Objectives, worked formalism, Mermaid diagram, and the Summary / Key Terms / Further Reading / Practice sections). Replace the `<!-- STUB -->`, `TODO:`, and `TKTK` markers as you author; the quality gate counts them down to zero.

| Chapter | File | Stub theme to fill | Lab | Question bank |
| --- | --- | --- | --- | --- |
| Systems Overview | [`systems_overview.md`](systems_overview.md) | Define what a **system** is for this domain — its boundary, components, and the observables that characterise it as a whole. | [`lab_systems_overview.md`](../labs/part_II/lab_systems_overview.md) | [`q_systems_overview.md`](../questions/part_II/q_systems_overview.md) |
| Dynamics and Change | [`dynamics_and_change.md`](dynamics_and_change.md) | Trace how the system's **state** evolves over time — rates, trajectories, equilibria, and the formalisms that describe motion and decay. | [`lab_dynamics_and_change.md`](../labs/part_II/lab_dynamics_and_change.md) | [`q_dynamics_and_change.md`](../questions/part_II/q_dynamics_and_change.md) |
| Regulation and Control | [`regulation_and_control.md`](regulation_and_control.md) | Explain how the system is held within bounds — **feedback**, thresholds, set-points, and the control structures that maintain stability. | [`lab_regulation_and_control.md`](../labs/part_II/lab_regulation_and_control.md) | [`q_regulation_and_control.md`](../questions/part_II/q_regulation_and_control.md) |

## How this part fits the whole

- **Reads from one source.** The chapter list, titles, and ordering above are mirrors of the `part_II` block in [`../config.yaml`](../config.yaml). To add, reorder, or disable a chapter, edit `config.yaml` and then run [`scripts/scaffold_chapter.py`](../../scripts/scaffold_chapter.py) to materialise any missing stub files — do not create chapter files by hand.
- **Figures are pre-wired.** Each chapter has a deterministic placeholder figure named `<part>_<stem>.png` (here: `part_II_systems_overview.png`, `part_II_dynamics_and_change.png`, `part_II_regulation_and_control.png`), produced by [`scripts/generate_figures.py`](../../scripts/generate_figures.py). Swap the placeholder for a real figure without renaming it.
- **The contract is enforced.** [`scripts/audit_textbook_quality.py`](../../scripts/audit_textbook_quality.py) and `tests/test_manuscript_integrity.py` check that every chapter keeps its required headings, one labelled figure, citations that resolve in [`references.bib`](../references.bib), and glossary links into [`glossary.md`](../glossary.md).

See [`AGENTS.md`](AGENTS.md) in this directory for the per-chapter authoring contract and the exact label and filename conventions used throughout Part II.
