# .agents — README.md

Agent-facing orientation for the `template_pitch_deck` exemplar's local agent
scaffolding.

| Surface | Purpose |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | Per-folder technical reference (routing + change discipline). |
| [`skills/`](skills/README.md) | Project-local skill catalog. |
| [`skills/template-pitch-deck/SKILL.md`](skills/template-pitch-deck/SKILL.md) | The operating skill: load this when working inside the exemplar. |

## For agents

Load [`skills/template-pitch-deck/SKILL.md`](skills/template-pitch-deck/SKILL.md)
before running scripts, editing content, or regenerating outputs in this
exemplar. It covers the thin-orchestrator contract, token/diligence gates, the
no-mocks testing rule, and the render commands.
