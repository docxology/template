# Prompt: Comprehensive assessment

## Purpose

Provide a **copy-paste template** for a full pass over code, tests, documentation, and manuscript—aligned with this repository’s gates—without baking in stale metrics.

Live counts and CI parity live in [`../_generated/canonical_facts.md`](../_generated/canonical_facts.md) and [`.github/AGENTS.md`](../../.github/AGENTS.md).

## Copy-paste prompt

```
You are performing a comprehensive assessment of the Research Project Template checkout for project(s): [names or "all active"].

Authoritative roster: docs/_generated/active_projects.md (do not assume fixed project names in prose).

Work through:

1. **Tests** — Run the appropriate pytest invocations (one project test dir per project; avoid merging two projects’ tests in one pytest process if both ship tests.conftest). Confirm coverage gates: infrastructure ≥60%, project ≥90% unless CI documents an exception. No mocks for the unit under test (see docs/rules/testing_standards.md).

2. **Architecture** — Thin orchestrators in scripts/; algorithms in projects/<n>/src/ or infrastructure/. No cross-project imports.

3. **Documentation** — Each meaningful directory has accurate AGENTS.md + README.md; links resolve; avoid duplicating the active project list—link _generated/active_projects.md.

4. **Manuscript** — If the project uses Pandoc-crossref + .bib, follow docs/guides/manuscript-semantics.md. If it uses refs/labels.yaml + [[FIG:]]/[[THMREF:]] tokens, use docs/prompts/manuscript_cross_references.md as the checklist. Validate markdown (and PDF/logs if outputs exist).

5. **Pipeline** — Core vs full DAG, optional LLM stages, copy to output/<name>/ per CLAUDE.md / RUN_GUIDE.

Deliver:
- Executive summary (pass/fail per area).
- Concrete issues (path, symptom, suggested fix).
- Commands you ran and raw exit status.

Do not invent coverage percentages; measure or cite canonical_facts.md / your pytest output.
```

## Commands (reference)

Adjust `<project>` using `docs/_generated/active_projects.md`.

```bash
uv sync

# Project tests + coverage
uv run pytest projects/<project>/tests/ \
  --cov=projects/<project>/src --cov-fail-under=90 -q

# Infrastructure tests + coverage
uv run pytest tests/infra_tests/ \
  --cov=infrastructure --cov-fail-under=60 -q

# Combined test entry point (orchestrated)
uv run python scripts/01_run_tests.py --project <project>

# Markdown validation (example)
uv run python -m infrastructure.validation.cli markdown projects/<project>/manuscript/

# Optional: strict source gate
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
```

## Manuscript cross-reference note

- **Pandoc-crossref style**: `@fig:`, `@eq:`, `@sec:`, `[@bibkey]` per [`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md).
- **Registry token style**: `[[FIG:…]]`, `[[THMREF:…]]`, etc.—see [`manuscript_cross_references.md`](manuscript_cross_references.md).

## Assessment checklist

### Pre-flight

- [ ] Identify target project(s) from `_generated/active_projects.md`.
- [ ] `uv sync` successful; interpreter matches CI matrix if relevant.

### During review

- [ ] Tests pass; coverage meets gates.
- [ ] No forbidden mock patterns in tests (see testing_standards).
- [ ] Docs paths and commands match current scripts.
- [ ] Manuscript refs and citations resolve (appropriate tool per project).

### Reporting

Use a short table: area | status | evidence (command, log snippet, or file).

## See also

- [`validation_quality.md`](validation_quality.md) — validation-focused prompt.
- [`documentation_creation.md`](documentation_creation.md) — doc maintenance.
- [`README.md`](README.md) — prompt index.
