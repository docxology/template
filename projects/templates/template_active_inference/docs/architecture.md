# Architecture — Active Inference Exemplar

## Track Architecture

```mermaid
flowchart TB
    subgraph tracks ["Research Tracks"]
        A[analytical<br/>Bernoulli K=2, MI/FE/EFE]
        S[simulation<br/>pymdp SI T-maze]
        G[GNN<br/>concordance parser]
        O[ontology<br/>term flattening]
        L[Lean<br/>formalization boundary]
        SH[sheaf manuscript<br/>registry + composition]
    end
    SH --> A & S & G & O & L
    VIZ[visualizations] --> SH
    GATES[gates] --> SH

    classDef t fill:#1e3a8a,color:#fff;
    class A,S,G,O,L,SH,VIZ,GATES t;
```

## Key source of truth files

- `tracks.yaml`: Pipeline track gates
- `manuscript/sheaf/tracks.yaml`: Manuscript sheaf registry
- `manuscript/sheaf/manifest.yaml`: IMRAD section matrix
- `figures.yaml`: Figure registry, captions, alt text
