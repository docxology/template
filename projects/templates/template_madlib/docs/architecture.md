# Architecture — Template Madlib

## Pipeline

```mermaid
flowchart LR
    CONFIG[config.yaml<br/>madlib: block] --> PARSE[src/config.py<br/>ParseConfig]
    PARSE --> TOKENS[src/tokens.py<br/>TokenExpansion]
    TOKENS --> COMPOSE[src/composition.py<br/>ComposeManuscript]
    COMPOSE --> HYD[scripts/z_generate<br/>_manuscript_variables.py]
    HYD --> RENDER[Stage 03: PDF Render]

    classDef c fill:#1e3a8a,color:#fff;
    class CONFIG,PARSE,TOKENS,COMPOSE,HYD,RENDER c;
```

## Key modules

- `src/config.py`: Parses the madlib schema from config.yaml
- `src/tokens.py`: Deterministic token selection and expansion
- `src/composition.py`: Manuscript section composition and hydration
- `src/manuscript_variables.py`: Token-to-variable mapping for injection
