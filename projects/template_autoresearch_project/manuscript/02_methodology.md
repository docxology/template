# Methodology {#sec:methodology}

The loop is implemented through the project source surface summarized by the
validated run artifacts. The project scripts remain thin dispatchers; reusable
behavior writes `{{AUTORESEARCH_LOOP_PATH}}`, `{{ML_RESULTS_PATH}}`,
`{{FIGURE_REGISTRY_PATH}}`, and `{{VARIABLE_PROVENANCE_PATH}}`.

## Task And Data {#sec:task-data}

The task is `{{ML_TASK_NAME}}`. The default configuration loads
`{{DATASET_PATH}}`, with provenance in `{{DATASET_PROVENANCE_PATH}}`, and uses
seed `{{ML_TASK_SEED}}`. The subset contains `{{TRAIN_SIZE}}` training images
and `{{TEST_SIZE}}` test images, with `{{DATASET_CLASS_COUNT}}` classes present
in both splits and image shape `{{IMAGE_SHAPE}}`. The provenance artifact
records upstream source-file hashes, the subset seed, class counts, and the
compressed subset hash. The default pipeline never downloads data at runtime.
The train and test splits contain `{{TRAIN_PER_CLASS_COUNT}}` and
`{{TEST_PER_CLASS_COUNT}}` examples per class, respectively. The registered
class-balance diagnostic is {{FIGURE_REF_DATASET_CLASS_BALANCE}}, and the
dataset contact sheet is {{FIGURE_REF_DATASET_CONTACT_SHEET}}.

{{FIGURE_BLOCK_DATASET_CLASS_BALANCE}}

{{CLASS_BALANCE_TABLE}}

{{FIGURE_BLOCK_DATASET_CONTACT_SHEET}}

The baseline is `{{BASELINE_ID}}` (`{{BASELINE_MODEL_TYPE_LABEL}}`). The bounded
candidate set is configured by the task artifact and covers
`{{MODEL_FAMILY_LABELS}}`, including `{{TRANSFORMER_CANDIDATE_TITLE}}` and at
least one deferred proposal. The transformer-style candidate borrows the
patch-token representation for comparison while staying inside the configured
iteration budget. This is intentionally a small configured model, not a claim
about full-scale image-transformer performance.

## Bounded Loop {#sec:bounded-loop}

The run follows `{{LOOP_STAGE_COUNT}}` configured stages:

- Resolve the human-authored program, project topic, and research questions.
- Build an `AutoResearchPlan` from the domain profile, experiment plan, and
  pipeline DAG.
- Validate exact stage-gate names declared in `autoresearch.yaml`.
- Evaluate the configured `{{DATASET_SHORT_NAME}}` candidate set up to the
  configured iteration budget.
- Generate claims only from configured questions and local artifact paths.
- Write data, reports, figures, benchmark scores, and review packets under the
  declared output contract.
- Run strict AutoResearch readiness validation and write readiness reports.

Candidates are declared in the proposal ledger and resolved from the task
configuration for execution. Each executable candidate declares a model type,
seed, training schedule, and model-specific parameters. The configured training
policy includes learning-rate decay `{{LEARNING_RATE_DECAY}}` and gradient
clipping norm `{{GRADIENT_CLIP_NORM}}`, both recorded from the validated task
run rather than described as a free-form manuscript setting. The loop evaluates
at most `{{CANDIDATE_BUDGET}}` configured iterations, selects the highest
`{{METRIC_NAME}}`, and breaks ties by lower parameter count and identifier.
Candidates outside the budget are recorded as deferred; the run-derived status
summary is `{{CANDIDATE_STATUS_SUMMARY}}`.

The closure is concrete and file-backed. `{{RESEARCH_PROGRAM_PATH}}`
constrains proposals; proposal records feed the bounded evaluation; evaluation
writes `{{ML_CANDIDATE_LEDGER_PATH}}` and `{{RUN_LEDGER_PATH}}`; ledgers support
artifact-linked claims; claims hydrate the manuscript through
`{{MANUSCRIPT_VARIABLES_PATH}}`; readiness validation writes
`{{READINESS_REPORT_PATH}}`; and review state is captured in
`{{REVIEW_DECISIONS_PATH}}`. The loop therefore maintains an inspectable
research process around a small metric result without making the process
self-approving or opaque.

The concrete closure is intentionally close to research-object and workflow-run
provenance practice. The artifact manifest lists generated objects and checksums;
the figure registry binds captions to source artifacts; the variable provenance
sidecar records the source pointer for each injected token or table; and the
review packet keeps human decisions outside generated approval. This is a
minimal local analogue of machine-readable provenance rather than a claim of
full research-object packaging.

The generated schema manifest at `{{AUTORESEARCH_SCHEMA_MANIFEST_PATH}}`
records `{{SCHEMA_MANIFEST_SCHEMA_COUNT}}` schema-versioned governance
payload(s) plus documented generic-table exemptions. The local research-object
manifest at `{{RESEARCH_OBJECT_MANIFEST_PATH}}` packages observed project paths,
hashes, the evidence registry, the source ledger, the schema manifest, and the
manual approval state. It is deliberately named a local research-object
manifest, not RO-Crate or SLSA compliance.

## Safety Controls {#sec:safety-controls}

