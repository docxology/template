# Results: Provenance, Density, and Resolved Manuscript Surface

The generated plan enables 11 of 11 manuscript sections and fills 40 token choice(s). Category density is adjectives: 2, artifacts: 8, audiences: 4, constraints: 3, failures: 3, measures: 6, methods: 1, nouns: 5, qualities: 3, verbs: 5. The result figures are generated from the same token plan that writes the inventory table, so visual and tabular claims share one source.

The configured results moves are report token density, show resolved section coverage, bind every manuscript token to provenance, and connect the figure and inventory to the same plan. The important result is therefore not a surprising word choice; it is the survival of traceability through a complete render path. Each token row records the variable, category, selected value, section, and config pointer that produced it.

The resolved manuscript also demonstrates the intended failure boundary. If a manuscript placeholder is added without a corresponding variable, the project test suite detects it. If a figure is referenced without registry support, the output validator reports it. If a generated number lacks evidence support, the evidence registry gate reports it before the copied output stage packages deliverables.

Visualization is enabled for configured_field_matrix, section_configuration_heatmap, field_origin_summary, token_injection_flow, section_token_allocation, provenance_trace_map, quality_gate_matrix. The configured-field figures are generated from the same explicit/default path inventory written to JSON; the pipeline, allocation, provenance, and gate figures are generated from the same token plan and QA schema.

