---
name: template-comprehensive-assessment
description: |
  Full checkout audit for the Research Project Template — tests, architecture, docs,
  manuscript, pipeline. USE WHEN user asks for comprehensive assessment, full repo review,
  health check across projects, audit everything, or pre-merge sanity sweep for template
  exemplars — even without naming docs/prompts or a skill. Not for single failing stage only.
---

# Comprehensive assessment

## Natural invoke

- "Audit the whole repo for template_autoresearch_project, template_code_project, and template_prose_project"
- "Full health check — tests, docs, manuscript, pipeline"
- "What's broken across all active projects?"

## Inputs to confirm

- **Project(s)** — names from [`docs/_generated/active_projects.md`](../../_generated/active_projects.md) or "all active".
- **Scope** — single project vs multi-project (one pytest process per project test dir).

## Workflow

Work through:

1. **Tests** — appropriate pytest invocations; one project test dir per project. Coverage: infra ≥60%, project ≥90% unless CI exception. No mocks ([`docs/rules/testing_standards.md`](../../rules/testing_standards.md)).

2. **Architecture** — thin orchestrators in `scripts/`; algorithms in `projects/<n>/src/` or `infrastructure/`. No cross-project imports.

3. **Documentation** — meaningful dirs have accurate AGENTS.md + README.md; links resolve; link `_generated/active_projects.md`, do not duplicate roster.

4. **Manuscript** — Pandoc-crossref + `.bib` → [`docs/guides/manuscript-semantics.md`](../../guides/manuscript-semantics.md). Registry `labels.yaml` + `[[FIG:]]` → [manuscript-cross-references](../manuscript-cross-references/SKILL.md). Validate markdown; PDF/logs if outputs exist.

5. **Pipeline** — core vs full DAG, optional LLM stages, copy to `output/<name>/` per CLAUDE.md / RUN_GUIDE.

## Deliverables

- Executive summary (pass/fail per area).
- Concrete issues: path, symptom, suggested fix.
- Commands run + raw exit status.
- Do not invent coverage percentages.

## Verification commands

```bash
uv sync
uv run pytest projects/<project>/tests/ --cov=projects/<project>/src --cov-fail-under=90 -q
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60 -q
uv run python scripts/01_run_tests.py --project <project>
uv run python -m infrastructure.validation.cli markdown projects/<project>/manuscript/
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
```

## When NOT to use

- **Single failing stage** → [pipeline-debugging](../pipeline-debugging/SKILL.md)
- **Claim-by-claim manuscript pass** → [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)
- **Determinism only** → [reproducibility-audit](../reproducibility-audit/SKILL.md)
