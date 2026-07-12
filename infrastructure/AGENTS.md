# Infrastructure Layer

## Purpose

Layer 1 contains reusable tooling for the research template: project discovery,
pipeline execution, validation, rendering, reporting, publishing, skills, and
agent-facing documentation. Project-specific science stays in
`projects/{name}/src/`; root and project scripts stay thin.

## Where To Look

| Task | Primary package | Notes |
| --- | --- | --- |
| Run or inspect the pipeline | `core/pipeline/`, `orchestration/`, `scripts/` | `run.sh` delegates into `infrastructure.orchestration`; stage semantics live in `core/pipeline/pipeline.yaml`. |
| Validate manuscripts and outputs | `validation/` | CLI entry point: `uv run python -m infrastructure.validation.cli ...`. |
| Render PDFs, slides, web, DOCX, EPUB | `rendering/` | Rendering preflight may import validation leaves, not broad validators. |
| Project roster, sidecar links, git guards | `project/` | Public scope comes from `project.public_scope`; private mirrors are local-only. Sidecar sync for all four top-level trees is registered in `orchestration/link_sync.py`. |
| Resource pools (fonds, rules, tools) | `fonds/`, `rules/`, `tools/` | Passive data pools, governance rules, and invocable tools mirror `projects/` with git-tracked `templates/*` exemplars. |
| Reports and release readiness | `reporting/` | Local evidence dashboards only; network publication is outside release-readiness aggregation. |
| Generated docs and live counts | `documentation/` | `COUNTS.md`, active projects, API reference, publication records. |
| Methods orchestration | `methods/` | Read-only mapping of pipeline contracts, methods prose, artifacts, evidence, validation commands. |
| Skill discovery and manifests | `skills/` | Regenerates `docs/_generated/skills_index.md` and `.cursor/skill_manifest.json`. |
| Optional companions | `search/`, `llm/`, `steganography/`, `sia/`, `autoresearch/` | Keep opt-in dependencies and generated state out of default CI/pipeline unless documented. |
| Expose the agent surface over MCP | `mcp_server.py` | Opt-in self-contained stdio JSON-RPC server (`python -m infrastructure.mcp_server`) exposing `list_operations` / `describe_pipeline` / `list_skills` / `invoke_cli` as MCP tools. Dual-era: legacy `2024-11-05` initialize plus stateless `2026-07-28` `server/discover` and per-request metadata. Standard-library only; not wired into CI/pipeline. |

## Boundaries

- Business logic lives in `infrastructure/` or `projects/{name}/src/`.
- Scripts orchestrate only; moving computation into scripts breaks the template
  contract and the thin-orchestrator drift checks.
- Do not hard-code rotating private project names. Link
  `docs/_generated/active_projects.md` for public rendered scope.
- `.codegraph/`, `.leann/`, `.omo/`, coverage files, output trees, and other
  local indexes are generated state and must not be tracked.
- Optional tools such as CodeGraph and LEANN are navigation aids. Publication
  claims require source files, tests, evidence registries, artifacts, and gates.

## Public API Rules

- Infrastructure packages that re-export symbols must keep explicit `__all__`
  entries and pass `uv run python -m infrastructure.skills check-all-exports`.
- Add new routable packages with `AGENTS.md`, `README.md`, and `SKILL.md` when
  they are intended for agent discovery.
- Keep generated facts in generated files. Do not copy measured counts into
  long-lived prose; regenerate `docs/_generated/COUNTS.md` instead.

## Verification

```bash
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run ruff check
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/audit/check_tracked_projects.py
uv run python scripts/audit/check_tracked_generated_artifacts.py
uv run python scripts/gates/module_line_count_check.py
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills check-all-exports
```

Use focused pytest slices for changed packages, then broaden only when the
changed surface crosses package or pipeline boundaries.

## Documentation Contract

- `AGENTS.md`: operating contract for agents; concise and non-redundant.
- `README.md`: human guide and deeper examples.
- `SKILL.md`: routing contract with YAML frontmatter.
- `docs/_generated/*`: generated facts; update via generator commands, not by
  hand.

## See Also

- [`README.md`](README.md)
- [`methods/AGENTS.md`](methods/AGENTS.md)
- [`project/AGENTS.md`](project/AGENTS.md)
- [`validation/AGENTS.md`](validation/AGENTS.md)
- [`rendering/AGENTS.md`](rendering/AGENTS.md)
