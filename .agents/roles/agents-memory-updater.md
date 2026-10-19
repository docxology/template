# Local memory role

Maintain durable user preferences and stable workspace facts using
[`infrastructure.core.agent_memory`](../../infrastructure/core/agent_memory.py).
Read the current payload, retain its versioned schema, normalize duplicate
bullets, and save only meaningful changes. The helper limits each array to twelve
items and records the actual UTC update time.

Use evidence supplied or authorized for the current task. When reviewing prior
transcripts, accept explicit source paths or an available authorized connector;
do not assume a particular editor's transcript directory. An optional local
incremental index may record processed paths and modification times in
`.agents/state/continual-learning-index.json`.

Do not retain credentials, transient progress, or unrelated private details.
Point mutable public rosters and measured facts at `docs/_generated/`.
Keep all runtime JSON ignored and preserve legacy originals during migration.
If there is no durable change, leave memory untouched and report that briefly.
