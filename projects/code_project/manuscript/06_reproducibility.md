# Reproducibility Certification

This section provides a machine-verifiable reproducibility certificate for the complete study. Every metric below is computed by the analysis pipeline and injected into the manuscript at render time — establishing a cryptographic chain of custody from configuration to publication.

## Configuration Provenance

| Property                          | Value                 |
| --------------------------------- | --------------------- |
| Config hash (SHA-256, truncated)  | `{{CONFIG_HASH}}`     |
| Paper version                     | {{CONFIG_VERSION}}    |
| First author                      | {{CONFIG_FIRST_AUTHOR}} |
| Keyword count                     | {{CONFIG_KEYWORDS}}   |

The configuration hash changes whenever any parameter in `config.yaml` is modified, ensuring that every rendered PDF is traceable to a specific configuration state.

## Generated Artifact Registry

The analysis pipeline produced the following artifacts, each validated by `infrastructure.validation.output.validator`:

| Category                           | Count                  |
| ---------------------------------- | ---------------------- |
| Publication-quality figures        | {{ARTIFACT_FIGURES}}   |
| Structured data files (CSV/JSON)   | {{ARTIFACT_DATA_FILES}} |
| Analysis reports                   | {{ARTIFACT_REPORTS}}   |
| **Total artifacts**                | **{{ARTIFACT_TOTAL}}** |

## Numerical Validation Summary

### Convergence Verification

Within the configured grid, **{{RESULT_NUM_CONVERGED}}** of **{{CONFIG_NUM_STEP_SIZES}}** runs satisfied `gradient_descent()` convergence (`{{RESULT_ALL_CONVERGED}}` indicates whether every row in `optimization_results.csv` converged).

- Converged step sizes: {{RESULT_CONVERGED_STEP_SIZES}}
- Non-convergent or hit-iteration-cap step sizes: {{RESULT_DIVERGED_STEP_SIZES}}
- Smallest recorded iteration count: {{RESULT_MIN_ITERATIONS}} (at $\alpha = {{RESULT_BEST_STEP_SIZE}}$)
- Largest recorded iteration count: {{RESULT_MAX_ITERATIONS}} (at $\alpha = {{RESULT_WORST_STEP_SIZE}}$)
- Mean iterations across all rows: {{RESULT_AVG_ITERATIONS}}

### Numerical Stability

Stability score from `infrastructure.scientific.stability`: **{{STABILITY_SCORE}}** (out of 1.00)

The stability analysis tested {{CONFIG_STABILITY_CELLS}} parameter combinations ({{CONFIG_NUM_STABILITY_STARTS}} starting points $\times$ {{CONFIG_NUM_STABILITY_STEPS}} step sizes), confirming uniform convergence across the entire parameter space.

## Madlib Injection Verification

This manuscript demonstrates the template's "madlib" capability: every quantitative claim is injected from computed data at render time. The substitution system processed the following variables:

- **Configuration variables**: Drawn from `manuscript/config.yaml` (`experiment:` section)
- **Result variables**: Computed from `output/data/optimization_results.csv`
- **Stability variables**: Extracted from `output/reports/stability_analysis.json`
- **Provenance variables**: Generated at substitution time (timestamps, hashes, versions)

To verify: modifying any value in `config.yaml` and re-running the pipeline will automatically update every corresponding claim in this document. No manual transcription is required or permitted.
