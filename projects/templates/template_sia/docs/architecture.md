# Architecture — template_sia

## Two-layer split

```mermaid
flowchart TB
  subgraph L1 [Layer 1 infrastructure/sia]
    TL[task_layout]
    EL[execution_logs]
    ER[evaluation_runner]
    CL[context_ledger]
    LR[loop_runner]
  end

  subgraph L2 [Layer 2 template_sia/src]
    LOOP[loop.py]
    CFG[loop_config.py]
    REP[reports.py]
  end

  subgraph TASK [tasks/mini_classify]
    PUB[data/public]
    PRIV[data/private]
    REF[reference/]
  end

  SCR[scripts/run_sia_loop.py] --> LOOP
  LOOP --> LR
  LR --> TL
  LR --> ER
  LR --> CL
  LOOP --> TASK
  LR -->|live=False| FIX[src/fixtures/]
  LR -->|live=True| LLM[infrastructure/llm]
```

| Layer | Location | Owns |
| --- | --- | --- |
| Layer 1 | `infrastructure/sia/` | Task validation, evaluation subprocess, context ledger, generation state machine |
| Layer 2 | `projects/templates/template_sia/src/` | Project config, fixture paths, manuscript variables, task-specific reference agent |
| Orchestration | `scripts/` | CLI flags (`--live-sia`), stdout paths for manifest collection |

## Generation artifact tree

Each run writes:

```
output/runs/run_{id}/
  context.md
  run_summary.json
  gen_{n}/
    target_agent.py
    agent_execution.json
    improvement.md
    results.json
```

Fixture replay copies recorded artifacts from `src/fixtures/recorded_generations/gen_{n}/` when `live=False`.

## Comparison with template_autoresearch_project

| | `template_sia` | `template_autoresearch_project` |
| --- | --- | --- |
| Goal | Benchmark self-improvement harness | Readiness / evidence / claim gates |
| Loop | Meta → Target → Feedback generations | AutoResearch plan validation |
| Default path | Fixture replay | Deterministic ML loop fixtures |

Do not merge these loops — they answer different research questions.
