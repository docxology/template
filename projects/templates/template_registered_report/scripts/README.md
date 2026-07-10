# scripts - template_registered_report

Thin orchestrators. All computation is imported from `src/registered_report/`;
these scripts only handle seeded layout and file I/O. Use the monorepo pipeline
scripts from the repository root for normal test/render stages.

`generate_figures.py` executes the registered analysis on deterministic
demonstration data and renders the four manuscript figures into
`manuscript/figures/`, writing the executed analysis to
`output/data/demo_analysis.json`:

```bash
MPLBACKEND=Agg uv run python projects/templates/template_registered_report/scripts/generate_figures.py
```

`generate_review_artifacts.py` creates deterministic registered-report review
artifacts from `data/example_registration.json`: frozen registration, review
packet, deviation ledger, sensitivity findings, and adherence report.

```bash
uv run python projects/templates/template_registered_report/scripts/generate_review_artifacts.py
```
