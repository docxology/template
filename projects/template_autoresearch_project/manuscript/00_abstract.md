# Abstract

This paper presents `{{AUTORESEARCH_TOPIC}}`, a public template exemplar that
turns an AutoResearch loop into ordinary reproducible research infrastructure.
The case study is intentionally small but concrete: `{{TRAIN_SIZE}}` training
and `{{TEST_SIZE}}` test images from a local balanced MNIST subset are evaluated
by a bounded numpy neural-network candidate loop. The run evaluates
`{{EVALUATED_CANDIDATE_COUNT}}` of `{{CANDIDATE_COUNT}}` proposed candidates,
including a tiny patch-attention classifier, selects
`{{ACCEPTED_CANDIDATE_ID}}` (`{{ACCEPTED_MODEL_TYPE}}`,
`{{ACCEPTED_PARAMETER_COUNT}}` parameters), and improves test accuracy from
`{{BASELINE_ACCURACY}}` to `{{BEST_ACCURACY}}`
(`{{ACCURACY_DELTA}}` absolute change). The same pipeline writes proposal,
candidate, run, review, benchmark, evidence, figure, confusion-matrix, and
manuscript-variable artifacts; uses `{{LLM_CALLS_USED}}` LLM calls at USD
`{{COST_USD_USED}}` cost; and records `{{LOOP_STAGE_COUNT}}` configured stages,
`{{SUPPORTED_CLAIM_COUNT}}` supported local-artifact claims, and
`{{REQUIRED_ARTIFACT_COUNT}}` required artifacts. The final readiness status is
`{{READINESS_STATUS}}`, with review gates deferred to a human rather than
self-approved by the generated run.
