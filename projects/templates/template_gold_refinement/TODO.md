# TODO — template_gold_refinement

Forward-only integrity backlog for the metallurgical gold-refining analogy
exemplar. This tree is part of the public template roster and must satisfy the
same forkability contract as the other exemplars.

## Current validation evidence

- 217 tests pass at 98.87% coverage on `src/` (90% gate enforced)
- Ruff lint clean on `src/`, `tests/`, and `scripts/`
- Mypy type-check clean on `src/`
- Refinery pipeline runs end-to-end: ore (9K) → nine-nines certification
- All manuscript `{{TOKEN}}` variables resolve with zero unresolved tokens
- `check_tracked_projects.py` passes (confidentiality guard)
- `check_template_drift.py --strict` passes (no drift)
- Figure generation: 6 figures (purity progression, karat grading, token density,
  provenance Sankey, purity-claim scatter, token heatmap)
- Evidence registry: `src/evidence.py` cross-checks contribution claims
- Interactive HTML dashboard: `src/dashboard.py` with refinery metrics
- Mega-madlib token injection: deterministic, seeded, config-owned lexicon
- Config blocks: contribution_claims, pipeline_phases, audit_rules
- Docs subtree: architecture, testing philosophy, style guide, syntax guide,
  FAQ, quickstart, output conventions, troubleshooting, agent instructions
