---
language: en
license: apache-2.0
task_categories:
  - text-generation
  - structured-prediction
tags:
  - active-inference
  - program-analysis
  - GNN
  - POMDP
  - code-understanding
  - roundtrip-evaluation
  - codebase-to-gnn
pretty_name: COGANT Roundtrip Evaluation Dataset
size_categories:
  - n<1K
---

# COGANT Roundtrip Evaluation Dataset

A benchmark of **23 Python repositories** evaluated for roundtrip fidelity
under the COGANT (Codebase-to-GNN Analysis Tool) pipeline. Each repository
was processed forward (code → program graph → GNN in Active Inference notation)
and then reversed (GNN → synthesized Python package → re-forwarded GNN). The
**ε (epsilon) role-match score** measures structural fidelity between the
original and reconstructed GNN.

## Description

COGANT translates arbitrary Python codebases into Generative Neural Network
(GNN) representations using Active Inference semantics. The forward pipeline
assigns every program-graph node a role from the set
`{HIDDEN_STATE, OBSERVATION, ACTION, POLICY, CONSTRAINT, CONTEXT}` and
compiles state-space matrices `(A, B, C, D, π)`. The reverse pipeline parses
a GNN markdown file and synthesizes a new Python package; re-running the
forward pipeline on that package yields a second GNN. The ε score is the
multiset similarity between the role populations of the two GNNs.

This dataset records the ε scores, GNN shape parameters, and classification
tiers for all 23 evaluation targets, spanning:

- **Zoo fixtures** (11 targets): hand-authored Active Inference primitives
  designed to exercise individual POMDP components.
- **Curated real-world examples** (3 targets): small, well-understood Python
  packages hand-validated by the COGANT team.
- **Real-world libraries** (9 targets): third-party open-source Python
  libraries of varying complexity, pulled from PyPI.

## Motivation

Roundtrip fidelity is the central empirical claim of the COGANT v1.0 paper:
that the forward GNN translation is faithful enough that an independently
synthesized codebase re-forwards to the same structural GNN. This dataset
makes that claim reproducible and extensible. Researchers can:

1. Verify the published ε scores by running `regenerate.py`.
2. Add new repositories to the evaluation corpus.
3. Use the pre-computed `roundtrip_results.jsonl` as a benchmark baseline for
   alternative GNN translation or synthesis approaches.

## Structure

```
_rnd/dataset/
├── DATASET_CARD.md          # This file (HuggingFace README format)
├── LICENSE                  # Apache 2.0
├── citation.bib             # BibTeX entry for the COGANT manuscript
├── regenerate.py            # Script to reproduce all ε scores from source
├── roundtrip_results.jsonl  # Pre-computed results (one JSON per line)
├── README.md                # Original ML dataset card (node-classification task)
├── dataset_summary.json     # Aggregate statistics
├── instances.jsonl          # Per-repo graph and GNN shape records
├── nodes.jsonl              # Per-node feature and role records
└── instances/               # Full per-repo JSON bundles
    ├── calculator.json
    ├── event_pipeline.json
    ├── flask_app.json
    ├── flask_mini.json
    ├── json_stdlib.json
    └── requests_lib.json
```

The roundtrip evaluation data lives in `roundtrip_results.jsonl`. Each line
is a JSON object with the following fields:

| Field | Type | Description |
|---|---|---|
| `rank` | int | Row number in the ROUNDTRIP_EVAL.md summary table (1–23). |
| `group` | str | Target group: `zoo`, `rwex` (curated real-world), or `rw` (real-world library). |
| `repo` | str | Short repository or fixture name. |
| `epsilon` | float | Role-match score ε ∈ [0, 1]. |
| `tier` | str | `ISOMORPHIC` (ε ≥ 0.8), `APPROXIMATE` (0.5 ≤ ε < 0.8), or `DIVERGENT` (ε < 0.5). |
| `orig_n_hidden` | int | HIDDEN_STATE count in the original GNN (n_states). |
| `orig_n_obs` | int | OBSERVATION count in the original GNN (n_obs). |
| `orig_n_actions` | int | ACTION count in the original GNN (n_actions). |
| `synth_n_hidden` | int | HIDDEN_STATE count in the re-forwarded synthesized GNN. |
| `synth_n_obs` | int | OBSERVATION count in the re-forwarded synthesized GNN. |
| `synth_n_actions` | int | ACTION count in the re-forwarded synthesized GNN. |
| `elapsed_s` | float | Wall-clock seconds for the full roundtrip (forward + reverse + forward). |

## Summary Table (23 Targets)

