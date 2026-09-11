# Architecture — AutoScientists

## Coordination Loop

The five coordination mechanisms from Gao, Fang & Zitnik (arXiv:2605.28655),
implemented deterministically:

1. **Shared champion/experiment-log state** — `SharedState` in `src/template_autoscientists/analysis/state.py`
2. **Dead-end registry** — `DeadEndRegistry` in `src/template_autoscientists/search/dead_ends.py`
3. **Effect-size ranking** — `rank_axes` in `src/template_autoscientists/search/ranking.py`
4. **Noise-band confirmation** — `confirm_improvement` in `src/template_autoscientists/analysis/confirmation.py`
5. **Stagnation-driven reorganization** — `StagnationDetector` in `src/template_autoscientists/search/stagnation.py`

## Data flow

```mermaid
flowchart LR
    O[objective] --> LOOP[Search Loop]
    LOOP --> P[Proposer]
    P --> CON[Confirmation]
    CON --> PROM[Promotion]
    PROM --> STAG[Stagnation]
    STAG --> REG[Dead-end Registry]
    REG --> LOOP

    classDef core fill:#1e3a8a,color:#fff;
    class O,LOOP,P,CON,PROM,STAG,REG core;
```
