# `template_prose_project/docs/`

Agent guide for the project's documentation hub.

## Purpose

Centralise human-readable documentation that goes beyond the top-level
[`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md): step-by-step
quickstarts, architectural diagrams, on-disk artefact conventions, and
troubleshooting flowcharts.

## Files

| File | When to consult |
|---|---|
| [`quickstart.md`](quickstart.md) | First-time runs and CI integration. |
| [`architecture.md`](architecture.md) | When extending the pipeline; classDiagram + sequenceDiagram. |
| [`output_conventions.md`](output_conventions.md) | When adding a new analysis stage that writes outputs. |
| [`troubleshooting.md`](troubleshooting.md) | When a check fails or a stage exits non-zero. |
| [`README.md`](README.md) | Quick-link index for human navigation. |

## Editing rules

* Every diagram **must** be Mermaid — no ASCII art (project-wide rule).
* Every file should signpost back to the project [`AGENTS.md`](../AGENTS.md)
  and to the relevant infrastructure module SKILL/AGENTS file.
* Keep the quickstart at ≤ 6 steps. Move detail into other files.

## See also

* [`README.md`](README.md) — quick links.
* [`../AGENTS.md`](../AGENTS.md) — project-level agent guide.
* [`docs/rules/folder_structure.md`](../../../docs/rules/folder_structure.md) —
  the project-wide tri-doc convention.
