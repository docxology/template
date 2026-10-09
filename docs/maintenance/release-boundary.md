# Release boundary

The root package metadata declares the **4.0.1** candidate. Its changelog
heading remains **Unreleased** until exact-revision acceptance closes.
The prepared 4.0.0 candidate was not published; its notes are retained. Tagging and publication require the verified
acceptance and publication steps below. The earlier recorded root release is `3.8.0` /
`v3.8.0`; its original publication evidence is retained in
[subsystem history](subsystem-status-history.md). Historical standalone release
entries do not version the root package.

Before the next root release, reconcile these surfaces together:

1. Finish the [Platform 4 required acceptance](platform-4-upgrade.md), including
   every source-owned candidate requirement and fresh independent review.
2. Reconcile package metadata, installed versions, locks, exports, source
   identities, artifacts, and the released changelog heading. Re-run acceptance
   against those final exact source bytes.
3. Supply a successful same-repository hosted run at that revision, its exact
   `platform-required-acceptance` artifact ID, and aggregate receipt SHA256.
   The bounded bundle contains only `output/readiness` evidence and the canonical
   `output/readiness/release-candidate/receipt.json` with `source_commit`.
4. Create the matching root tag only after acceptance passes, then manually
   dispatch the release workflow with that handoff. A root 4+ tag push alone is
   blocked. The dedicated [required acceptance workflow](../../.github/workflows/platform-required-acceptance.yml)
   produces the complete bundle only after every original requirement passes;
   partial CI receipts cannot authorize this step.
5. Verify remote commit IDs, retrieved artifact hashes, publication identities,
   licenses, and working URLs, then refresh status and publication records.

No release, tag, or external publication is created by local verification.
See [`TO-DO.md`](../../TO-DO.md) for the remaining external release action and
[`docs/guides/publication-runbook.md`](../guides/publication-runbook.md) for
provider-specific publishing steps.

## Development checkpoint

Work on the 4.0.1 acceptance adapters may be committed on a development branch
while acceptance remains incomplete. Such a checkpoint preserves reviewed source
and focused regression checks; it is not a candidate acceptance receipt or a
release authorization. Unsupported source occurrences and missing native,
runtime, hosted, model or coverage evidence must remain blocked. Complete final
coverage, regenerated publication outputs, exact-SHA hosted acceptance and the
versioned release handoff are still required before publication.
