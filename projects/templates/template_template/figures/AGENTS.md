# AGENTS — figures

Automation guidance for `figures` in the `template_template` exemplar.

- This directory holds **no PNGs**. Architecture figures are regenerated
  on every run by Stage 02 analysis (`scripts/generate_architecture_viz.py` →
  `src/template_template/architecture_viz.py:generate_all_architecture_figures`)
  and written to `../output/figures/*.png`, which is tracked as public output
  when files stay below the size ceiling.
- The manuscript references those rendered figures via `../output/figures/*.png`,
  matching the sibling exemplars (e.g. `template_code_project`). Do not commit
  hand-synced copies here; they drift from the live repository they depict.
- To regenerate: run the project analysis stage
  (`scripts/pipeline/stage_02_analysis.py`) or invoke
  `scripts/generate_architecture_viz.py` directly.
