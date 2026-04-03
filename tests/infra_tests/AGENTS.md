# tests/infra_tests/ - Infrastructure Test Documentation

## Purpose

The `tests/infra_tests/` directory validates the reusable infrastructure modules in `infrastructure/`.

## Standards

- Use real data and real execution paths.
- Do not use mocks, monkeypatches, or fabricated responses.
- Use subprocess calls for CLI behavior.
- Use temporary directories for filesystem behavior.
- Use live services only when a test is explicitly marked for them.

## Covered Areas

- `core/`
- `documentation/`
- `llm/`
- `publishing/`
- `rendering/`
- `reporting/`
- `scientific/`
- `skills/`
- `steganography/`
- `validation/`

## Notes for Contributors

- Keep file and directory names aligned with the live tree.
- Avoid stale counts and old module names in documentation.
- Keep `README.md` summaries short and `AGENTS.md` entries technical.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