![Token category density](../output/figures/token_density.png){#fig:token-density}

![Section token allocation](../output/figures/section_token_allocation.png){#fig:section-token-allocation}

![Provenance trace map](../output/figures/provenance_trace_map.png){#fig:provenance-trace-map}

## Token Inventory

| Variable | Category | Value | Section | Source |
| --- | --- | --- | --- | --- |
| `STUDY_ADJECTIVE` | adjectives | reviewable | abstract | `manuscript/config.yaml#madlib.lexicon.adjectives[5]` |
| `STUDY_NOUN` | nouns | pipeline | abstract | `manuscript/config.yaml#madlib.lexicon.nouns[4]` |
| `STUDY_VERB` | verbs | hydrate | abstract | `manuscript/config.yaml#madlib.lexicon.verbs[1]` |
| `INTRO_NOUNS_1` | nouns | protocol | introduction | `manuscript/config.yaml#madlib.lexicon.nouns[5]` |
| `INTRO_NOUNS_2` | nouns | section | introduction | `manuscript/config.yaml#madlib.lexicon.nouns[3]` |
| `INTRO_NOUNS_3` | nouns | lexicon | introduction | `manuscript/config.yaml#madlib.lexicon.nouns[2]` |
| `INTRO_NOUNS_4` | nouns | artifact | introduction | `manuscript/config.yaml#madlib.lexicon.nouns[6]` |
| `INTRO_VERBS_1` | verbs | condition | introduction | `manuscript/config.yaml#madlib.lexicon.verbs[3]` |
| `INTRO_VERBS_2` | verbs | bind | introduction | `manuscript/config.yaml#madlib.lexicon.verbs[6]` |
| `INTRO_VERBS_3` | verbs | bind | introduction | `manuscript/config.yaml#madlib.lexicon.verbs[6]` |
| `INTRO_VERBS_4` | verbs | compose | introduction | `manuscript/config.yaml#madlib.lexicon.verbs[0]` |
| `METHOD_NAME` | methods | conditional section hydration | methods | `manuscript/config.yaml#madlib.lexicon.methods[3]` |
| `METHOD_CONSTRAINT` | constraints | publication claims stay local until release | methods | `manuscript/config.yaml#madlib.lexicon.constraints[3]` |
| `METHOD_ARTIFACT_1` | artifacts | token-injection flow | methods | `manuscript/config.yaml#madlib.lexicon.artifacts[6]` |
| `METHOD_ARTIFACT_2` | artifacts | quality-gate matrix | methods | `manuscript/config.yaml#madlib.lexicon.artifacts[9]` |
| `METHOD_QUALITY_1` | qualities | claim humility | methods | `manuscript/config.yaml#madlib.lexicon.qualities[4]` |
| `METHOD_QUALITY_2` | qualities | render readiness | methods | `manuscript/config.yaml#madlib.lexicon.qualities[3]` |
| `RESULT_MEASURE_1` | measures | provenance coverage | results | `manuscript/config.yaml#madlib.lexicon.measures[3]` |
| `RESULT_MEASURE_2` | measures | evidence registry cleanliness | results | `manuscript/config.yaml#madlib.lexicon.measures[6]` |
| `RESULT_MEASURE_3` | measures | category density | results | `manuscript/config.yaml#madlib.lexicon.measures[2]` |
| `RESULT_ARTIFACT_1` | artifacts | configured-field figures | results | `manuscript/config.yaml#madlib.lexicon.artifacts[10]` |
| `RESULT_ARTIFACT_2` | artifacts | token inventory | results | `manuscript/config.yaml#madlib.lexicon.artifacts[0]` |
| `DISCUSSION_ADJECTIVE` | adjectives | auditable | discussion | `manuscript/config.yaml#madlib.lexicon.adjectives[0]` |
| `DISCUSSION_AUDIENCE_1` | audiences | pipeline maintainers | discussion | `manuscript/config.yaml#madlib.lexicon.audiences[2]` |
| `DISCUSSION_AUDIENCE_2` | audiences | research educators | discussion | `manuscript/config.yaml#madlib.lexicon.audiences[3]` |
| `CONFIG_CONSTRAINT` | constraints | disabled sections retain explicit traceability | configuration | `manuscript/config.yaml#madlib.lexicon.constraints[2]` |
| `EVALUATION_MEASURE_1` | measures | copied output readiness | evaluation | `manuscript/config.yaml#madlib.lexicon.measures[7]` |
| `EVALUATION_MEASURE_2` | measures | figure registry completeness | evaluation | `manuscript/config.yaml#madlib.lexicon.measures[5]` |
| `EVALUATION_MEASURE_3` | measures | category density | evaluation | `manuscript/config.yaml#madlib.lexicon.measures[2]` |
| `EVALUATION_ARTIFACT_1` | artifacts | manuscript variable map | evaluation | `manuscript/config.yaml#madlib.lexicon.artifacts[3]` |
| `EVALUATION_ARTIFACT_2` | artifacts | provenance trace map | evaluation | `manuscript/config.yaml#madlib.lexicon.artifacts[8]` |
| `REPRODUCIBILITY_ARTIFACT_1` | artifacts | section plan | reproducibility | `manuscript/config.yaml#madlib.lexicon.artifacts[1]` |
| `REPRODUCIBILITY_ARTIFACT_2` | artifacts | manuscript variable map | reproducibility | `manuscript/config.yaml#madlib.lexicon.artifacts[3]` |
| `LIMITATION_FAILURE_1` | failures | domain misuse | limitations | `manuscript/config.yaml#madlib.lexicon.failures[4]` |
| `LIMITATION_FAILURE_2` | failures | overclaimed generated prose | limitations | `manuscript/config.yaml#madlib.lexicon.failures[1]` |
| `LIMITATION_FAILURE_3` | failures | figure provenance gap | limitations | `manuscript/config.yaml#madlib.lexicon.failures[3]` |
| `SCOPE_CONSTRAINT` | constraints | all lexicon entries live in config | scope | `manuscript/config.yaml#madlib.lexicon.constraints[1]` |
| `SCOPE_AUDIENCE` | audiences | pipeline maintainers | scope | `manuscript/config.yaml#madlib.lexicon.audiences[2]` |
| `AUTHORING_AUDIENCE` | audiences | manuscript reviewers | authoring_contract | `manuscript/config.yaml#madlib.lexicon.audiences[1]` |
| `AUTHORING_QUALITY` | qualities | render readiness | authoring_contract | `manuscript/config.yaml#madlib.lexicon.qualities[3]` |

## Provenance Matrix

| Section | Token variables | Source categories |
| --- | ---: | --- |
| Abstract | `STUDY_ADJECTIVE`, `STUDY_NOUN`, `STUDY_VERB` | adjectives, nouns, verbs |
| Introduction: Lexicon as Data and Manuscript as Build Artifact | `INTRO_NOUNS_1`, `INTRO_NOUNS_2`, `INTRO_NOUNS_3`, `INTRO_NOUNS_4`, `INTRO_VERBS_1`, `INTRO_VERBS_2`, `INTRO_VERBS_3`, `INTRO_VERBS_4` | nouns, verbs |
| Methods: Source-Owned Token Injection and Conditional IMRAD Assembly | `METHOD_NAME`, `METHOD_CONSTRAINT`, `METHOD_ARTIFACT_1`, `METHOD_ARTIFACT_2`, `METHOD_QUALITY_1`, `METHOD_QUALITY_2` | artifacts, constraints, methods, qualities |
| Results: Provenance, Density, and Resolved Manuscript Surface | `RESULT_MEASURE_1`, `RESULT_MEASURE_2`, `RESULT_MEASURE_3`, `RESULT_ARTIFACT_1`, `RESULT_ARTIFACT_2` | artifacts, measures |
| Discussion: Accountability Boundaries for Generated Prose | `DISCUSSION_ADJECTIVE`, `DISCUSSION_AUDIENCE_1`, `DISCUSSION_AUDIENCE_2` | adjectives, audiences |
| Configuration: Schema-Controlled Lexicon, Slots, and Narrative Moves | `CONFIG_CONSTRAINT` | constraints |
| Evaluation: Gate Criteria, QA Probes, and Failure Discovery | `EVALUATION_MEASURE_1`, `EVALUATION_MEASURE_2`, `EVALUATION_MEASURE_3`, `EVALUATION_ARTIFACT_1`, `EVALUATION_ARTIFACT_2` | artifacts, measures |
| Reproducibility: Seeded Regeneration and Artifact Trace | `REPRODUCIBILITY_ARTIFACT_1`, `REPRODUCIBILITY_ARTIFACT_2` | artifacts |
| Limitations: Non-Claims, Misuse Modes, and Human Review | `LIMITATION_FAILURE_1`, `LIMITATION_FAILURE_2`, `LIMITATION_FAILURE_3` | failures |
| Scope: Related Generators and Responsible Forking | `SCOPE_CONSTRAINT`, `SCOPE_AUDIENCE` | audiences, constraints |
| Authoring Contract: Human Review and Forking Obligations | `AUTHORING_AUDIENCE`, `AUTHORING_QUALITY` | audiences, qualities |
