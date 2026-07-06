## Abstract

`template_autopoiesis` is a combinatoric grammar that **deterministically generates
whole runnable projects**.  Given a single integer seed and a grammar of orthogonal
slots, the system produces a fully-materialized child project — complete with kernel
source, tests, analysis entry-point, and a manuscript stub — whose every byte is
traceable to that seed.

### Generation pipeline

```mermaid
flowchart LR
    G[Grammar\nconfig.yaml] --> E[Expand\nseed → Spec]
    E --> M[Materialize\nSpec → Child]
    M --> V[Verify\ntree-hash check]
    V --> S[Seal\nQR provenance]
```

### Grammar product space

```mermaid
flowchart TB
    A[primitive_domain: 5] --> EP[Effective product: 45 cells]
    T[track: 3] --> EP
    S[section_set: 3] --> EP
    EP --> TP[Total product: 360 cells]
    R[3 reserved slots, 2 options each] --> TP
```

- **Domain count**: 5
- **Effective product size**: 45
- **Total product size**: 360
- **Reserved slots**: 3 (`figure_profile, qr_profile, integrity_profile`)
- **Grammar hash**: `f84a8f9dbcb18e37`
- **Tests**: 493 · **Coverage**: 96.28%
