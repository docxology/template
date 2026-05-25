---
name: template-methods-orchestration
description: |
  Repo-wide methods orchestration workflow for the Research Project Template. USE WHEN
  the user asks to add, audit, improve, or validate methods, methodology, method
  contracts, stage-to-method wiring, artifact/evidence provenance, or orchestration
  across template projects.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: verified_only
  task_type: open-ended
  modes:
    - audit
    - plan
    - repair
  related_skills:
    - template-pipeline-debugging
    - template-reproducibility-audit
    - template-manuscript-claim-verification
    - template-validation-quality
---

# Methods orchestration

## Natural invoke

- "Improve all methods orchestration repo-wide"
- "Make sure methods match the pipeline and artifacts"
- "Audit methodology sections against stage contracts"
- "Add method contract validation for this project"

## Workflow

1. **Build the plan** - run `infrastructure.methods` for the target project(s).
2. **Check surfaces** - manuscript methods files, `pipeline.yaml` stage
   contracts, artifact manifest, evidence registry, and validation commands.
3. **Repair source layers** - update `src/`, thin scripts, manuscript source, or
   stage contracts. Do not edit generated `output/` as a fix.
4. **Regenerate and validate** - run core pipeline or focused stage commands,
   then rerun methods plan with `--check`.
5. **Document routing** - update AGENTS/README when method ownership or commands
   changed.

## Verification commands

```bash
uv run python -m infrastructure.methods plan --project <project> --format markdown
uv run python -m infrastructure.methods plan --project <project> --format json --check
uv run python scripts/execute_pipeline.py --project <project> --core-only
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
uv run pytest tests/infra_tests/methods -q
```

## Handoffs

- Broken stage behavior -> [pipeline-debugging](../pipeline-debugging/SKILL.md)
- Evidence/claim mismatch -> [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)
- Rebuild drift -> [reproducibility-audit](../reproducibility-audit/SKILL.md)
- Validation CLI failures -> [validation-quality](../validation-quality/SKILL.md)
