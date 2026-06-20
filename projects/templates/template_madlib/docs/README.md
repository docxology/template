# Documentation

See:

- `../README.md` for usage, generated evidence, and exemplar positioning.
- `../AGENTS.md` for editing rules.
- `../manuscript/README.md` for Madlib schema, design principles, pipeline phases, evaluation criteria, QA probes, failure modes, authoring obligations, cover/figure controls, configured-field origins, and token-shell rules.
- `../src/README.md` for module responsibilities.
- `../tests/README.md` for verification coverage.
- `../data/claim_ledger.yaml` for local method, visualization, and publication-boundary claims.

Generated documentation outputs belong under `output/`; keep durable Madlib behavior documented in tracked source docs. If a doc describes a method step, make sure the step is also declared in `manuscript/config.yaml`, implemented in `src/`, covered by tests, and regenerated through Stages 02-05.

Review-packet, digest-invariant, claim-ledger, and fork-migration language should be documented through the same source path: config rows, generated Methods prose, claim ledger, and tests. Do not describe those obligations only in a freeform doc.
