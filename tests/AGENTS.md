# tests/ - Repository Test Documentation

## Purpose

The `tests/` directory contains repository-wide tests for infrastructure, integrations, and behavioral contracts that cross module boundaries.

## Standards

- Use real data and real execution paths.
- Do not use mock frameworks (`unittest.mock`, `MagicMock`, `mocker.patch`) or replace the unit under test with fake behavior.
- `pytest.monkeypatch` is acceptable for environment variables, current working directories, import paths, and test-server URLs when the test still exercises real code paths.
- Prefer subprocess calls for CLI behavior.
- Use temporary files and directories for filesystem behavior.
- Use HTTP test servers for HTTP behavior.

## Current Subtrees

- `tests/_support/` - shared test helpers (canonical ephemeral project scaffold factory)
- `tests/infra_tests/` - infrastructure module coverage
- `tests/integration/` - end-to-end and orchestration coverage
- `tests/regression/` - pinned-value regression tier (real exemplar projects only)

## Synthetic project scaffold factory

Infrastructure and integration tests that need a minimum-valid project tree
under ``tmp_path`` should use [`tests/_support/projects.py`](_support/projects.py):

- ``make_project(root, name="template_test", ...)`` — one project under
  ``projects/<name>/`` or ``projects/<program>/<name>/`` (pass ``program="templates"``
  for qualified names like ``templates/template_test``).
- ``make_repo(root, names=(...))`` — repository root with multiple synthetic projects.
- ``repo_layout=False`` — standalone project at ``<root>/<name>/`` (integration fixtures).

Default slug ``template_test`` is the canonical synthetic stand-in. Do **not**
create a git-tracked ``template_test`` project under ``projects/`` — contract,
public-scope, and regression tests continue to reference the nine public exemplars.

## Coverage Expectations

- Infrastructure code is held to the repository coverage floor in `tests/infra_tests/`.
- Integration tests should confirm the pipeline and shell entry points remain wired correctly.
- The project pipeline uses a curated `pipeline-smoke` infrastructure subset for speed; the full infrastructure coverage gate remains explicit (`scripts/01_run_tests.py --infra-only --infra-scope full`).

## Documentation Expectations

- Keep `README.md` files aligned with the live test tree.
- Keep per-folder `AGENTS.md` files accurate and specific to the folder they document.

## Multi-project pytest and `conftest.py`

**Canonical:** Run **one pytest process per** `projects/<name>/tests/` tree. Use
`infrastructure.core.test_runner.run_per_project_pytest` (from
[`scripts/01_run_tests.py`](../scripts/01_run_tests.py)), or invoke
`uv run pytest projects/<name>/tests/` for a single workspace. CI `test-project`
merges coverage with `--cov-append` across per-project runs.

**Unsupported:** One `pytest` collection that spans multiple
`projects/*/tests/` directories when **more than one** of them defines
`tests/conftest.py`. Pytest loads each `conftest` as a plugin; the shared
basename collides (`ValueError: plugin already registered`). The workaround is
the per-project subprocess model above, not a single mega pytest command.

**References:** [`infrastructure/core/test_runner.py`](../infrastructure/core/test_runner.py),
[`tests/infra_tests/core/test_test_runner.py`](infra_tests/core/test_test_runner.py),
[`TO-DO.md`](../TO-DO.md) (tracked conftest item).

## See Also

- [`README.md`](README.md)
- [`infra_tests/AGENTS.md`](infra_tests/AGENTS.md)
- [`integration/AGENTS.md`](integration/AGENTS.md)
