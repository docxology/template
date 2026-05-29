---
name: agents-memory-updater
description: Mine high-signal transcript deltas, update local continual-learning-memory.json, and keep the incremental transcript index in sync. Never write Learned sections to root AGENTS.md.
model: inherit
---

# Local agent memory updater

Own the full memory update flow for continual learning in this **public** template repo.

## Trigger

Use from `continual-learning` when transcript deltas may produce durable memory updates.

## Target files

- **Memory (read/write):** `.cursor/hooks/state/continual-learning-memory.json`
- **Schema (read-only):** `.cursor/hooks/state/continual-learning-memory.example.json`
- **Index (read/write):** `.cursor/hooks/state/continual-learning-index.json`

Optional deterministic merge via:

```bash
uv run python -c "from pathlib import Path; from infrastructure.core.agent_memory import load_memory, save_memory, normalize_bullets; ..."
```

## Workflow

1. Read existing memory JSON first. If missing, copy structure from the example file (version 1, empty arrays).
2. Load the incremental index if present.
3. Inspect only transcript files under `~/.cursor/projects/<workspace-slug>/agent-transcripts/` that are new or have newer mtimes than the index.
4. Pull out only durable, reusable items:
   - recurring user preferences or corrections
   - stable workspace facts
5. Update memory JSON carefully:
   - update matching bullets in place (same topic → revise existing string)
   - add only net-new bullets
   - deduplicate semantically similar bullets
   - cap each array to at most 12 bullets (`learned_user_preferences`, `learned_workspace_facts`)
   - set `updated_at` to current ISO-8601 UTC timestamp
6. Refresh the incremental index for processed transcripts; remove entries for files that no longer exist.
7. If the merge produces no memory changes, leave memory unchanged but still refresh the index when transcripts were scanned.
8. If no meaningful updates exist, respond exactly: `No high-signal memory updates.`

## Guardrails

- Plain bullet strings in JSON arrays only — no evidence/confidence tags, no nested metadata.
- Do not write secrets, private credentials, one-off instructions, or transient session details.
- **Never** edit root `AGENTS.md` Learned sections (enforced by `test_root_agents_is_public_repo_contract_not_personal_memory`).
- Exclude paths, API keys, and machine-local home directories unless they are stable workspace conventions already documented in public docs.

## Output

- Updated `.cursor/hooks/state/continual-learning-memory.json` and index when needed
- Otherwise exactly `No high-signal memory updates.`
