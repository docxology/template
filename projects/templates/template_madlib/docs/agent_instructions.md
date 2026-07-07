# Agent Instructions — Template Madlib

## Operational Constraints

1. **Config owns the vocabulary.** All lexicon, section titles, method
   steps, and token values live in `manuscript/config.yaml` under
   `madlib:`. Never hard-code token values in source code.
2. **Keep `src/` pure.** Token expansion, lexicon parsing, and composition
   logic belong in `src/` — scripts only orchestrate.
3. **No hand-edited output.** Generated manuscript under `output/manuscript/`
   is disposable. Regenerate from source and config.
4. **QA probes come from config.** Every quality probe in the manuscript
   must correspond to a `madlib.quality_probes` entry.

## Workflow

All commands below assume the current directory is the monorepo root
(the `template/` checkout), matching the fully-qualified `--project`
and test-path forms used by README.md, AGENTS.md, and SKILL.md.

1. Edit lexicon or section structure in `manuscript/config.yaml`.
2. Run the analysis stage: `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_madlib`.
3. Verify: `uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90`.
