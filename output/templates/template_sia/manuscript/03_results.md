# Results {#sec:results}

@tbl:sia-metrics summarizes fixture-replay metrics for the bundled run.

| Gen | Metric | Value | N |
| --- | --- | ---: | ---: |
| 1 | accuracy | 0.5000 | 6 |
| 2 | accuracy | 0.6667 | 6 |
| 3 | accuracy | 0.8333 | 6 |

: SIA generation metrics (fixture replay). {#tbl:sia-metrics}

Metric delta (final − first generation): 0.3333.

Final injected token: accuracy=0.8333 (n=6).

![SIA metric progression across generations.](../output/figures/sia_metric_progression.png){#fig:sia-metric-progression width=85%}

## Incremental improvement

The generation-over-generation accuracy delta quantifies the self-refinement
signal at each step of the loop.

![Generation-over-generation metric delta (Δaccuracy) for the SIA loop, illustrating the incremental improvement at each self-refinement step.](../output/figures/sia_improvement_delta.png){#fig:sia-improvement-delta width=80%}
