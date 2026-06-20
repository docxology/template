# data

`claim_ledger.yaml` records project-local claims that should stay tied to config, source, or generated artifacts.

Keep claims narrow. Do not add external publication, DOI, release, or empirical validation claims unless corresponding evidence exists and the publication metadata has been updated.

For method-protocol changes, record only source-owned or generated-artifact claims unless the fork has added domain evidence. A domain fork must add validators and claim-ledger evidence before using Madlib output as empirical, theoretical, benchmark, or reader-quality support.

If documentation promises review-packet completeness, include claim rows for the copied output surface and generated output statistics. Do not let a PDF-only handoff satisfy a method-audit claim.

If figure counts, artifact names, protocol steps, or publication metadata change, update the ledger in the same commit as the source/config/docs change. Metadata files (`CITATION.cff`, `.zenodo.json`, `codemeta.json`) remain conservative unless a real standalone release or deposited record exists.
