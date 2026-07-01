# `template_madlib` — configuration-count regression tests

> One file per manuscript claim cluster. Re-derives each count via
> the project's deterministic token-injection pipeline and compares to
> the pinned ground truth in
> [`../../../pinned_values/template_madlib.json`](../../../pinned_values/template_madlib.json).

The manuscript is fully tokenized: its quantitative claims are the
`{{..._COUNT}}` tokens rendered from `manuscript/config.yaml` (seed
431). These tests bind those rendered claims back to their source
functions (`generate_variables`, `load_madlib_config`,
`generate_token_plan`) so a config edit that silently changes a count
fails loudly instead of drifting the manuscript.
