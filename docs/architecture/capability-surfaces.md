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
| **Skills** (`SKILL.md` descriptors) | `infrastructure.skills.discovery` | `.agents/skill_manifest.json` | `manifest_matches_discovery` |
| **Operations** (every `python -m` CLI) | `infrastructure.skills.operation_registry` | `.agents/operations_manifest.json` | `operations_manifest_matches_discovery` |
| **Pipeline stages** (stage count derived live from `pipeline.yaml`) | `infrastructure.core.pipeline.cli` | derived live from `pipeline.yaml` | n/a (derive-only) |
| **Templates** (public exemplars) | `infrastructure.project.exemplar_roster` | `infrastructure/project/template_manifest.json` | `--check` in `scripts/docgen/exemplar_roster.py` |

Catalogs are **derived, never hand-maintained** — so they cannot silently rot.

## Invoking capabilities

All infrastructure CLIs are invoked via `uv run python -m infrastructure.<module>`;
the only `console_scripts` entry point is `research-template`
(→ `infrastructure.orchestration.cli:main`). Conventions an adopting
CLI should follow (see `infrastructure/core/cli_scaffold.py`):

- `main(argv: Sequence[str] | None = None) -> int` — headless-invocable, returns
  an exit code (see `scripts/runner/exit_codes.py` for the shared `ExitCode` enum).
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

The server implements [MCP `2026-07-28`](https://blog.modelcontextprotocol.io/posts/2026-07-28/).
Clients may probe `server/discover` or invoke tools directly. Every request carries
`io.modelcontextprotocol/protocolVersion`, client identity, and client
capabilities in `params._meta`. Discovery returns the server identity in
`result._meta["io.modelcontextprotocol/serverInfo"]`. Discovery and tool lists
include cache lifetime and scope; all successful results use `resultType: complete`.
Unsupported versions return a structured negotiation error advertising only
`2026-07-28`. Each request is admitted independently, including requests sent
after discovery on the same stdio connection.

`invoke_cli` is curated: it refuses any module that is not `infrastructure.*` and
not reported invocable by the operation registry — it is a vetted tool surface,
not an arbitrary shell. It is also **capability-tiered**: each operation carries an
`effect`. Only explicitly reviewed module routes are `read_only`. Known local
file writers, external/paid dispatchers and brokers are `mutating`; every other
or newly discovered CLI receives that tier conservatively. This is an opt-in
requirement for unaudited operations, not a claim that they actually write.
The tier applies to the whole module, including help/schema/dry-run forms.

Both the MCP tool and the public Python `invoke_cli` API require `allow_mutating`
to be a boolean; strings, numbers, null and containers are refused before
discovery or dispatch. Missing authorization defaults to `false`. Literal
`allow_mutating=true` or the existing configured `TEMPLATE_MCP_ALLOW_MUTATING=1`
opt-in admits the guarded tier; a valid `false` retains that configured behavior.
Direct CLI commands keep their own admission and custody rules.

The operation registry discovers both **packages** (a directory with `__main__.py`)
and **single-file CLIs** (a `foo.py` with an `if __name__ == "__main__":` guard whose
directory is not itself an invocable package) — so documented single-file entry points
such as `infrastructure.core.health` and `infrastructure.project.public_scope` are
reachable through this surface too.

Run it:

```bash
uv run python -m infrastructure.mcp_server      # or: uv run python scripts/runner/mcp_server_template.py
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
