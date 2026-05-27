# template_autoresearch_project Docs

This folder documents the public AutoResearch exemplar project. The project is
designed to run through the standard template pipeline while keeping the
AutoResearch loop deterministic, configurable, offline, and human-reviewed. It
demonstrates a local MNIST subset, bounded numpy neural-network candidate
evaluation, evidence-linked accepted ideas, review gates, benchmark-style
grading, phase-settlement ledgers, figure-quality checks, local security
integrity artifacts, and explicit disclosure while deferring autonomous
generated-code execution, runtime dataset downloads, and external signing.
The generated evidence-registry report is compact by default; the full fact
dump is an opt-in local debug artifact via `TEMPLATE_EVIDENCE_REGISTRY_FULL=1`.

Primary command:

```bash
./run.sh --pipeline --project template_autoresearch_project --core-only --skip-infra
```

Useful direct checks:

```bash
uv run python scripts/02_run_analysis.py --project template_autoresearch_project
uv run python -m infrastructure.autoresearch.cli validate --project template_autoresearch_project --fail-on-issues
uv run python -m pytest projects/template_autoresearch_project/tests -q
```

Documentation map:

| File | Purpose |
| --- | --- |
| [configuration.md](configuration.md) | Project knobs and how they feed the loop |
| [outputs.md](outputs.md) | Generated data, reports, and review artifacts |
| [runbook.md](runbook.md) | End-to-end operation through `run.sh` |
