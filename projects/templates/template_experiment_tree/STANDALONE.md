# STANDALONE — template_experiment_tree

## Purpose
Living research record with a version-controlled experiment tree with frozen nodes.

## Clean copy
```bash
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_experiment_tree --dest projects/working/my_record --new-name my_research
```

## Intentional dependencies (monorepo-only)
- None: the engine is project-local (`src/template_experiment_tree`) with no
  `infrastructure/` imports — the exemplar is standalone by construction.
- Fork config: copy `manuscript/config.yaml.example` to `config.yaml`.

## Claim boundaries
- The exemplar demonstrates the frozen-node discipline; it does not claim
  statistical methodology beyond preregistration semantics.
- No network, no LLM calls, no runtime dataset downloads.

## Validation commands
```bash
uv run pytest projects/templates/template_experiment_tree/tests \
  --cov=projects/templates/template_experiment_tree/src --cov-fail-under=90
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/gates/public_capabilities.py
```
