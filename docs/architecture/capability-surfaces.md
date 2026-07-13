# Capability Surfaces — the agent-operable contract

> How an AI agent (not just a human reading prose) discovers, invokes, composes,
> and verifies every capability this package exposes. The unifying idea: a small
> set of **machine-readable catalogs**, each generated from live source and each
> guarded by a drift check, plus an MCP server that serves them at runtime.

## The one discovery contract

Every agent-facing catalog follows the same shape, proven first by the skills
module (`infrastructure/skills/discovery.py`):

```
discover_*  ->  build_*_payload  ->  write_*_manifest  ->  *_matches_discovery (drift gate)
```

| Catalog | Module | Emit / generated artifact | Drift gate |
| --- | --- | --- | --- |
| **Skills** (`SKILL.md` descriptors) | `infrastructure.skills.discovery` | `.cursor/skill_manifest.json` | `manifest_matches_discovery` |
| **Operations** (every `python -m` CLI) | `infrastructure.skills.operation_registry` | `.cursor/operations_manifest.json` | `operations_manifest_matches_discovery` |
| **Pipeline stages** (14-stage contract) | `infrastructure.core.pipeline.cli` | derived live from `pipeline.yaml` | n/a (derive-only) |
| **Templates** (public exemplars) | `infrastructure.project.exemplar_roster` | `infrastructure/project/template_manifest.json` | `--check` in `generate_exemplar_roster_doc.py` |

Catalogs are **derived, never hand-maintained** — so they cannot silently rot.

## Invoking capabilities

All CLIs are invoked via `uv run python -m infrastructure.<module>` (the package
sets `package = false`; there are no `console_scripts`). Conventions an adopting
CLI should follow (see `infrastructure/core/cli_scaffold.py`):

- `main(argv: Sequence[str] | None = None) -> int` — headless-invocable, returns
  an exit code (see `scripts/exit_codes.py` for the shared `ExitCode` enum).
- Shared flags: `--repo-root`, `--project`, `--format {json,table}`, `--verbose`.
- `--schema` — emit the command's JSON parameter contract (via
  `cli_scaffold.parser_schema`), the per-command counterpart to the operation
  catalog. Reference adopter: `python -m infrastructure.core.pipeline describe-pipeline --schema`.

Discover everything at once:

```bash
uv run python -m infrastructure.skills operations-list-json   # all invocable CLIs + subcommands + exports
uv run python -m infrastructure.core.pipeline describe-pipeline --format json   # the stage DAG
uv run python -m infrastructure.skills list-json              # all SKILL.md descriptors
```

## MCP server (runtime surface)

`infrastructure/mcp_server.py` is a **self-contained stdio MCP server** (newline
-delimited JSON-RPC 2.0, standard library only — no new dependencies). It exposes
the catalogs as MCP tools so any MCP-speaking agent can reach them without an
editor:

| Tool | Returns |
| --- | --- |
| `list_operations` | the operation catalog |
| `describe_pipeline` | the pipeline stage contract (`core_only` arg) |
| `list_skills` | discovered `SKILL.md` descriptors |
| `invoke_cli` | runs a **registered** `infrastructure.*` CLI; returns `{exit_code, stdout, stderr}` |

The server is **dual-era**. Existing clients retain the `2024-11-05`
`initialize` / `notifications/initialized` lifecycle and legacy response shapes.
Clients implementing the [MCP `2026-07-28` release candidate](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/)
can instead
probe `server/discover` and then issue stateless requests carrying
`io.modelcontextprotocol/protocolVersion`, client identity, and client
capabilities in `params._meta`. Modern list results are explicitly cacheable;
no initialize state is retained or required. Unsupported modern versions return
the structured negotiation error with the server's supported-version list, so a
dual-era client can choose the modern version or fall back to legacy initialize.

`invoke_cli` is curated: it refuses any module that is not `infrastructure.*` and
not reported invocable by the operation registry — it is a vetted tool surface,
not an arbitrary shell. It is also **capability-tiered**: each operation carries an
`effect` (`read_only` by default, `mutating` for the publish / upload / paid CLIs
in the registry's `MUTATING_OPERATIONS` allowlist), and a `mutating` op is refused
unless the caller passes `allow_mutating=true` or sets `TEMPLATE_MCP_ALLOW_MUTATING=1`.

The operation registry discovers both **packages** (a directory with `__main__.py`)
and **single-file CLIs** (a `foo.py` with an `if __name__ == "__main__":` guard whose
directory is not itself an invocable package) — so documented single-file entry points
such as `infrastructure.core.health` and `infrastructure.project.public_scope` are
reachable through this surface too.

Run it:

```bash
uv run python -m infrastructure.mcp_server      # or: uv run python scripts/mcp_server_template.py
```

The conformance matrix is exercised against the pure handler and a real stdio
subprocess:

```bash
uv run pytest tests/infra_tests/test_mcp_server.py -q
```

**MCP direction.** The package was previously MCP-*client*-only
(`infrastructure/search/deep_research/` consumes remote MCP servers). This server
adds the MCP-*server* surface. It is **opt-in** and intentionally not part of the
default pipeline or CI.

## Verification surface

Tests are themselves agent-composable:

- `tests/_suite_registry.py` — `SUITE_REGISTRY` names each suite (`infra_tests`,
  `integration`, `regression`) with its path and coverage floor.
- `tests/_test_selector.py` — `TestSelector(...).build()` emits a validated
  `pytest` argv list, so an agent never hand-constructs marker strings.

## Summary of delivery surfaces

1. **Library API** — typed, `__all__`-fenced module exports.
2. **CLI** — `uv run python -m infrastructure.<module>` with uniform flags + `--schema`.
3. **Pytest** — suites discoverable via the suite registry + selector.
4. **Docs** — `SKILL.md` + per-folder `AGENTS.md`/`README.md`.
5. **Shell** — `run.sh` / `secure_run.sh` dispatch into the orchestration CLI.
6. **YAML config** — `pipeline.yaml`, project `config.yaml`.
7. **Validation gates** — ruff/mypy/bandit/pytest floors + audit scripts + drift checks.
8. **MCP server** — `infrastructure/mcp_server.py` (opt-in runtime surface).
