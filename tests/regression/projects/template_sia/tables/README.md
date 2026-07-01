# `template_sia` — table regression tests

> One file per manuscript table. Re-derives each value via
> the project's deterministic fixture-replay SIA loop
> (`infrastructure.sia.run_sia_loop`, `live=False`) and
> compares to the pinned ground truth in
> [`../../../pinned_values/template_sia.json`](../../../pinned_values/template_sia.json).
