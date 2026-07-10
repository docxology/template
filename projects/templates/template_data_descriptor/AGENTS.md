# template_data_descriptor - AGENTS.md

## Ground truth

Configuration lives in `manuscript/config.yaml`; dataset descriptor fixtures live in `data/`; reusable validation logic lives in `src/data_descriptor/`. Outputs are regenerated and must not be hand-edited.

## Commands

Run tests from the monorepo root:

```bash
uv run pytest projects/templates/template_data_descriptor/tests --cov=projects/templates/template_data_descriptor/src --cov-fail-under=90
uv run python scripts/pipeline/stage_01_test.py --project templates/template_data_descriptor --project-only
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_data_descriptor
```

## Contracts and boundaries

Keep scripts thin if project-local orchestration is added. Business logic belongs in `src/data_descriptor/`; tests use real fixture descriptors. Publication claims must stay bound to descriptor validity, schema completeness, field constraints, provenance, license state, metadata-only release manifests, and reproducibility TODO evidence.

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.
