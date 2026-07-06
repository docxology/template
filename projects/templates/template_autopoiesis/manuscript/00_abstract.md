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
    A[primitive_domain: 5] --> EP[Effective product: {{EFFECTIVE_PRODUCT_SIZE}} cells]
    T[track: 3] --> EP
    S[section_set: 3] --> EP
    EP --> TP[Total product: {{PRODUCT_SIZE}} cells]
    R[3 reserved slots, 2 options each] --> TP
```

- **Domain count**: {{DOMAIN_COUNT}}
- **Effective product size**: {{EFFECTIVE_PRODUCT_SIZE}}
- **Total product size**: {{PRODUCT_SIZE}}
- **Reserved slots**: {{RESERVED_SLOT_COUNT}} (`{{RESERVED_SLOT_NAMES}}`)
- **Grammar hash**: `{{GRAMMAR_HASH}}`
- **Tests**: {{TEST_COUNT}} · **Coverage**: {{COVERAGE_PCT}}%
