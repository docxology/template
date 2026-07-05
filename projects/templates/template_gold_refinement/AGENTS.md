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
| Source-owned equation registry | `src/formalisms.py` |
| Scientific-integrity dimensions and evidence tiers | `src/integrity.py` |
| Figure specs, layouts, SVG output, and quality report | `src/figures/` (`FIGURE_SPECS` in `_common.py`) |
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
| `output/` | Regeneratable artifacts. Never hand-edit generated Markdown, PDFs, reports, or figures; update the source owner and rerun the pipeline. |

## Visualization Contract

All 12 public figure labels are owned by `src/figures/__init__.py::FIGURE_SPECS`.
Each spec must declare `name`, `label`, `path`, `svg_path`, `caption`,
`generated_by`, `data_sources`, and `visual_encoding`. `generate_all_figures()`
must write PNG and SVG companions plus `output/figures/figure_registry.json`
and `output/reports/figure_quality_report.json`.

Graph-like visuals are generated from deterministic NetworkX graphs:

- `build_provenance_flow_graph()` for ore → stage → certification flow
- `build_formalism_traceability_graph()` for formalism → equation → source
- `build_implementation_circuit_graph()` for config/code/artifact/gate wiring
- `build_claim_evidence_topology()` for claim → evidence → boundary topology

Quantitative visuals must use source-owned encodings: nines transform for
late-stage purity, source-tier colors for integrity risk, and count/percentage
labels for evidence tiers. Keep manuscript figure variables pointed at PNG
paths; SVG is a companion technical artifact.

## Scientific-Integrity Contract

`output/reports/claim_support_registry.json` is the project-local contribution
claim assay. `output/reports/evidence_registry.json` is reserved for the shared
template evidence validator. Do not overwrite one with the other. Manuscript
claims should cite generated variables or registries instead of hand-maintained
numbers.

## Edit Rules

- Add vocabulary in `manuscript/config.yaml` under `gold_refinement.lexicon`.
- Add refinement stages or modify purity targets in `src/refinery.py` and
  `src/purity.py` together — purity must increase monotonically across stages.
- Change `src/config.py` only when the schema changes, and cover new validation
  behavior in `tests/test_config.py`.
- Keep manuscript figures behind generated figure-group variables.
- Add or rename figures only by editing `FIGURE_SPECS`, generator functions,
  manuscript variables, and registry/quality tests together.
- Add equation-backed claims through `src/formalisms.py`, not by hand-numbering
  equations in manuscript prose.
- Add integrity claims through `src/integrity.py` and the claim ledger before
  strengthening manuscript language.
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
uv run python -m infrastructure.validation.cli prerender \
  projects/templates/template_gold_refinement/manuscript --repo-root .
uv run python -m infrastructure.validation.cli evidence \
  projects/templates/template_gold_refinement \
  --manuscript-dir projects/templates/template_gold_refinement/manuscript \
  --fail-on-issues
```


## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-gold-refinement/SKILL.md`](.agents/skills/template-gold-refinement/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.

## Parent Docs

- Template root: [`../../../AGENTS.md`](../../../AGENTS.md)
- Publishing guide: [`../../../docs/guides/publishing-guide.md`](../../../docs/guides/publishing-guide.md) · Publishing module reference: [`../../../infrastructure/publishing/README.md`](../../../infrastructure/publishing/README.md) · Zenodo DOI strategy: [`../../../docs/guides/zenodo-doi-strategy.md`](../../../docs/guides/zenodo-doi-strategy.md) · Archival targets: [`../../../docs/maintenance/archival-targets.md`](../../../docs/maintenance/archival-targets.md)
- Memory and decision records: [`../../../docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md)
