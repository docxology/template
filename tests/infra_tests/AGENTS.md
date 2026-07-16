# tests/infra_tests/ - Infrastructure Test Documentation

## Purpose

The `tests/infra_tests/` directory validates the reusable infrastructure modules in `infrastructure/`.
The full suite is the coverage-bearing repository gate. Project pipelines run
the narrower `pipeline-smoke` subset to validate DAG execution, advisory
controls, evidence/profile/benchmark extension points, documentation
invariants, and tracked-artifact guards without rerunning every infrastructure
module test on each project render.

## Standards

- Use real data and real execution paths.
- Do not use mock frameworks or fake replacements for the unit under test.
- Use `pytest.monkeypatch` only for environment/path isolation or to point clients at local test servers that exercise real HTTP/filesystem code.
- Use subprocess calls for CLI behavior.
- Use temporary directories for filesystem behavior.
- Use live services only when a test is explicitly marked for them.
- Treat `monkeypatch.setattr`/`setitem` as prohibited semantic dependency
  replacement, not evidence that a test is mock-free. The enforced lexical and
  semantic gates are documented in
  [`tests/AGENTS.md`](../AGENTS.md#automated-gate-versus-semantic-inventory).

## Covered Areas

- `autoresearch/`
- `benchmark/`
- `config/`
- `core/`
- `doctor/`
- `documentation/`
- `git_hook_smoke/`
- `llm/`
- `methods/`
- `orchestration/`
- `project/`
- `prose/`
- `publishing/`
- `reference/`
- `rendering/`
- `reporting/`
- `scientific/`
- `search/`
- `sia/`
- `skills/`
- `steganography/`
- `validation/`

Important nested guides:

- `core/config/`, `core/pipeline/`, and `core/telemetry/` carry focused docs for newer core sub-suites.
- `validation/docs/` carries docs-linter regression tests.

## Notes for Contributors

- Keep file and directory names aligned with the live tree.
- Avoid stale counts and old module names in documentation.
- Keep `README.md` summaries short and `AGENTS.md` entries technical.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