The default autonomy level is `{{AUTONOMY_LEVEL}}`. The run ledger records
`{{LLM_CALLS_USED}}` LLM calls and USD `{{COST_USD_USED}}` cost. The edit
allowlist is restricted to the public project source and manuscript surfaces,
plus the task configuration file, and the pipeline never executes
generated code. Review gates are emitted with deferred decisions so that
validation can confirm the gates exist without pretending that the machine
approved publication.

Publication approval is a non-generated input. The run may read
`human_review.yaml` and copy its state into review payloads, but generated
readiness cannot set publication approval by itself; the default local review
state remains `{{RESEARCH_OBJECT_APPROVAL_STATE}}`.

Disclosure: `{{DISCLOSURE_TEXT}}` status is declared for this exemplar
because it models machine-produced plans, ledgers, reports, and manuscript
variables as review inputs rather than autonomous approval.

## Adversarial And Supply-Chain Controls {#sec:adversarial-supply-chain-controls}

The security layer is configured as `{{SECURITY_PROFILE_MODE}}` with network
policy `{{SECURITY_NETWORK_POLICY}}`, integrity algorithm
`{{SECURITY_INTEGRITY_ALGORITHM}}`, external signing
`{{SECURITY_EXTERNAL_SIGNING}}`, and framework labels
`{{SECURITY_FRAMEWORKS}}`. Its scope is `{{SECURITY_CLAIM_SCOPE}}`. These
values are generated from `{{AUTORESEARCH_SECURITY_PROFILE_PATH}}`; the default
run remains offline and deterministic.

The local threat model covers `{{SECURITY_ASSET_COUNT}}` asset(s),
`{{SECURITY_THREAT_COUNT}}` threat row(s), and
`{{SECURITY_CONTROL_COUNT}}` control row(s). The security artifacts are written
to `{{AUTORESEARCH_THREAT_MODEL_PATH}}`,
`{{AUTORESEARCH_SUPPLY_CHAIN_INVENTORY_PATH}}`,
`{{AUTORESEARCH_INTEGRITY_ATTESTATION_PATH}}`, and
`{{AUTORESEARCH_SECURITY_REVIEW_PATH}}`. The control-matrix figure is
{{FIGURE_REF_SECURITY_CONTROL_MATRIX}}. The table and figure are generated from
the threat model and inventory, not manually maintained.

{{FIGURE_BLOCK_SECURITY_CONTROL_MATRIX}}

{{SECURITY_ARTIFACT_TABLE}}

{{SECURITY_THREAT_MODEL_TABLE}}

## Positioning Against Autonomous Science Systems {#sec:positioning-autonomous-science}

The implementation should be read as a bounded local analogue of current
AutoResearch trends, not as a miniature autonomous scientist. Artifact
manifests, evidence registries, review gates, and manuscript hydration provide
machine-readable governance surfaces for one offline project run. They do not
perform autonomous literature mining, proof search, live agent orchestration,
runtime dataset expansion, self-modifying code search, or self-approval of
publication claims.

## Evidence And Scoring {#sec:evidence-scoring}

The experiment writes `{{ML_RESULTS_PATH}}`, `{{ML_CANDIDATE_LEDGER_PATH}}`,
`{{ML_CONFUSION_MATRIX_PATH}}`, `{{ML_TRAINING_HISTORY_PATH}}`,
`{{ML_ERROR_EXAMPLES_PATH}}`, `{{ML_PREDICTION_RECORDS_PATH}}`,
`{{ML_CLASSIFICATION_DIAGNOSTICS_PATH}}`, `{{ML_CANDIDATE_INTERVALS_PATH}}`,
`{{ML_CLASS_BALANCE_PATH}}`, `{{ML_CALIBRATION_REPORT_PATH}}`,
`{{ML_ROBUSTNESS_REPORT_PATH}}`, `{{ML_PROBABILITY_DIAGNOSTICS_PATH}}`,
`{{ML_BOOTSTRAP_INTERVALS_PATH}}`, `{{ML_PAIRED_COMPARISON_PATH}}`,
`{{ML_STATISTICAL_SUMMARY_PATH}}`, `{{ML_TRAINING_DIAGNOSTICS_PATH}}`,
`{{ML_BENCHMARK_SCORE_PATH}}`, and registered figures through
`{{FIGURE_REGISTRY_PATH}}`. The diagnostic payloads preserve probabilities,
confidence and margin summaries, class metrics, calibration bins,
confusion-pair summaries, train/test gaps, deterministic no-retrain
perturbation scores, bootstrap intervals, paired baseline comparison,
selective accuracy thresholds, Brier score, negative log likelihood, top-2
accuracy, probability-quality comparisons, learning-rate traces, best-epoch
markers, final learning rates, and train-test gap summaries without serializing
model weights. The benchmark score combines metric
improvement, budget compliance, offline execution, transformer-candidate
coverage, and candidate-selection status. Manuscript variables are hydrated from
these artifacts, and readiness validation checks `{{EVIDENCE_REGISTRY_PATH}}`,
`{{ARTIFACT_MANIFEST_PATH}}`, method ledgers, review gates, benchmark outputs,
and AI-assisted disclosure before rendering is treated as ready for review.
The generated tables and figure blocks used in @sec:results are sourced through
`{{VARIABLE_PROVENANCE_PATH}}` and `{{FIGURE_BLOCKS_PATH}}`, so captions,
artifact tables, and run-derived result statements share the same validated
artifact base.

The figure registry also carries the method contract for each visualization:
source artifact, generated file, rendering method, and claim boundary. The
rendered method table below is generated from that registry rather than
maintained manually.

{{FIGURE_METHOD_TABLE}}
