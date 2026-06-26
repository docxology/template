# Discussion: Load-Bearing vs Rhetorical Analogy {#sec:discussion}

## Load-bearing vs rhetorical

The gold-refining analogy operates on two levels. **Rhetorically**, it provides a memorable framing for a methods paper: purity progression, karat grading, and certification are vivid metaphors for manuscript quality. **Operationally**, each stage maps to a real template-infrastructure operation — smelting to claim removal, assaying to evidence validation, cupellation to cross-reference resolution, and certification to full pipeline validation.

The analogy is smelting the manuscript: it performs the refinement it describes.

## Useful adaptation cases

- **Domain-specific refinement pipelines**: fork the exemplar and remap stages to domain operations (e.g., clinical evidence, legal citation, engineering specification).
- **Purity measurement**: adopt the purity fraction and karat grade vocabulary for any staged quality process.
- **Mega-madlib composition**: reuse the deterministic token engine for any config-owned lexical composition task.

## Misuse modes

| Mode | Risk | Detection | Mitigation |
|------|------|-----------|------------|
| Non-monotone purity | A stage has lower output purity than input. | assert_monotone_increase raises ValueError. | Fix stage purity targets in src/refinery.py. |
| Empty lexicon category | A required lexicon category is empty or missing. | Config validation raises GoldRefinementConfigError. | Add vocabulary to manuscript/config.yaml. |
| Unresolved token | A manuscript placeholder has no generated variable. | test_all_manuscript_tokens_are_generated fails. | Add variable in src/manuscript_variables.py. |
| Rhetorical-only analogy | The analogy is decorative with no operational mapping. | Review that each stage maps to a real infrastructure operation. | Connect stages to template pipeline operations. |

## Design principles

| Principle | Rationale |
|-----------|-----------|
| Analogy is load-bearing | Each metallurgical stage maps to a real template-infrastructure operation, not mere decoration. |
| Purity increases monotonically | The refinery pipeline guarantees strictly increasing purity from ore to certification. |
| Token selection is deterministic | A fixed seed and lexicon produce the same injection plan across reruns. |
| Configuration owns prose choices | Reviewers can inspect the declared language surface before generation. |
| Generated output is disposable | The durable artifact is the regeneration contract, not hand-edited output. |
