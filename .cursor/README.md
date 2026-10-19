# Deprecated Cursor compatibility directory

Generic configuration moved to [`.agents/`](../.agents/README.md).
Use its manifests, local workflows and memory schema. New generic behavior
belongs there; Cursor-specific adapters may remain here.

Existing ignored `.cursor/hooks/state/` files stay local and are retained.
The memory loader can read the legacy memory file with a deprecation warning;
its next explicit save writes `.agents/state/continual-learning-memory.json`.
Review the result before removing any old local state.
