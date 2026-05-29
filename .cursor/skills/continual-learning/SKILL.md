---
name: continual-learning
description: Orchestrate continual learning by delegating transcript mining to agents-memory-updater and writing durable memory to local JSON (never root AGENTS.md Learned sections). USE WHEN continual learning, mine prior chats, maintain agent memory, or the stop hook triggers this skill.
disable-model-invocation: true
---

# Continual Learning (template repo)

Keep durable agent memory in **local JSON**, not in root `AGENTS.md`.

## Trigger

Use when the user asks to mine prior chats, maintain agent memory, or run the continual-learning loop (including stop-hook followups).

## Workflow

1. Call the `agents-memory-updater` subagent (repo override at `.cursor/agents/agents-memory-updater.md`).
2. Return the updater result verbatim.

## Target file

- Memory: `.cursor/hooks/state/continual-learning-memory.json`
- Schema example: `.cursor/hooks/state/continual-learning-memory.example.json`
- Optional helpers: `infrastructure.core.agent_memory`

## Guardrails

- Keep this skill orchestration-only — do not mine transcripts or edit files in the parent flow.
- Do not bypass the subagent.
- **Never** add or edit `## Learned User Preferences` or `## Learned Workspace Facts` in root `AGENTS.md` (public-repo contract).
- Do not commit `continual-learning-memory.json` or `continual-learning-index.json`.
