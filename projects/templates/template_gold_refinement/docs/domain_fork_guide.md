# Domain Fork Guide

This exemplar is designed to be forked, but only after the analogy is remapped to a real domain. The gold-refining metaphor is load-bearing for staged purification, not a claim that gold explains every quality process.

## Start here

1. Copy the exemplar.
2. Replace the stage labels with domain operations.
3. Replace the benchmark metrics with domain-specific measurements.
4. Add a validator that can fail on the domain's own terms.
5. Keep the analogy boundary explicit in prose and config.

## Stage remap patterns

| Canonical stage | Clinical evidence | Legal citation | Engineering specification |
|---|---|---|---|
| ore | ingest the raw literature corpus | gather source documents and pleadings | ingest requirements and design notes |
| smelting | remove duplicates and irrelevant studies | remove non-controlling authority | remove ambiguity and duplicated requirements |
| assaying | check risk of bias and evidence support | check citation authority and pinpoint accuracy | check traceability to implementation and tests |
| cupellation | resolve cross-references and reporting gaps | resolve cross-references and exhibit labels | resolve API references and interface contracts |
| certification | run publication gate and reproducibility checks | run brief-quality and filing checks | run release readiness and verification checks |

## Domain adapter pattern

Use `src/domain_adapter.py` as the translation layer:

- `domain_profile.yaml` owns the stage map, metric weights, and boundary notes.
- `load_domain_profile()` reads the profile from disk.
- `DomainAdapterProfile.purity_from_metrics()` converts domain measurements into the same 0 to 1 purity scale used by the exemplar.
- `stage_rows()` and `metric_rows()` provide machine-readable tables for reports or manuscripts.

The profile should be rewritten, not merely renamed, when the fork changes domain semantics. If a domain uses different quality units, add metric bounds in the profile instead of burying the conversion in a script.

## Secure pipeline and optional review gates

The gold-refinement exemplar now carries two explicit policy surfaces in `manuscript/config.yaml`:

- `steganography:` for secure PDF post-processing
- `llm.reviews:` for optional review generation when Ollama is available and the run is explicitly opted in

Use `src/pipeline_policy.py` to evaluate those gates. The secure-pipeline profile should stay declarative so a fork can tell, before execution, whether the pipeline is meant to watermark, seal, or encrypt outputs.

## Analogy boundary

The analogy stops when purity becomes a rhetorical score detached from evidence. A fork must not reuse the gold-refining language as if it were domain proof.

Keep these non-claims explicit:

- The analogy is not universal.
- Purity does not replace expert review.
- A good render is not the same as a valid domain claim.

## Checklist

- Update `manuscript/config.yaml` with the new domain lexicon and stage map.
- Update `contribution_claims` with domain-owned evidence pointers.
- Replace or extend the adapter profile before reusing certification language.
- Keep a source-owned validator for the domain's failure modes.
- Regenerate the outputs after every substantive change.
