# AGENTS.md — template_gold_refinement

Public canonical exemplar mapping gold-refining metallurgy onto scientific
manuscript composition via mega-madlib token injection.

## Ground Truth

| Surface | Source of truth |
| --- | --- |
| Refinery stages and purity targets | `src/refinery.py` |
| Karat grading and purity computation | `src/purity.py` |
| Mega-madlib config schema | `src/config.py` |
| Token selection (deterministic digest) | `src/composition.py` |
| Manuscript variable map | `src/manuscript_variables.py` |
| Experiment parameters and metadata | `manuscript/config.yaml` |
| Open follow-up scope | `TODO.md` |

Generated counts and claim numbers belong in `output/data/manuscript_variables.json`
and hydrated manuscript output, not in hand-authored prose.

## Layer Contract

| Surface | Rule |
| --- | --- |
| `src/` | Domain logic only. Refinery, purity, config, composition, and variable generation here. Do not import `infrastructure.*`. |
| `scripts/` | Thin orchestrators. They may put repo/project paths on `sys.path`, call `src/`, and delegate manuscript injection to shared infrastructure. |
| `manuscript/` | Token shells plus metadata. Section prose, titles, and tables must resolve from generated variables. |
| `tests/` | Real config/data/files only; no mocks. |
| `output/` | Regeneratable and ignored. Never treat generated Markdown, PDFs, or figures as source of truth. |

## Edit Rules

- Add vocabulary in `manuscript/config.yaml` under `gold_refinement.lexicon`.
- Add refinement stages or modify purity targets in `src/refinery.py` and
  `src/purity.py` together — purity must increase monotonically across stages.
- Change `src/config.py` only when the schema changes, and cover new validation
  behavior in `tests/test_config.py`.
- Keep manuscript figures behind generated figure-group variables.
- Add new manuscript placeholders only after adding variables in
  `src/manuscript_variables.py` and coverage in `tests/test_manuscript_variables.py`.
- Regenerate output through Stages 02-05 after source or config edits.

## Verification

```bash
uv run pytest projects/templates/template_gold_refinement/tests/ \
  --cov=projects/templates/template_gold_refinement/src --cov-fail-under=90
uv run python scripts/02_run_analysis.py --project templates/template_gold_refinement
uv run python scripts/03_render_pdf.py --project templates/template_gold_refinement
uv run python scripts/04_validate_output.py --project templates/template_gold_refinement
```

## Parent Docs

- Template root: [`../../../AGENTS.md`](../../../AGENTS.md)
- Publishing guide: [`../../../docs/guides/publishing-guide.md`](../../../docs/guides/publishing-guide.md)
