# Coordinated publication refresh

Finalize the coordinated release metadata and authored release surfaces before
requesting this preparation. The manual
[publication-refresh workflow](../../.github/workflows/publication-refresh.yml)
requires its exact dispatched commit as `source_sha` and the Root version already
declared there as `expected_version`. It prepares an ordinary reviewed patch.
It does not push, activate a bypass credential, tag, publish, measure coverage,
or satisfy required release acceptance.

The Source-owned controller is
`infrastructure.publishing.publication_refresh`; path custody is in
`publication_refresh_custody`, and `release_provider_graph` supplies the same
current metadata graph used by coordinated version planning. The controller
derives the rerender roster from the canonical projects whose
`output/manuscript/config.yaml` is already tracked. It renders and validates
those projects with the existing `rendered_refresh` producer and revalidates the
unchanged output bytes of the canonical complement. The roster is not a fixed
list of fifteen names. Provider dependencies finish before their consumers,
with one to four independent project workers per wave.

Before generation, the workflow prepares the exact locked Root and own project
environments and checks the actual SDK version and source origin. The existing
native preparation action supplies the Source-pinned Lean, document/browser,
Java and format-reader tools and hash-verified dependency cache. Missing tools,
an unknown provider, stale metadata, a dirty checkout or an incorrect requested
SHA refuses the run.

Capture admits only the finite base-tracked canonical output inventory in mode
100644. Flat numbered manuscript sections additionally require explicit
compose-enabled targets in the tracked schema-2 sheaf manifest, tracked compiler
sources and tracked authored fragment inputs. A numbered filename by itself
grants no generated ownership. Authored/config/test/private paths, additions,
deletions, symlinks, mode changes and unexpected untracked files are refused.

The runner commits its generated candidate in the disposable checkout. Both
existing strict all-public publication gates and the unchanged all-project
exemplar-config guard then run on that committed tree.
Only success of all three commands admits the review artifact: an exact full-index
binary patch from the dispatched base, the base/result commits and trees, a
changed-path/blob/SHA-256 manifest, original producer and gate bytes/exits, and
checksums. Failures retain separately named diagnostics without an accepted
review artifact.

Review and integrate the exact retained patch through the ordinary PR path.
Verify the integrated tree against the candidate tree; preserve the original
archives and their digests. Any later metadata, implementation or output edit
requires fresh affected measurements. Final all-project coverage, census,
publication validation and exact-SHA required acceptance remain the separate
[release boundary](release-boundary.md).
