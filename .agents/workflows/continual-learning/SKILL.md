---
name: continual-learning
description: Update repository-local durable preferences and workspace facts from user-authorized evidence, with an incremental local index. Use when asked to maintain agent memory or review prior authorized work.
metadata:
  invocation: explicit
---

# Maintain local agent memory

Use [the shared memory role](../../roles/agents-memory-updater.md) and
[`infrastructure.core.agent_memory`](../../../infrastructure/core/agent_memory.py).
Read current memory before changing it. Keep durable facts in
`.agents/state/continual-learning-memory.json`; the tracked example defines its schema.

Use only user-provided or explicitly authorized transcript sources. Delegate
when the current task allows it; direct execution of the same role is also supported.
This workflow does not authorize contacting other chats or people, reading
unrelated private transcripts, or scheduling background work.

Retain the original legacy memory during migration. Save through the helper,
which writes the canonical path atomically. Keep runtime memory and transcript
indexes ignored; root `AGENTS.md` remains the public repository contract.
