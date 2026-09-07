## Change

<!-- Describe the concrete problem, resulting behavior, and affected public interfaces.
Link issues when relevant. Explain any changed defaults or compatibility impact. -->

## Verification

<!-- List commands actually run and their results. Distinguish passing tests,
skips, baseline failures, and deferred verification. Link relevant CI or audit
receipts. Local success does not establish hosted CI success. -->

Useful local checks (run the ones relevant to this change):

```bash
uv sync --frozen
uv run python -m infrastructure.project.public_scope lint-paths | xargs uv run ruff check
uv run python -m infrastructure.project.public_scope lint-paths | xargs uv run ruff format --check
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy
uv run pytest tests/infra_tests/ --benchmark-disable --cov=infrastructure --cov-fail-under=60 --timeout=120 -m "not requires_ollama and not requires_docker and not network and not slow and not bench and not benchmark and not performance"
uv run python scripts/gates/public_readiness.py --profile release --json
uv run pytest tests/regression/ -q --no-cov --timeout=120
uv run python scripts/audit/lint_docs.py
uv run python scripts/docgen/api_reference.py --check
```

The readiness report counts **projects**, not individual tests. Each public
exemplar must meet its own coverage floor; `--allow-skips` is an explicit
project-level exception, not evidence that skipped work passed.

See [CI definitions](workflows/ci.yml) and [local pre-push checks](AGENTS.md#local-pre-push-parity-pre-commit-configyaml)
for the full platform matrix and security checks. Identify affected pipeline
stages using the [canonical stage map](../docs/RUN_GUIDE.md#core-pipeline-stages--executive-reporting).

## Compatibility and failure boundaries

<!-- Describe preserved imports, changed dependencies/defaults, migration needs,
security boundaries, and meaningful limitations. For rendering changes, separate
real renderer/browser evidence from pixel or accessibility certification. -->

## Review checklist

Mark completed items and explain anything not applicable:

- [ ] Changes preserve the infrastructure/project boundary and thin orchestrators.
- [ ] Tests use real implementations and comply with the repository no-mocks policy.
- [ ] Relevant lint, type, test, coverage, and security checks passed.
- [ ] Affected documentation and generated references match the implementation.
- [ ] The staged diff contains only intended public files and no credentials or private artifacts.
- [ ] Deferred checks and known failures are explicitly documented.
