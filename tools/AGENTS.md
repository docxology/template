# AGENTS.md — tools/

> Agent-oriented documentation for the `tools/` directory.
> Human developers: see [README.md](README.md).

## Purpose

This directory contains **executable entry points** that agents can discover, invoke, and compose.
Each tool is declared via a `tools.yaml` manifest that specifies type, entrypoints, and metadata.

## Discovery

An agent scanning this workspace should:

1. Recursively find all `tools.yaml` files under `tools/`.
2. Parse `type`, `entrypoints`, and `tags` to decide whether a tool is applicable.
3. Prefer tools tagged `curated` or `production` over `experimental`.

## Manifest Schema (`tools.yaml`)

```yaml
type: code_executor | validator | skill | agent | renderer | model
description: "Human-readable description"
version: "semver string"
tags:
  - curated        # passes quality bar
  - exemplar       # reference implementation
  - production     # safe to run in live pipelines
  - experimental   # under development
creator: "org/repo"
license: "SPDX identifier"
entrypoints:
  - scripts/run.sh        # primary execution entrypoint
  - scripts/validate.sh   # validation / health-check entrypoint
```

## Invocation Contract

| Entrypoint | stdin | stdout | exit code |
|---|---|---|---|
| `scripts/run.sh` | JSON payload (optional) | JSON result | 0 = success |
| `scripts/validate.sh` | — | human-readable report | 0 = valid |
| `scripts/invoke.sh` | prompt string | agent response | 0 = success |
| `scripts/predict.sh` | JSON payload | JSON prediction | 0 = success |

## Available Exemplars

| Path | Type | Description |
|---|---|---|
| `templates/template_code_executor/` | `code_executor` | Generic code execution tool manifest |
| `templates/template_validator/` | `validator` | Validation tool manifest |
| `templates/template_skill/` | `skill` | Agent skill manifest |
| `templates/template_model/` | `model` | Pre-trained linear regression model, real OLS-computed coefficients |

## Extending

To add a new tool:
1. Create a subdirectory (not under `templates/` — that is for exemplars only).
2. Copy the closest exemplar's `tools.yaml` and scripts as a starting point.
3. Register the new tool in the parent `AGENTS.md` and `README.md`.
