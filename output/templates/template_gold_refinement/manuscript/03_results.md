# Results: Purity Progression and Karat Grading {#sec:results}

The refinery pipeline produces a monotonically increasing purity sequence across 5 stages, reaching final purity of 99.9999999% (nine-nines) (24K (nine-nines certified)).

## Purity progression

![Purity progression across refinery stages](../output/figures/purity_progression.png){#fig:purity_progression}

| Stage | Name | Output purity | Karat | Gain |
|-------|------|--------------|-------|------|
| 1 | ore | 37.50% | 9K | Extract raw gold-bearing ore from the earth |
| 2 | smelting | 75.00% | 18K | Heat ore to separate gold from slag and dross |
| 3 | assaying | 91.67% | 22K | Test a sample to determine gold content and impurities |
| 4 | cupellation | 99.900% | 24K | Refine by blowing air through molten lead-gold alloy |
| 5 | certification | 99.9999999% (nine-nines) | 24K (nine-nines certified) | Certify purity grade and stamp hallmark |

## Karat grading scale

![Gold karat grading scale with refinery stage markers](../output/figures/karat_grading.png){#fig:karat_grading}

## Final certification

- **Final purity:** 99.9999999% (nine-nines)
- **Final karat:** 24K (nine-nines certified)
- **Total purity gain:** 90.00%
- **Nine-nines certified:** Yes
- **Nines count:** 9

## Token plan summary

The mega-madlib engine generated 8 tokens from seed 431 across 4 lexicon categories.

![Mega-madlib token distribution](../output/figures/token_density.png){#fig:token_density}

### Category distribution

| Category | Count |
|----------|-------|
| manuscript_terms | 2 |
| metallurgical_terms | 3 |
| purity_adjectives | 2 |
| refinement_verbs | 1 |

### Section distribution

| Section | Token count |
|---------|-----------|
| discussion | 1 |
| methodology | 5 |
| results | 2 |

### Provenance trace

| Variable | Category | Value | Section | Source |
|----------|----------|-------|---------|--------|
| DISCUSSION_REFINEMENT_VERB | refinement_verbs | smelting | discussion | manuscript/config.yaml#gold_refinement.lexicon.refinement_verbs[3] |
| METHOD_MANUSCRIPT_TERM_1 | manuscript_terms | evidence | methodology | manuscript/config.yaml#gold_refinement.lexicon.manuscript_terms[4] |
| METHOD_MANUSCRIPT_TERM_2 | manuscript_terms | evidence | methodology | manuscript/config.yaml#gold_refinement.lexicon.manuscript_terms[4] |
| METHOD_METAL_TERM_1 | metallurgical_terms | hallmark | methodology | manuscript/config.yaml#gold_refinement.lexicon.metallurgical_terms[4] |
| METHOD_METAL_TERM_2 | metallurgical_terms | cupellation | methodology | manuscript/config.yaml#gold_refinement.lexicon.metallurgical_terms[0] |
| METHOD_METAL_TERM_3 | metallurgical_terms | assaying | methodology | manuscript/config.yaml#gold_refinement.lexicon.metallurgical_terms[1] |
| RESULTS_PURITY_ADJ_1 | purity_adjectives | unrefined | results | manuscript/config.yaml#gold_refinement.lexicon.purity_adjectives[0] |
| RESULTS_PURITY_ADJ_2 | purity_adjectives | purified | results | manuscript/config.yaml#gold_refinement.lexicon.purity_adjectives[1] |

Selected purity adjectives for this section: unrefined, purified.

## Provenance flow

![Provenance flow diagram](../output/figures/provenance_sankey.png){#fig:provenance_sankey}

## Purity vs claim support

![Purity vs claim support](../output/figures/purity_claim_scatter.png){#fig:purity_claim_scatter}

## Token selection sensitivity

![Token selection heatmap](../output/figures/token_heatmap.png){#fig:token_heatmap}

## Contribution claims

| Claim | Statement | Evidence | Boundary |
|-------|-----------|----------|----------|
| Five-stage refinery | The refinery pipeline has 5 canonical stages from ore to nine-nines. | src/refinery.py::CANONICAL_STAGES | local |
| Monotone purity | Purity increases strictly across all refinery stages. | src/refinery.py::assert_monotone_increase | local |
| Nine-nines certification | The certification stage achieves 99.9999999% purity. | src/purity.py::NINE_NINES_PURITY | local |
| Deterministic tokens | Token selection is deterministic via seeded SHA-256 digest. | src/composition.py::_choose_value | local |