| Rank | Group | Repo / Fixture | ε | Tier |
|---:|---|---|---:|---|
|  1 | zoo  | 01_simple_state  | 1.0000 | ISOMORPHIC  |
|  2 | zoo  | 02_observer      | 1.0000 | ISOMORPHIC  |
|  3 | zoo  | 03_actor         | 1.0000 | ISOMORPHIC  |
|  4 | zoo  | 04_pomdp_minimal | 1.0000 | ISOMORPHIC  |
|  5 | zoo  | 05_multi_factor  | 1.0000 | ISOMORPHIC  |
|  6 | zoo  | 06_hierarchical  | 1.0000 | ISOMORPHIC  |
|  7 | zoo  | 08_preferences   | 1.0000 | ISOMORPHIC  |
|  8 | zoo  | 11_sensor_fusion | 1.0000 | ISOMORPHIC  |
|  9 | rwex | json_stdlib      | 1.0000 | ISOMORPHIC  |
| 10 | rwex | requests_lib     | 1.0000 | ISOMORPHIC  |
| 11 | zoo  | 12_full_pomdp    | 0.9474 | ISOMORPHIC  |
| 12 | rw   | dateutil         | 0.8638 | ISOMORPHIC  |
| 13 | rw   | pyyaml           | 0.8520 | ISOMORPHIC  |
| 14 | rwex | flask_app        | 0.8429 | ISOMORPHIC  |
| 15 | zoo  | 07_event_driven  | 0.7778 | APPROXIMATE |
| 16 | zoo  | 10_constraint    | 0.7143 | APPROXIMATE |
| 17 | zoo  | 09_policy        | 0.6667 | APPROXIMATE |
| 18 | rw   | tqdm             | 0.5749 | APPROXIMATE |
| 19 | rw   | fastapi          | 0.5402 | APPROXIMATE |
| 20 | rw   | click            | 0.5134 | APPROXIMATE |
| 21 | rw   | httpx            | 0.4777 | DIVERGENT   |
| 22 | rw   | urllib3          | 0.4252 | DIVERGENT   |
| 23 | rw   | requests         | 0.4147 | DIVERGENT   |

**Distribution:** ISOMORPHIC 14/23 (61%) · APPROXIMATE 6/23 (26%) · DIVERGENT 3/23 (13%)

### Key finding

The three DIVERGENT repositories (requests, urllib3, httpx) share a single
failure mode: constraint-heavy role distributions (304–744 CONSTRAINT nodes)
collapse to the synthesizer's fixed scaffolding of 3–4 CONSTRAINT nodes,
driving ε below 0.5. All zoo fixtures and curated real-world examples land in
ISOMORPHIC or APPROXIMATE. The core POMDP skeleton (HIDDEN_STATE, OBSERVATION,
ACTION) is preserved across all 23 targets; fidelity loss is confined to
POLICY, CONTEXT, and high-cardinality CONSTRAINT populations.

## Intended Use

- **Benchmark baseline**: compare alternative GNN translation or synthesis
  methods against the COGANT v0.5.0 baseline ε scores.
- **Ablation studies**: remove or replace individual pipeline stages
  (parser, planner, synthesizer) and measure ε impact.
- **Synthesizer improvement**: the DIVERGENT bucket defines a clear target —
  closing the CONSTRAINT-count gap — for future synthesizer work.
- **Active Inference tooling**: the pre-computed GNN shape parameters
  (n_hidden, n_obs, n_actions) enable downstream researchers to select
  tractable targets for Active Inference simulation without re-running COGANT.

## Limitations

- **Python only**: COGANT supports JavaScript ingestion experimentally, but
  only Python repositories are included in this evaluation.
- **Rule-derived roles**: semantic role assignments come from COGANT's
  translation rules, not from human annotators. Agreement with expert
  annotators has not been measured on this corpus.
- **ε is a multiset-similarity metric**: it is sensitive to role-population
  imbalance. A repository dominated by CONSTRAINT nodes will score poorly even
  if all other roles round-trip faithfully. A coverage-based metric (does every
  origin role appear at least once?) would yield higher scores for the DIVERGENT
  bucket.
- **Synthesizer version lock**: scores were computed with `cogant==0.5.0`. The
  reverse synthesizer is under active development; future versions are expected
  to close the CONSTRAINT gap.
- **Wall-clock elapsed times** were measured on a single machine and are
  provided for relative comparison only.

## Reproducibility

```bash
cd projects_in_progress/cogant
python _rnd/dataset/regenerate.py
# outputs: _rnd/dataset/roundtrip_results.jsonl
```

The `regenerate.py` script uses `cogant.reverse.idempotency.verify_repo_roundtrip()`
on the zoo fixtures in `examples/zoo/` and the curated examples in
`examples/real_world/`, and `cogant roundtrip` (subprocess) for the third-party
library fixtures in `_rnd/eval_repos/`.

## Citation

```bibtex
@software{cogant2026,
  title   = {COGANT: Codebase-to-GNN Analysis Tool},
  author  = {Friedman, Daniel Ari},
  year    = {2026},
  url     = {https://github.com/docxology/template},
  version = {0.5.0}
}
```

## License

Apache 2.0. See `LICENSE` for the full text. Third-party library fixtures in
`_rnd/eval_repos/` carry their own upstream licenses; consult each library's
`LICENSE` file for terms.
