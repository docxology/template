---
title: "Manuscript directory: code_project"
type: "manuscript_guide"
version: "2.1"
---

# Manuscript (`projects/code_project/manuscript/`)

Repository-wide agent rules for this exemplar live in [`../docs/agent_instructions.md`](../docs/agent_instructions.md). This file covers **manuscript-specific** editing and how these files connect to the build.

## Contents

| File / pattern | Role |
| --- | --- |
| `00_abstract.md` … `07_scope_and_related_work.md` | Section sources combined by the renderer |
| `SYNTAX.md` | Citation, figure, and cross-reference syntax |
| `config.yaml`, `config.yaml.example` | Paper metadata and pipeline options |
| `preamble.md` | LaTeX preamble shared by PDF output |
| `references.bib` | Bibliography |

Variable placeholders (e.g. `{{CONFIG_*}}`, `{{RESULT_*}}`) are filled from pipeline data; see [`../scripts/z_generate_manuscript_variables.py`](../scripts/z_generate_manuscript_variables.py) and generated JSON under `projects/code_project/output/data/`.

## RASP conventions (short)

1. Avoid boilerplate closers such as “In summary” / “In conclusion” at the end of sections unless the section genuinely needs them.
2. Figures and numbers in `03_results.md` must match what `scripts/optimization_analysis.py` writes (paths under `projects/code_project/output/figures/` and related CSV/JSON).
3. When referencing template code, prefer concrete paths or URLs (e.g. [`infrastructure/core`](https://github.com/docxology/template/tree/main/infrastructure/core)) over vague module dotted paths alone.

## Infrastructure coupling (scripts, not `src/`)

Orchestrators under `projects/code_project/scripts/` should use `infrastructure.core.logging.utils.get_logger(__name__)` (same pattern as `optimization_analysis.py`). Scientific checks should go through `infrastructure.scientific` helpers where applicable.

## Workflow when changing behavior and prose

1. Update the mathematical or experimental description in `02_methodology.md` / `05_experimental_setup.md` as needed.
2. Add or extend tests in `projects/code_project/tests/test_optimizer.py` (there is no separate `tests/integration/` tree in this project).
3. Regenerate analysis outputs, then refresh manuscript sections that cite numbers or figure filenames.
4. From the **repository root**:

```bash
uv run python projects/code_project/scripts/optimization_analysis.py
uv run python scripts/03_render_pdf.py --project code_project
```

Final deliverables appear under `output/code_project/` after `scripts/05_copy_outputs.py` (working files remain under `projects/code_project/output/` during the run).

## See also

- [`README.md`](README.md) — Quick orientation
- [`../docs/rendering_pipeline.md`](../docs/rendering_pipeline.md) — Manuscript → PDF flow
