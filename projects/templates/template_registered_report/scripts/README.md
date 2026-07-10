# scripts - template_registered_report

Use the monorepo pipeline scripts from the repository root for normal test/render stages.

`generate_review_artifacts.py` creates deterministic registered-report review artifacts from `data/example_registration.json`: frozen registration, review packet, deviation ledger, sensitivity findings, and adherence report.

```bash
uv run python projects/templates/template_registered_report/scripts/generate_review_artifacts.py
```
