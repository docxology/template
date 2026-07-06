# Operations Diagrams

Deployment diagrams and operational workflows. Prefer linking to [`docs/_generated/active_projects.md`](../_generated/active_projects.md) instead of copying project names here.

## Docker deployment architecture

Compose definitions live in [`infrastructure/docker/docker-compose.yml`](../../infrastructure/docker/docker-compose.yml). Typical layout:

```mermaid
graph TB
    subgraph Host
        R[Repository checkout<br/>mounted read-write]
        DC[Docker Compose<br/>profiles: dev, ollama]
    end
    subgraph Containers
        DEV[research-template<br/>sleep / shell / pipeline]
        OLL[ollama optional<br/>:11434]
    end
    DC -->|build/run| DEV
    DC -->|optional profile| OLL
    R -->|bind mount| DEV
```

There is no bundled FastAPI web server in the default compose stack; port **8000** is exposed as a placeholder for optional tooling.

## Pipeline orchestration (high level)

Aligned with [`infrastructure/core/pipeline/pipeline.yaml`](../../infrastructure/core/pipeline/pipeline.yaml): clean → setup → tests → analysis → PDF → validation → optional LLM stages → copy outputs.

```mermaid
flowchart LR
    Z[Clean outputs] --> A[Setup env]
    A --> B[Infra tests]
    A --> C[Project tests]
    C --> D[Analysis]
    D --> E[PDF render]
    E --> F[Validate]
    F --> G[LLM stages<br/>optional]
    F --> H[Copy outputs]
```

Use `./run.sh --pipeline` or `scripts/runner/execute_pipeline.py`; `--core-only` skips LLM-tagged stages.

## Log rotation pipeline

```mermaid
flowchart TD
    L[Log Files<br/>projects/*/output/logs/] --> R{Check Rotation}
    R -->|Needs Rotation| C[Compress &<br/>Archive]
    R -->|No| K[Keep Current<br/>Log]
    C --> D[Delete Logs<br/>>90 days]
    K --> E[End]
    D --> E
```

## Environment setup flow

```mermaid
flowchart TD
    Start[uv sync] --> S0[scripts/pipeline/stage_00_setup.py]
    S0 --> OK{Checks pass?}
    OK -->|Yes| RS[./run.sh --help]
    OK -->|No| Fix[Fix deps / paths]
    Fix --> Start
    RS --> Done[Run pipeline or tests]
```

See [`config-wizard.md`](config-wizard.md) for commands.
