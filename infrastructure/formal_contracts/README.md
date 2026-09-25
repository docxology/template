# Formal Contracts

Typed block model + fail-closed checker for well-typed manuscripts.

```python
from infrastructure.formal_contracts import (
    Claim, DependencyEdge, EdgeKind, Evidence, EvidenceTier,
    FormalStatement, MatchPolicy, Section, compose, check_manuscript,
)

ms = compose([
    Section(id="sec:main", children=("claim:1", "ev:1", "def:1")),
    FormalStatement(id="def:1", kind="definition"),
    Evidence(id="ev:1", tier=EvidenceTier.STRONG),
    Claim(
        id="claim:1",
        statement="X holds",
        evidence=(
            DependencyEdge(
                target_id="ev:1",
                kind=EdgeKind.SUPPORTS,
                policy=MatchPolicy(min_tier=EvidenceTier.STRONG),
            ),
        ),
    ),
])
report = check_manuscript(ms)
assert report.ok
```

Negative controls (missing evidence, dangling ref, cycle, duplicate id)
each fail with a specific `FORMAL.*` diagnostic; see
`tests/infra_tests/formal_contracts/`.

Category-theoretic status: monoidal composition of block sequences with a
preorder-enriched dependency relation; associativity and identity are
property-tested. No further categorical structure is claimed.
