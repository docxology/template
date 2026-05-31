```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Introduction}
\section*{Introduction}
```

# Motivation and scope {#sec:intro_motivation}

<!-- sheaf-track:prose -->

## Scientific scope

This manuscript couples three tracks on toy Active Inference models: a Bernoulli–Ising analytical oracle, a pymdp T-maze rollout, and a sheaf-indexed assembly contract that binds 13 optional fragment tracks under an IMRAD outline. The scientific claims stay within those models and their generated artifacts; they are not empirical statements about biological agents.

## Manuscript structure

Three **scientific tracks** (analytical, pymdp, sheaf composition) map onto 13 **composable fragment types** and 10 pipeline gates ([@fig:multi_track_architecture]). [@sec:sheaf_coverage] summarizes which fragment tracks bind to each manifest row. [@sec:methods_sheaf] documents the compose pipeline, coverage semantics ([@eq:coverage_cell]), and strict validation gates.

The pymdp track follows the [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference) with a minimal T-maze and planning horizon `policy_len = 2`. Other sections cite [@sec:methods_pymdp] instead of repeating that reference.
