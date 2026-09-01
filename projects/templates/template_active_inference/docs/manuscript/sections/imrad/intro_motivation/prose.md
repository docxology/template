## Scientific scope

This manuscript couples three tracks on toy Active Inference models: a Bernoulli–Ising analytical oracle, a pymdp T-maze rollout, and a sheaf-indexed assembly contract that binds {{sheaf_track_count}} optional fragment tracks under an IMRAD outline. The conceptual lineage is the free-energy and active-inference literature [@friston2010fep; @buckley2017mathreview; @parr2022active], with critical scope pressure from accounts that separate FEP's broad organizing role from direct empirical brain claims [@gershman2019fepbrain]. Here that distinction is operational: the scientific claims stay within these models and their generated artifacts, not biological agents.

## Manuscript structure

Three **scientific tracks** (analytical, pymdp, sheaf composition) map onto {{sheaf_track_count}} **composable fragment types** and {{pipeline_track_count}} pipeline gates ([@fig:multi_track_architecture]). [@sec:sheaf_coverage] summarizes which fragment tracks bind to each manifest row. [@sec:methods_sheaf] documents the compose pipeline, coverage semantics ([@eq:coverage_cell]), and strict validation gates.

The pymdp track follows the [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference) [@pymdp2024] with a minimal T-maze and planning horizon `policy_len = {{si_tmaze_policy_len}}`. Other sections cite [@sec:methods_pymdp] instead of repeating that reference.
