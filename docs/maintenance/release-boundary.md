# Release boundary

The root package metadata declares intended platform **4.0.0**, and its
changelog heading remains **Unreleased**. No new tag, GitHub release, or deposit
follows from that declaration. The earlier recorded root release is `3.8.0` /
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
   blocked. The complete acceptance producer/upload lane remains to be built;
   partial CI receipts cannot authorize this step.
5. Verify remote commit IDs, retrieved artifact hashes, publication identities,
   licenses, and working URLs, then refresh status and publication records.

No release, tag, or external publication is created by local verification.
See [`TO-DO.md`](../../TO-DO.md) for the remaining external release action and
[`docs/guides/publication-runbook.md`](../guides/publication-runbook.md) for
provider-specific publishing steps.
