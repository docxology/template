# `template_sia/docs/`

Documentation hub for the SIA harness exemplar.

```mermaid
flowchart LR
    HUB[template_sia/docs]
    HUB --> AI[agent_instructions.md<br/>7 hard rules · read-first]
    HUB --> ARCH[architecture.md<br/>Meta → Target → Feedback]
    HUB --> TP[testing_philosophy.md<br/>fixture replay · zero-mock]
    HUB --> RP[rendering_pipeline.md<br/>analysis → variables → PDF]
    HUB --> SG[style_guide.md<br/>thin orchestrator rules]
    HUB --> SX[syntax_guide.md<br/>SIA tokens + task layout]
    HUB --> QS[quickstart.md<br/>first run]
    HUB --> OC[output_conventions.md<br/>runs/ + reports/]
    HUB --> TS[troubleshooting.md<br/>common failures]
    HUB --> FAQ[faq.md<br/>SIA vs autoresearch]
    HUB --> FG[forking_guide.md<br/>copy this exemplar]
    HUB --> META[AGENTS.md · README.md]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef f fill:#0f766e,stroke:#0f172a,color:#fff
    class HUB d
    class AI,ARCH,TP,RP,SG,SX,QS,OC,TS,FAQ,FG,META f
```

## Quick links

| File | Purpose |
| --- | --- |
| [`agent_instructions.md`](agent_instructions.md) | Hard rules for agents modifying this project |
| [`architecture.md`](architecture.md) | Layer 1 / Layer 2 split and generation artifact tree |
| [`testing_philosophy.md`](testing_philosophy.md) | Fixture replay default; live Ollama opt-in |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Analysis scripts → manuscript tokens → PDF |
| [`style_guide.md`](style_guide.md) | Thin orchestrator and determinism conventions |
| [`syntax_guide.md`](syntax_guide.md) | `{{SIA_*}}` tokens and task directory layout |
| [`quickstart.md`](quickstart.md) | First-run commands |
| [`output_conventions.md`](output_conventions.md) | Where loop artifacts land on disk |
| [`troubleshooting.md`](troubleshooting.md) | Diagnostic flow for failed stages |
| [`faq.md`](faq.md) | SIA harness vs AutoResearch; live mode |
| [`forking_guide.md`](forking_guide.md) | Copy this exemplar for a new harness task |
| [`AGENTS.md`](AGENTS.md) | Agent-oriented walkthrough of this hub |

## Audience entry points

- **First-time agent** → [`agent_instructions.md`](agent_instructions.md), then [`architecture.md`](architecture.md)
- **New task under `tasks/`** → [`syntax_guide.md`](syntax_guide.md) + [`../../../../infrastructure/sia/AGENTS.md`](../../../../infrastructure/sia/AGENTS.md)
- **Pipeline / PDF** → [`quickstart.md`](quickstart.md) + [`rendering_pipeline.md`](rendering_pipeline.md)
- **Fork for your benchmark** → [`forking_guide.md`](forking_guide.md)

## See also

- [`../README.md`](../README.md) — project overview
- [`../AGENTS.md`](../AGENTS.md) — module map
- [`../../../../infrastructure/sia/README.md`](../../../../infrastructure/sia/README.md) — Layer 1 API
- [`../../../../docs/guides/fork-an-exemplar.md`](../../../../docs/guides/fork-an-exemplar.md) — pick the right exemplar
