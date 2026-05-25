# Methodology

The loop is implemented in `src/loop.py`, with reusable ML-task behavior in
`src/ml_task.py`, artifact writing in `src/writers.py`, figures in
`src/figures.py`, and manuscript-variable hydration in
`src/manuscript_variables.py`. The project scripts remain thin dispatchers.

## Task

The task is a deterministic nonlinear binary classification problem. The data
generator uses seed `{{ML_TASK_SEED}}`, draws two continuous features, and labels
each point by a noisy interaction of the two features. A majority-class baseline
sets the reference accuracy. Candidate models are ridge classifiers with either
linear features or a small quadratic feature map. This gives the loop a real
metric surface while keeping the experiment small enough for every default CI
run.

## Bounded Loop

The run follows `{{LOOP_STAGE_COUNT}}` configured stages:

1. Resolve the human-authored program, project topic, and research questions.
2. Build an `AutoResearchPlan` from the domain profile, experiment plan, and
   pipeline DAG.
3. Validate exact stage-gate names declared in `autoresearch.yaml`.
4. Evaluate the fixed candidate set up to the configured iteration budget.
5. Generate claims only from configured questions and local artifact paths.
6. Write data, reports, figures, benchmark scores, and review packets under
   `output/`.
7. Run strict AutoResearch readiness validation and write readiness reports.

Candidates are loaded from `seed_ideas.yaml`. Each candidate declares a feature
map, ridge penalty, complexity score, expected artifacts, and touched paths. The
loop evaluates at most the configured iteration budget, selects the highest
held-out accuracy, and breaks ties by lower complexity, lower penalty, then
identifier. Candidates outside the budget are recorded as deferred, not silently
ignored.

## Safety Controls

The default autonomy level is `proposal_only`. The run ledger records
`{{LLM_CALLS_USED}}` LLM calls and USD `{{COST_USD_USED}}` cost. The edit
allowlist is restricted to the public project source and manuscript surfaces,
and the pipeline never executes generated code. Review gates are emitted with
deferred decisions so that validation can confirm the gates exist without
pretending that the machine approved publication.

Disclosure: AI-assisted AutoResearch status is declared for this exemplar
because it models machine-produced plans, ledgers, reports, and manuscript
variables as review inputs rather than autonomous approval.

## Evidence And Scoring

The experiment writes `output/data/ml_task_results.json`,
`output/data/ml_candidate_ledger.json`, `output/reports/ml_experiment_report.md`,
`output/reports/ml_benchmark_score.json`, and
`output/figures/ml_candidate_scores.png`. The benchmark score combines metric
improvement, budget compliance, offline execution, and candidate-selection
status. Manuscript variables are hydrated from these artifacts, and readiness
validation checks the evidence registry, artifact manifest, method ledgers,
review gates, benchmark outputs, and AI-assisted disclosure before rendering is
treated as ready for review.
