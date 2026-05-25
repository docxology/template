# infrastructure/core/config/ - Configuration Helper Documentation

## Purpose

The `infrastructure/core/config/` package holds configuration loading, formatting, query helpers, schema definitions, and the config CLI.

## Files

- `loader.py` - config loading and environment merging
- `formatting.py` - author and metadata formatting
- `queries.py` - config queries
- `schema.py` - config models and validation schema
- `cli.py` - config CLI entry point

## Per-project schema extensions

`schema.py` exposes a small registry so projects can declare extra
valid top-level keys for `manuscript/config.yaml` without disabling
validation globally:

- `register_project_schema_extension(project_name, schema)` — record
  additional keys for a project (or, with `project_name=""`, globally).
- `get_project_schema_extensions(project_name)` — read back the
  registered keys.
- `clear_project_schema_extensions()` — test-fixture helper.

`loader.validate_config_keys` and `loader.load_config` accept an
optional `project_name=` argument; the loader also infers the name
from a standard `…/projects/<name>/manuscript/config.yaml` path.
Both functions support `strict=True` for CI/tooling paths that should
raise on unknown top-level keys. `schema.generate_manuscript_config_schema`
exports a JSON Schema for editors and fork setup automation. The canonical
top-level schema includes `analysis.scripts` for the Stage 02 script allowlist;
arbitrary project-owned settings belong under `project_config` unless a
project registers a schema extension.
Full usage example:
[`docs/operational/config/configuration.md`](../../../docs/operational/config/configuration.md#per-project-schema-extensions).

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`docs/operational/config/configuration.md`](../../../docs/operational/config/configuration.md) — per-project schema extensions section
