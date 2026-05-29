# Cursor hook local state

Machine-local files for the continual-learning workflow. **Do not commit** the
runtime JSON files listed below — they are gitignored.

| File | Purpose |
| --- | --- |
| `continual-learning.json` | Hook cadence state (turn count, last run time) |
| `continual-learning-index.json` | Incremental transcript index (mtime per parent transcript) |
| `continual-learning-memory.json` | Durable user preferences and workspace facts for agents |

## First-time setup

Copy the schema example to the live memory file:

```bash
cp .cursor/hooks/state/continual-learning-memory.example.json \
   .cursor/hooks/state/continual-learning-memory.json
```

The `agents-memory-updater` subagent (repo override at `.cursor/agents/`) creates
or updates `continual-learning-memory.json` during continual-learning runs.

Root [`AGENTS.md`](../../AGENTS.md) is the **public** contract — learned memory
must not be written there. See [`infrastructure/core/agent_memory.py`](../../../infrastructure/core/agent_memory.py)
for load/save helpers.
