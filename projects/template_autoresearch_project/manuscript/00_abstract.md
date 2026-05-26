# Abstract {#sec:abstract}

This paper presents `{{AUTORESEARCH_TOPIC}}`, a public template exemplar that
turns an AutoResearch loop into ordinary reproducible research infrastructure.
The case study is intentionally small but concrete: `{{TRAIN_SIZE}}` training
and `{{TEST_SIZE}}` test images from `{{DATASET_NAME}}` are evaluated by the
bounded `{{ML_TASK_NAME}}` loop. The run evaluates
`{{EVALUATED_CANDIDATE_COUNT}}` of `{{CANDIDATE_COUNT}}` proposed candidates,
including `{{TRANSFORMER_CANDIDATE_TITLE}}`, selects
`{{ACCEPTED_CANDIDATE_ID}}` (`{{ACCEPTED_MODEL_TYPE_LABEL}}`,
`{{ACCEPTED_PARAMETER_COUNT}}` parameters), and improves `{{METRIC_NAME}}` from
`{{BASELINE_ACCURACY}}` to `{{BEST_ACCURACY}}`
(`{{ACCURACY_DELTA}}` absolute change). The validated diagnostic layer reports
macro F1 `{{ACCEPTED_MACRO_F1}}`, bootstrap accuracy interval
`{{BOOTSTRAP_ACCURACY_INTERVAL}}`, Brier score `{{ACCEPTED_BRIER_SCORE}}`,
negative log likelihood `{{ACCEPTED_NEGATIVE_LOG_LIKELIHOOD}}`, top-2 accuracy
`{{ACCEPTED_TOP2_ACCURACY}}`, and exact McNemar p-value `{{MCNEMAR_P_VALUE}}`.
The same pipeline writes proposal, candidate, run, review, benchmark, evidence,
figure, confusion-matrix, statistical-summary, probability-quality, and
manuscript-variable artifacts from declared output contracts; uses
`{{LLM_CALLS_USED}}` LLM calls at USD `{{COST_USD_USED}}` cost; and records
`{{LOOP_STAGE_COUNT}}` configured stages, `{{SUPPORTED_CLAIM_COUNT}}` supported
local-artifact claims, and `{{REQUIRED_ARTIFACT_COUNT}}` required artifacts.
The final readiness status is `{{READINESS_STATUS}}`, with review gates
deferred to a human rather than self-approved by the generated run.
