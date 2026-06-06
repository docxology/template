---
name: template-academic-pipeline
description: |
  Research-to-publication orchestrator for template projects: research, write, verify,
  review, revise, reproduce, validate, and finalize. USE WHEN the user wants the whole
  paper workflow or enters midstream with an existing paper or reviewer comments.
metadata:
  version: "1.1.0"
  last_updated: "2026-06-06"
  status: active
  data_access_level: verified_only
  task_type: open-ended
  modes:
    - full
    - existing-paper
    - reviewer-comments
    - finalize
  related_skills:
    - template-deep-research
    - template-academic-paper
    - template-academic-paper-reviewer
    - template-manuscript-claim-verification
    - template-reproducibility-audit
---

# Academic pipeline

Template-native orchestrator for the full research-to-publication path. It
coordinates existing skills and file-backed controls; it does not introduce an
autonomous hidden approval loop.

## Natural invoke

- "Run the complete research-to-paper workflow"
- "I already have a paper; review and finalize it"
- "I received reviewer comments; revise and verify"
- "Prepare this manuscript for Zenodo or arXiv"

## Inputs to confirm

- **Entry point** - new research, existing paper, reviewer comments, or finalization.
- **Project** - active template project or private project path; preserve confidentiality boundaries.
- **HITL mode** - full-auto, gate-only, checkpoint, or project policy from pipeline control.
- **Required gates** - claim verification, reproducibility, validation, review, and publication package checks.

## Workflow

1. **Stage map** - research -> paper plan/draft -> claim verification -> read-only review -> revision -> re-review -> reproducibility -> validation -> final package.
2. **Material passport** - record handoffs as file paths and generated artifacts: search corpus, claim ledger, evidence registry, artifact manifest, snapshots, validation reports, and reviewer matrices.
3. **Human checkpoints** - use existing HITL controls for gate-only or checkpoint approvals; detached review files live under `output/hitl/`.
4. **Integrity gates** - run claim verification before review and finalization; run the deterministic reference-existence gate (no fabricated/mismatched/anachronistic citations) and the prose-quality scan; run double-run reproducibility before release claims. These gates are file-backed and deterministic, mirroring the ARS mandatory integrity-check stages but as code, not a hidden agent loop.
5. **Finalize** - render from source, validate outputs, copy deliverables, and document residual risks. Never hand-edit `output/` as the fix.

## Deliverables

- Pipeline status table: stage, owner skill, inputs, outputs, gate, and next action.
- Material passport summary with artifact paths and verification status.
- Review and revision traceability matrix.
- Final readiness report with claim, reproducibility, validation, and publication checks.

## Verification commands

```bash
uv run python scripts/execute_pipeline.py --project <project> --core-only
uv run python -m infrastructure.validation.cli evidence projects/<project> --fail-on-issues
uv run python -m infrastructure.reference.verification verify projects/<project>/manuscript/references.bib --live --as-of-year <year> --fail-on-issues
uv run python -m infrastructure.validation.cli prose-quality projects/<project>/manuscript
uv run python -m infrastructure.validation.cli integrity output/<project>/
uv run python -m infrastructure.core.pipeline.snapshot compare <left> <right> --output-dir projects/<project>/output
```

## References

- [MODE_REGISTRY.md](../MODE_REGISTRY.md)
- [deep-research](../deep-research/SKILL.md)
- [academic-paper](../academic-paper/SKILL.md)
- [academic-paper-reviewer](../academic-paper-reviewer/SKILL.md)
- [reproducibility-audit](../reproducibility-audit/SKILL.md)
