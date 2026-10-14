# Documentation Infrastructure Tests

## Scope

This directory tests source-derived documentation and the SDK's current figure
metadata and generated-registry APIs. The module map and commands are in
[README.md](README.md).

## Figure controls

`test_figure_manager.py` exercises real registration, metadata conversion,
label lookup, JSON persistence/reload, Markdown inventories, and recovery from
corrupt registry input. Registry identifiers are metadata records; manuscript
presentation numbers belong to pandoc-crossref.

`test_generated_figure_registry.py` creates actual output files and binds them
to project-owned specifications. Preserve its negative controls for missing or
deleted outputs, duplicate labels or filenames, incomplete specifications, and
publication refusal before a partial destination/registry can be created.

## Documentation controls

- API and glossary tests parse actual source ASTs and declared exports. Marker
  replacement must preserve surrounding authored prose and remain idempotent.
- Stage tables derive from the canonical YAML DAG; tests must expose changed
  stages rather than retaining copied literals.
- Count and coverage tests bind the declared input inventory. Keep measurement
  subprocesses isolated from canonical authored sources and publication outputs.
  Exact independent coverage snapshots follow the production contract in
  [documentation AGENTS](../../../infrastructure/documentation/AGENTS.md).
- Public project and publication tables derive from source-owned registries and
  metadata. Tests use controlled local inputs and explicit external retrieval
  boundaries.
- Backlog tests preserve stable IDs, future-work criteria, and privacy checks for
  rotating or confidential paths.

## Testing rules

Use real files, computations, subprocesses, and source modules. Tests must cover
meaningful behavior and refusal cases without replacing dependencies or adding
mock frameworks. Use pytest's unique temporary paths for mutable fixtures;
ordinary documentation tests must not create or rewrite repository outputs.

After refactoring, remove only tests exclusive to a retired API. Preserve the
current persistence, corruption, metadata, generated-file validation, and
source-derived documentation controls.

```bash
uv run pytest tests/infra_tests/documentation/ -v
uv run pytest tests/infra_tests/documentation/test_figure_manager.py tests/infra_tests/documentation/test_generated_figure_registry.py -v
```

Run the full public Ruff/mypy surface and relevant documentation drift checks
for source/API changes. Regenerate counts and the API reference through their
own generators; keep measured numbers out of hand-authored test guidance.

## See Also

- [Documentation module contract](../../../infrastructure/documentation/AGENTS.md)
- [Infrastructure test contract](../AGENTS.md)
- [Testing standards](../../../docs/rules/testing_standards.md)
- [Testing guide](../../../docs/development/testing/testing-guide.md)
