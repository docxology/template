# Shared agent interface

Read [the repository contract](../AGENTS.md) and the applicable directory guide
before editing. This directory is the canonical home for generic agent behavior.

| Surface | Contract |
| --- | --- |
| [`skill_manifest.json`](skill_manifest.json) | Generated public skill discovery; `agent_ref` identifies the source skill. |
| [`operations_manifest.json`](operations_manifest.json) | Generated static CLI catalog; operation effects and each CLI's admission rules govern execution. |
| [`workflows/`](workflows/) | Maintained local workflow descriptors shared by editors and agent runtimes. |
| [`roles/agents-memory-updater.md`](roles/agents-memory-updater.md) | Local memory role using user-authorized evidence. |
| [`state/README.md`](state/README.md) | Tracked schema and ignored machine-local memory. |
| [`skills/`](skills/) | The unchanged pinned upstream collection governed by [`context-engineering.lock.json`](context-engineering.lock.json). |

Generic workflow discovery does not install files into a user's runtime.
`runtime-install` installs only the pinned upstream collection and requires an
intentional user-level installation request. Preserve that collection's provenance;
put local additions under `workflows/`.

Regenerate through the owning CLI, then verify discovery and routing:

```bash
uv run python -m infrastructure.skills write
uv run python -m infrastructure.skills operations-write
uv run python -m infrastructure.skills write-index
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills operations-check
uv run python scripts/gates/skill_reachability_check.py
```

Only declared public agent directories and exact manifest/schema files enter
Source evidence. Runtime memory and transcript indexes stay ignored. The public
contract never grants access to unrelated transcripts, messages, or credentials.
