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
those projects with the existing `rendered_refresh` producer. One reviewed
semantic consumer, `templates/template_pitch_deck`, additionally reads COUNTS and
version facts during canonical Stage 02; default refresh runs that genuine stage
before its existing non-rebind refresh. The remaining canonical projects revalidate
their unchanged output bytes. Current Source therefore has fifteen tracked
publication-copy projects, Pitch analysis/refresh, and nine unchanged rebinds. The roster is not a fixed
list of fifteen names. Provider dependencies finish before their consumers,
with one to four independent project workers per wave. A project owns one
sequential command chain, so Pitch analysis and refresh never race. A nonzero or
unaccepted analysis result is terminal; it cannot fall through to refresh.

Before generation, the workflow prepares the exact locked Root and own project
environments and checks the actual SDK version and source origin. The existing
native preparation action supplies the Source-pinned Lean, document/browser,
Java and format-reader tools and hash-verified dependency cache. Missing tools,
an unknown provider, stale metadata, a dirty checkout or an incorrect requested
SHA refuses the run.

The v3 plan binds the one fixed dependent consumer, its actual canonical subject,
COUNTS/version input bytes and reviewed Stage 02/reader/compiler paths to the exact
Source commit. The actual canonical Stage 02 selection is also bound and must
include chart generation before deck rendering. Private or unknown subjects,
missing producers and changed inputs
refuse before generation. This declaration grants no additional output paths.

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

## Coverage import and unchanged-output rebind

The default mode remains `refresh`: regenerate tracked publication copies, run
the genuine dependent Pitch analysis/refresh, and revalidate the unchanged
complement. A coverage import changes semantic Pitch inputs as well as the shared
stage fingerprint. Regenerate those dependent outputs before using `rebind-only`;
unchanged output bytes alone cannot prove that displayed measurements are current. The requested mode is frozen in the Source-derived plan,
preparation and generation records, checked against the dispatch on every phase,
and retained in the review manifest.

In `rebind-only`, all canonical projects use the actual existing
`rebind_project` path through `refresh_rendered_provenance.py --rebind`.
There is no analysis/render fallback. A changed recorded output fingerprint
refuses the run. Capture admits only base-tracked flat
`projects/templates/<canonical>/output/reports/*.json` regular non-executable
files; the compiled manuscript allowance is empty. The all-project config guard
and both strict publication audits remain mandatory.

Use this sequence after final metadata and genuine publication generation settle:

1. Freeze the authored Source and compiled manuscripts at commit C, then measure
   all canonical own release-profile coverage inputs at C.
2. While HEAD remains C, import those exact measured values into the owning
   coverage-literal store and regenerate its provenance. Verify every measured
   project input hash still matches C; retain the original measurements.
3. Commit the imported literals and provenance as D. Preserve the original C
   measurements and compare every project/support identity with C.
4. Produce dependent publication candidate Q through the actual Source-owned
   analysis/refresh chain. The default hosted refresh includes Pitch's genuine
   Stage 02 before refresh, the fifteen publication copies, and nine rebinds.
   Check its complete footprint and strict committed-tree gates. If any project
   source, compiled manuscript or measured support input changes, remeasure that
   affected input after it settles; never keep a mismatched C identity.
5. With dependent outputs current and unchanged, dispatch `mode=rebind-only` at
   the exact Source Q, `source_sha=Q`, and the actual final `expected_version`.
   This all-project strict receipt rebind produces E without analysis or render
   fallback. Integrate its exact reviewed patch through the ordinary PR path.
6. Verify the integrated tree and current CI Gate, then perform required acceptance
   on the exact final main revision. C measurements retain `source_commit=C`
   only while their original measured project/support hashes still match.

If the unchanged-output rebind refuses, preserve its original failure. Perform
an explicit real refresh and remeasure any affected inputs after their Source
settles, then repeat the import/rebind sequence. Never restamp a changed output
or relabel an old measurement.
