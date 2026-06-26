# Results {#sec:results}

@tbl:sia-metrics summarizes fixture-replay metrics for the bundled run.

{{SIA_METRICS_TABLE}}

: SIA generation metrics (fixture replay). {#tbl:sia-metrics}

Metric delta (final − first generation): {{SIA_METRIC_DELTA}}.

Final injected token: {{SIA_FINAL_METRIC_NAME}}={{SIA_FINAL_METRIC_VALUE}} (n={{SIA_FINAL_N_SAMPLES}}).

![SIA metric progression across generations.](../output/figures/sia_metric_progression.png){#fig:sia-metric-progression width=85%}

## Incremental improvement

The generation-over-generation accuracy delta quantifies the self-refinement
signal at each step of the loop.

![Generation-over-generation metric delta (Δaccuracy) for the SIA loop, illustrating the incremental improvement at each self-refinement step.](../output/figures/sia_improvement_delta.png){#fig:sia-improvement-delta width=80%}
