# `template_prose_project/docs/`

Documentation hub for the prose-review exemplar.

```mermaid
flowchart LR
    HUB[/template_prose_project/docs//]
    HUB --> QS[quickstart.md<br/>5-step getting started]
    HUB --> ARCH[architecture.md<br/>two-layer compliance + sequence diagram]
    HUB --> OC[output_conventions.md<br/>where every artefact lands]
    HUB --> TS[troubleshooting.md<br/>diagnostic flowchart]
    HUB --> META[AGENTS.md · README.md]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef f fill:#0f766e,stroke:#0f172a,color:#fff
    class HUB d
    class QS,ARCH,OC,TS,META f
```

## Quick links

| File | Purpose |
|---|---|
| [`quickstart.md`](quickstart.md) | 5-step getting-started flow. |
| [`architecture.md`](architecture.md) | Two-layer compliance and data-flow diagrams. |
| [`output_conventions.md`](output_conventions.md) | Where every artefact lands on disk. |
| [`troubleshooting.md`](troubleshooting.md) | Diagnostic flowchart for common failures. |
| [`AGENTS.md`](AGENTS.md) | Agent-oriented walkthrough of this hub. |

## See also

* Project [`README.md`](../README.md) — top-level project overview.
* Project [`AGENTS.md`](../AGENTS.md) — agent walkthrough.
* [`infrastructure/prose/SKILL.md`](../../../infrastructure/prose/SKILL.md) — underlying API.
