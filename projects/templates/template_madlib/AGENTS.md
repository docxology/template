# Template Madlib Agent Notes

`template_madlib` is a public canonical exemplar for deterministic token injection, conditional IMRAD composition, design-principle reporting, operational phase tracing, cover/pipeline visual explanation, configured-field origin visualization, evaluation criteria, QA probes, failure-mode reporting, authoring obligations, and source-owned manuscript hydration.

## Layer Contract

| Surface | Rule |
| --- | --- |
| `src/` | Domain logic only. Parse config, plan tokens, compose sections, write artifacts, and generate variables here. Do not import `infrastructure.*`. |
| `scripts/` | Thin wrappers. They may put repo/project paths on `sys.path`, call `src/`, and delegate manuscript injection to shared infrastructure. |
| `manuscript/` | Token shells plus metadata. Section prose, titles, and tables must resolve from generated variables, not hand-edited output. |
| `tests/` | Real config/data/files/subprocesses only; no mocks. |
| `output/` | Regeneratable and ignored. Never treat generated Markdown, PDFs, reports, or figures as source of truth. |

## Edit Rules

- Add vocabulary in `manuscript/config.yaml` under `madlib.lexicon`.
- Add new manuscript shape controls under `section_titles`, `narrative_moves`, `method_protocol`, `design_principles`, `pipeline_phases`, `evaluation_criteria`, `quality_probes`, `failure_modes`, `authoring_obligations`, `visualizations`, `audit_rules`, or `contribution_claims`.
- Keep method changes config-owned. A generated Methods claim needs a `method_protocol` row, a `pipeline_phases` row when it is operational, a QA probe or failure mode when it can fail, and claim-ledger evidence when it supports a claim.
- Review-packet, token-invariant, claim-ledger, and fork-migration language belongs in config plus `src/composition_*.py` / `src/figure_specs.py`; do not hide those obligations in generated output or freeform docs only.
- Change `src/config.py` only when the schema changes, and cover new validation behavior in `tests/test_config.py`.
- Change `src/composition_sections.py`, `src/composition_tables.py`, or `src/composition_figures.py` when generated manuscript body or Markdown evidence tables change.
- Keep manuscript figures behind generated figure-group variables; do not hard-code image markdown in section shells.
- Add new manuscript placeholders only after adding variables in `src/manuscript_variables.py` and coverage in `tests/test_manuscript_variables.py`.
- Keep publication claims local unless a real DOI, release, or external validation exists.
- Regenerate output through Stages 02-05 after source or config edits; do not hand-edit generated Markdown, PDFs, HTML, slides, figures, reports, or copied deliverables.

Decision memory and verifier hardening follow [`../../../docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## Verification

```bash
uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_madlib
uv run python scripts/pipeline/stage_03_render.py --project templates/template_madlib
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_madlib
```

A clean validation run should report figure registry, evidence registry, design overlays, and artifact manifest as passed.

## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-madlib/SKILL.md`](.agents/skills/template-madlib/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.

## Publishing

- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Publishing module reference](../../../infrastructure/publishing/README.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md) · [Archival targets](../../../docs/maintenance/archival-targets.md)
