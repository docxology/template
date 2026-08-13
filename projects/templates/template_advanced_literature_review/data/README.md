# Data

This directory contains tracked, human-authored inputs for the advanced
multi-phase literature-review exemplar.

| Path | Purpose |
| --- | --- |
| `subfield_defaults_exoplanet.yaml` | Default subfield taxonomy used when retargeting or validating the bundled exoplanet-atmosphere configuration. |
| `claim_ledger.yaml` | Source-owned claim ledger for project-local numeric/config claims, consumed by the repository's shared `infrastructure/validation` evidence-registry gates. |
| `llm_filter_calibration.json` | Small offline calibration fixture (4 labeled abstracts) for the optional LLM-filter contract in `src/multi_phase/contracts.py` (`validate_llm_calibration`/`score_llm_calibration`); loaded by `tests/test_multi_phase_search.py`. |

Generated corpora, phase metadata, reports, and figures belong under
`../output/`; do not write runtime artifacts into this directory.
