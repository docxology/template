# template_redacted_report - AGENTS.md

## Ground truth

Configuration lives in `manuscript/config.yaml`; invented public redaction fixtures live in `data/`; reusable release-audit logic lives in `src/redacted_report/`.

## Commands

```bash
uv run pytest projects/templates/template_redacted_report/tests --cov=projects/templates/template_redacted_report/src --cov-fail-under=90
uv run python scripts/pipeline/stage_01_test.py --project templates/template_redacted_report --project-only
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_redacted_report
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_redacted_report
```

## Contracts and boundaries

Keep this exemplar limited to lawful redaction, declassification support, public-records release review, taxonomy normalization, source-safe ledgers, reviewer approval gates, sanitized packet export, and source-protection auditing. Do not add targeting, collection, evasion, or surveillance operational guidance. All committed examples must be invented fixtures.

Stage 02 runs only `scripts/01_generate_release_artifacts.py`, as declared by
`manuscript/config.yaml` → `analysis.scripts`. The script delegates loading,
policy application, source-safe projection, and canonical JSON writing to
`src/redacted_report/artifacts.py`. Public audit artifacts must remain text-free:
they may expose sanitized metadata and cryptographic hashes, never source spans,
review rationales, or the in-memory narrative packet.

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile numbers generated (not transcribed into prose), and pair every verifier-like gate (hash manifests, PDF proof verification, redaction ledgers) with a negative control — as the known-bad crafted-file cases in `tests/test_visuals_coverage.py` do.
