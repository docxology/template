# Methodology

The loop is implemented in `src/loop.py`, with reusable ML-task behavior in
`src/ml_task.py`, artifact writing in `src/writers.py`, figures in
`src/figures.py`, and manuscript-variable hydration in
`src/manuscript_variables.py`. The project scripts remain thin dispatchers.

## Task And Data

The task is deterministic MNIST digit classification. The default configuration
loads `data/mnist_tiny.npz`, a local balanced subset derived from the canonical
MNIST files with seed `{{ML_TASK_SEED}}`. The subset contains `{{TRAIN_SIZE}}`
training images and `{{TEST_SIZE}}` test images, with all ten classes present in
both splits. The provenance file records upstream source-file hashes, the subset
seed, class counts, and the compressed subset hash. The default pipeline never
downloads data at runtime.

The baseline is a nearest-centroid classifier over flattened 28 by 28 pixels.
The bounded candidate set is configured in `mnist_task.yaml` and includes
softmax regression, a one-hidden-layer ReLU MLP, a tiny patch-attention
classifier, and one deferred MLP candidate. The patch-attention candidate splits
each MNIST image into 7 by 7 patches, embeds the patches, adds deterministic
positional encodings, applies a single fixed self-attention block, mean-pools the
tokens, and trains a softmax head. This is intentionally a small transformer-like
model, not a claim about full-scale ViT performance.

## Bounded Loop

The run follows `{{LOOP_STAGE_COUNT}}` configured stages:

1. Resolve the human-authored program, project topic, and research questions.
2. Build an `AutoResearchPlan` from the domain profile, experiment plan, and
   pipeline DAG.
3. Validate exact stage-gate names declared in `autoresearch.yaml`.
4. Evaluate the fixed MNIST neural-network candidate set up to the configured
   iteration budget.
5. Generate claims only from configured questions and local artifact paths.
6. Write data, reports, figures, benchmark scores, and review packets under
   `output/`.
7. Run strict AutoResearch readiness validation and write readiness reports.

Candidates are declared in `seed_ideas.yaml` for the proposal ledger and
resolved from `mnist_task.yaml` for execution. Each executable candidate
declares a model type, seed, training schedule, and model-specific parameters.
The loop evaluates at most the configured iteration budget, selects the highest
test accuracy, and breaks ties by lower parameter count and identifier.
Candidates outside the budget are recorded as deferred, not silently ignored.

## Safety Controls

The default autonomy level is `proposal_only`. The run ledger records
`{{LLM_CALLS_USED}}` LLM calls and USD `{{COST_USD_USED}}` cost. The edit
allowlist is restricted to the public project source and manuscript surfaces,
plus the MNIST task configuration file, and the pipeline never executes
generated code. Review gates are emitted with deferred decisions so that
validation can confirm the gates exist without pretending that the machine
approved publication.

Disclosure: AI-assisted AutoResearch status is declared for this exemplar
because it models machine-produced plans, ledgers, reports, and manuscript
variables as review inputs rather than autonomous approval.

## Evidence And Scoring

The experiment writes `output/data/mnist_task_config.json`,
`output/data/ml_task_results.json`, `output/data/ml_candidate_ledger.json`,
`output/data/ml_confusion_matrix.csv`,
`output/reports/ml_experiment_report.md`,
`output/reports/ml_benchmark_score.json`, and
`output/figures/ml_candidate_scores.png`. The benchmark score combines metric
improvement, budget compliance, offline execution, transformer-candidate
coverage, and candidate-selection status. Manuscript variables are hydrated from
these artifacts, and readiness validation checks the evidence registry, artifact
manifest, method ledgers, review gates, benchmark outputs, and AI-assisted
disclosure before rendering is treated as ready for review.