- Manuscript staleness detection in `src/manuscript_variables.py`
- Claim-ledger alignment test
- Negative-control tests for broken configs and purity values
- Figure-registry validation: every `[@fig:...]` cross-checked
- Bug fix: `generate_purity_claim_scatter` evidence path corrected (was using `.parent`)
- Edge-case tests: _check_evidence_source (#/:: paths, missing files/symbols),
  dashboard category+evidence rows, figure None-path fallbacks, staleness detection,
  SOURCE_DATE_EPOCH, config branch misses, composition empty-lexicon error path

## integrity and template-status gaps

- [x] Add figure generation (purity progression, karat grading, token density)
  to `src/figures.py`
- [ ] Add steganography profile to `manuscript/config.yaml` when secure
  pipeline is needed
- [ ] Add LLM review enablement when Ollama is available
- [x] Add `contribution_claims` config block for generated method claims
- [x] Add `pipeline_phases` config block for stage-level provenance
- [x] Add `audit_rules` config block for compliance tracking

## configurable-surface gaps

- [x] Add `contribution_claims` to `manuscript/config.yaml.example` fork template
- [x] Add `pipeline_phases` to `manuscript/config.yaml.example` fork template
- [x] Add `audit_rules` to `manuscript/config.yaml.example` fork template
- [x] Add `evaluation` and `authoring_contract` narrative moves to config.yaml.example
- [x] Add steganography and render format blocks to config.yaml.example

## documentation and signposting gaps

- [x] Add `docs/` subtree with architecture and testing philosophy
- [x] Add `docs/style_guide.md` for coding conventions
- [x] Add `docs/syntax_guide.md` for manuscript syntax reference
- [x] Add `docs/faq.md` for common questions
- [x] Add `docs/quickstart.md` for getting started
- [x] Add `docs/output_conventions.md` for output file layout
- [x] Add `docs/troubleshooting.md` for common errors
- [x] Add `docs/agent_instructions.md` for AI agent guidance

## test and validator gaps

- [x] Add property-based tests for purity monotonicity across refinery stages
- [x] Add subprocess smoke tests for `refinement_analysis.py` and
  `z_generate_manuscript_variables.py`
- [x] Add figure generation tests (non-blank PNG, registry, labels)
- [x] Add negative-control tests for malformed karat grades
- [x] Add cross-reference integrity test for `[@fig:...]` labels
- [x] Add evidence-registry validation test
- [x] Add claim-ledger alignment test
- [x] Add manuscript staleness detection

## ordered improvement ladder

### Phase 1: Figure generation and visualizations (complete)

1. [x] Create `src/figures.py` with purity progression chart
2. [x] Add karat grading chart
3. [x] Add token density chart
4. [x] Write `figure_registry.json` from `generate_all_figures()`
5. [x] Add figure tests in `tests/test_figures.py`

### Phase 2: Config enrichment (complete)

1. [x] Add `contribution_claims` config block + schema field + parsing
2. [x] Add `pipeline_phases` config block + schema field + parsing
3. [x] Add `audit_rules` config block + schema field + parsing
4. [x] Add `evaluation` and `authoring_contract` sections
5. [x] Update `manuscript_variables.py` to emit all new config-derived tables

### Phase 3: Manuscript expansion (complete)

1. [x] Add figure references (`[@fig:...]`) to abstract, methodology, results
2. [x] Add mathematical equations (monotone purity, token digest)
3. [x] Add `08_evaluation.md` with QA probes and audit rules tables
4. [x] Add `09_authoring_contract.md` with obligations and fork checklist
5. [x] Update all manuscript sections with deeper content

### Phase 4: Documentation hub (complete)

1. [x] Add `docs/architecture.md`
2. [x] Add `docs/testing_philosophy.md`
3. [x] Add `docs/style_guide.md`
4. [x] Add `docs/syntax_guide.md`
5. [x] Add `docs/faq.md`
6. [x] Add `docs/quickstart.md`
7. [x] Add `docs/output_conventions.md`
8. [x] Add `docs/troubleshooting.md`
9. [x] Add `docs/agent_instructions.md`

### Phase 5: Research integrity deepening (complete)

1. [x] Add evidence registry (`src/evidence.py`) that cross-checks every
      manuscript claim against its evidence source
2. [x] Add claim-ledger alignment test that verifies `data/claim_ledger.yaml`
      entries match `contribution_claims` config block
3. [x] Add negative-control tests: feed deliberately broken configs and verify
      the refinery rejects them (non-monotone purity, empty lexicon, etc.)
4. [x] Add manuscript staleness detection: compare `output/manuscript/` against
      source `manuscript/` to detect stale rendered output
5. [x] Add figure-registry validation test: every `[@fig:...]` in manuscript
      must have a registry entry

### Phase 6: Advanced visualization (complete)

1. [x] Add interactive HTML dashboard (`src/dashboard.py`) showing refinery metrics
2. [x] Add provenance trace Sankey diagram (ore → stages → certification)
3. [x] Add purity-vs-claim-support scatter plot
4. [x] Add token selection heatmap (seed × category → selected value)

### Phase 7: Domain extension and forking (future)

1. [ ] Create a domain-specific fork guide showing how to remap stages to
      clinical evidence, legal citation, or engineering specification domains
2. [ ] Add a "domain adapter" pattern in `src/` that translates domain-specific
      quality metrics into the refinery's purity scale
3. [ ] Document the analogy-break boundary: where does gold-refining fail as a
      model for manuscript composition?

### Phase 8: Publishing and provenance (future)

1. [ ] Add `.zenodo.json` for Zenodo deposit integration
2. [ ] Add `manuscript/config.yaml` DOI fields when published
3. [ ] Add transmission bookends (transmission_begin/end manuscript sections)
4. [ ] Add steganography profile for secure pipeline (`secure_run.sh`)
5. [ ] Add LLM review enablement (`manuscript/config.yaml` llm block)

### Phase 9: Deeper analogy research (future)

1. [ ] Formalize the analogy-break boundary as a theorem: for what class of
      manuscript quality processes does the gold-refining analogy hold?
2. [ ] Add a "reverse assay" mode: given a target purity, compute the minimum
      set of refinery stages needed to reach it
3. [ ] Add multi-objective purity: purity as a vector (claim support, citation
      density, evidence coverage) rather than a scalar
4. [ ] Connect the refinery to real manuscript validation infrastructure
      (`infrastructure.validation`) and measure actual purity on a real paper
