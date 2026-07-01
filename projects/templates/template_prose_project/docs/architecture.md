# Architecture

## Two-Layer Compliance

```mermaid
flowchart TB
    subgraph L1 [Layer 1 - Infrastructure]
        PROSE["infrastructure/prose/<br/>readability · structure · quality"]
        REF["infrastructure/reference/<br/>BibTeX read/write/convert"]
    end

    subgraph L2 [Layer 2 - Project orchestration]
        CFG["src/config.py<br/>typed YAML loader"]
        PIPE["src/pipeline/<br/>read → analyse → check"]
        FIG["src/figures.py<br/>matplotlib renderers"]
        MV["src/manuscript_variables.py<br/>abstract substitution"]
        REP["src/report.py<br/>markdown review report"]
    end

    subgraph SCR [Thin orchestrators]
        S1[scripts/run_prose_pipeline.py]
        S2[scripts/y_generate_prose_figures.py]
        S3[scripts/z_generate_manuscript_variables.py]
    end

    L1 --> L2
    L2 --> SCR

    PIPE -.uses.-> PROSE
    PIPE -.uses.-> REF

    classDef l1 fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef l2 fill:#0f766e,stroke:#0f172a,color:#fff
    classDef sc fill:#7c2d12,stroke:#0f172a,color:#fff
    class PROSE,REF l1
    class CFG,PIPE,FIG,MV,REP l2
    class S1,S2,S3 sc
```

## Data flow

```mermaid
sequenceDiagram
    participant CLI as scripts/run_prose_pipeline.py
    participant CFG as load_project_config
    participant PIPE as run_prose_pipeline
    participant PROSE as infrastructure.prose
    participant REF as infrastructure.reference
    participant FS as Filesystem
    participant REP as write_review_report

    CLI->>CFG: load_project_config(yaml)
    CFG-->>CLI: ProjectConfig
    CLI->>PIPE: run_prose_pipeline(config, root)
    PIPE->>PROSE: analyze_manuscript(manuscript_dir)
    PROSE-->>PIPE: ManuscriptReport
    PIPE->>REF: parse_bibfile(references_path)
    REF-->>PIPE: BibDatabase
    PIPE->>PIPE: evaluate checks
    PIPE->>FS: write manuscript_report.json + checks.json
    PIPE-->>CLI: ProseRunArtifacts
    CLI->>REP: write_review_report(...)
    REP->>FS: write review_report.md
```

## Why These Exemplar Shapes?

The permanent `template_*_project` exemplars cover the always-on computational
and prose-review paths; the optional search add-on covers literature discovery:

| Project | Workflow | Algorithm? | Mutates `references.bib`? |
|---|---|---|---|
| `template_code_project` | Numerical experiment + analysis | yes (`src/optimizer.py`) | no |
| `template_prose_project` | Editorial review (readability + structure + bibliography) | no | no (read-only validation) |
| `template_search_project` | Literature discovery → BibTeX → LLM synthesis | no | yes (auto-populates) |

The infrastructure modules are deliberately small and stable; each
exemplar is small and explicit. New projects pick whichever shape is
closest and adjust from there.
