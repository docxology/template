# template_advanced_literature_review TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
proving artifact, acceptance command, and negative control; absence of an owner or external receipt
keeps a capability blocked rather than silently promoting it.

## Backlog operating rules

- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.
- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.
- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips
  or blockers.
- Re-derive counts and receipts from live source data; never copy measurements into this planning file.

## Integrity and template-status gaps

- Keep the offline corpus clearly marked as synthetic; live DOI sources require source-tier provenance and attribution in README, manuscript, and generated-output prose.
- Keep `output/data/phase_artifact_manifest.json` phase-aware for every corpus,
  metadata, and validation artifact; extend it before adding a new artifact
  family.
- Add cross-phase conflict and knowledge-graph calibration validators without
  allowing structural evidence to be presented as an empirical result.
- Keep `data/subfield_defaults_exoplanet.yaml` tied to project-local configuration, not borrowed from sibling exemplars.

## Configurable-surface gaps

- Retargeting should remain config-owned through `manuscript/config.yaml` phase definitions; avoid hard-coded domain terms in multi-phase `src/` modules.
- Keep phase temporal boundaries, filtering criteria, and LLM prompts explicit and configurable.
- Ensure new domains can define their own methodological phases without code changes.

## Documentation and signposting gaps

- Keep README, AGENTS, and `docs/_generated/exemplar_roster.md` synchronized through the generator.
- Document multi-phase architecture distinctly from single-term template capabilities.
- Keep troubleshooting examples specific to multi-phase scenarios (phase filtering failures, cross-phase validation conflicts).

## Test and validator gaps

The open work below should add tests or validators before promoting new claim surfaces.

## Multi-Phase Specific Considerations

- **Phase Definition Discipline**: New phases should have clear temporal boundaries, distinct methodological focus, and appropriate filtering criteria.
- **Cross-Phase Validation**: Later phases should validate, not merely supplement, earlier phase findings.
- **LLM Filter Calibration**: Abstract content filtering requires domain-specific calibration datasets for reliable precision/recall.
- **Temporal Coherence**: Phase-aware statistics must handle temporal overlaps and methodological transitions gracefully.

## Minor upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `ARL-PHASE-VALIDATION-1` | Minor | Phase configuration schema | phase-boundary validation receipt | phase configuration tests and replay gate | invalid temporal bounds must fail before replay |

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `ARL-CROSS-PHASE-1` | Medium | Cross-phase evidence schema | cross-phase conflict receipt | cross-phase validation test with conflicting evidence | structural overlap must not count as causal support |
| `ARL-LLM-FILTER-1` | Medium | Calibration corpus and opt-in provider | calibration fixture bundle | LLM filter tests with known positive/negative examples | unavailable provider must report skip, not pass |
| `ARL-PHASE-PROVENANCE-1` | Medium | Phase artifact manifest | all `output/` artifacts with phase metadata | provenance audit across full pipeline | artifact without phase provenance must fail |

## Major upcoming

No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
