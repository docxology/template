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
regenerates every canonical public project with the existing `rendered_refresh`
producer. A tracked `output/manuscript/config.yaml` identifies a materialized
publication copy, not whether that project's rendered products depend on the
current renderer. Projects without that copy must also acquire current global
HTML semantics, mathematics and applicable EPUB styling through real generation.
One reviewed semantic consumer, `templates/template_pitch_deck`, additionally
reads COUNTS and version facts during canonical Stage 02; default refresh runs
that genuine stage before its non-rebind refresh. There is no implicit
unchanged-output complement. Provider dependencies finish before their consumers,
with exactly one project worker per wave. The shared execution account uses
strict same-UID process observation: concurrent project producers can appear in
each other's final census, so both `run` and `generate` refuse `--jobs` values
other than `1` before any phase or producer. The CLI and workflow default to
that single worker. A project owns one sequential command chain, so Pitch
analysis and refresh never race. A nonzero or
unaccepted analysis result is terminal; it cannot fall through to refresh.

Before generation, the workflow prepares the exact locked Root and own project
environments and checks the actual SDK version and source origin. The existing
native preparation action supplies the Source-pinned Lean, document/browser,
Java and format-reader tools and hash-verified dependency cache. Missing tools,
an unknown provider, stale metadata, a dirty checkout or an incorrect requested
SHA refuses the run.


The hosted controller runs plan, locked preparation, generation, candidate,
strict verification and capture in one `run` payload under the existing fresh
unprivileged Linux execution account. Its original Git preflight precedes the phase
chain and is not repeated after the disposable candidate commit. The strict
same-owner process census, guardian, deadlines and exit predicates are unchanged.
Evidence is created in the account's existing caller-readable artifact directory
outside Source; only the final successful payload admits a review upload.
Original diagnostics remain available after a failed phase. Inputs are explicit
CLI arguments; the account's runtime environment allowlist is unchanged.

The v4 plan binds the one fixed dependent consumer, its actual canonical subject,
COUNTS/version input bytes and reviewed Stage 02/reader/compiler paths to the exact
Source commit. The actual canonical Stage 02 selection is also bound and must
include chart generation before deck rendering. Private or unknown subjects,
missing producers and changed inputs
refuse before generation. This declaration grants no additional output paths.

Capture freezes the base-tracked canonical output inventory in mode 100644 and
the immutable blob identities of its tracked canonical artifact manifests.
Reconstructing that ownership does not reopen retired output paths. The clean
initial plan still requires every base-owned file to be a real non-executable
regular file. Flat numbered manuscript sections additionally require explicit
compose-enabled targets in the tracked schema-2 sheaf manifest, tracked compiler
sources and tracked authored fragment inputs; numbering alone grants nothing.

Default refresh also captures genuine stable-output inventory transitions. A new
path must occur in the freshly validated canonical artifact manifest of its own
fixed public project. That manifest must match the complete current Git-shippable
inventory, including file bytes and hashes. A retired path must have been both
tracked and declared by the frozen base manifest, and must be absent from the
current manifest and filesystem. A newly invented manifest cannot grant ownership.
This permits renderer-owned filename changes without retaining obsolete aliases
or dropping current pages from the candidate. Authored/config/test/private paths,
undeclared additions or removals, symlinks, executable modes and all other
unexpected untracked files remain refused. `rebind-only` grants no such
additions or removals.

The runner commits its generated candidate in the disposable checkout. Both
existing strict all-public publication gates and the unchanged all-project
exemplar-config guard then run on that committed tree.
Only success of all three commands and every actual canonical generation command
(including dependent Pitch analysis) admits the review artifact: an exact
full-index binary patch from the dispatched base, the base/result commits and
trees, a changed-path/blob/SHA-256 manifest, original producer and gate bytes/exits,
and checksums. The v4 change records identify `A`, `M` and `D` explicitly;
`before_blob` is null for additions, while `after_blob`, `sha256` and `bytes` are
null for deletions. The binary patch disables rename collapsing so both sides
remain explicit. `COMPLETE.json` records `all_committed_tree_gates_passed`; it is
not release acceptance. Failures retain separately named diagnostics without an
accepted review artifact.

Review and integrate the exact retained patch through the ordinary PR path.
Verify the integrated tree against the candidate tree; preserve the original
archives and their digests. Any later metadata, implementation or output edit
requires fresh affected measurements. Final all-project coverage, census,
publication validation and exact-SHA required acceptance remain the separate
[release boundary](release-boundary.md).

## Coverage import and unchanged-output rebind

The default mode is `refresh`: regenerate all canonical public projects and run
the genuine dependent Pitch analysis before its refresh. A coverage import
changes semantic Pitch inputs as well as the shared stage fingerprint.
Regenerate those outputs before using `rebind-only`; unchanged bytes alone do not
prove current displayed measurements or renderer behavior. The requested mode is
frozen in the Source-derived plan, preparation and generation records, checked
against the dispatch on every phase, and retained in the review manifest.

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
4. Produce publication candidate Q through the actual complete Source-owned
   regeneration chain. Default refresh regenerates every canonical public project
   and includes Pitch's genuine Stage 02 before its rendering.
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
