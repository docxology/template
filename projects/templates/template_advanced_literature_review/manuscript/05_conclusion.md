# Conclusion

This exemplar turns a phase-aware literature-review design into an auditable,
reproducible pipeline. It separates retrieval, de-duplication, full-text assessment,
extraction, bibliometrics, knowledge-graph construction, visualization,
reproducibility assessment, and export into independently checkable stages.

The central result is architectural: configuration and recorded artifacts determine the
manuscript, while the claim ledger records what is configured, synthetic, or
source-backed. A deterministic fixture run can prove that the pipeline and validators
work; it cannot establish conclusions about {{SEARCH_TERM_TITLE}}. Live conclusions
require refreshed retrieval evidence, provenance, domain review, and a clean release
audit.

## Reproducibility

The rendered manuscript is generated from `output/data/*.json`, figures, manifests,
registries, and validation reports. A second clean run should match under the
repository’s canonical normalized-diff rules. Any unexplained difference is a release
finding. No generated output should be edited by hand.
