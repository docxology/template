# Local agent state

Tracked schema: [`continual-learning-memory.example.json`](continual-learning-memory.example.json).
Runtime memory, hook cadence and transcript indexes are ignored. The existing
Git publication guard also rejects force-added runtime state in this directory
and in `.cursor/hooks/state/`; only the direct README and
empty schema example are public. Keep personal
facts here rather than in the public repository instructions.

Use `load_memory()` and `save_memory()` from
[`infrastructure.core.agent_memory`](../../infrastructure/core/agent_memory.py).
The loader reads `.agents/state/continual-learning-memory.json`, then falls
back to the tracked empty schema. Saving writes only the canonical file.
Other local files are preserved.
