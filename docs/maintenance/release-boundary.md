# Release boundary

This repository currently has two distinct release surfaces that must not be
treated as interchangeable:

- The root package metadata and repository tag are `3.5.1` / `v3.5.1`.
- The GitHub release list also contains a newer-published `v1.0.1` entry from
  the standalone publication lane. That entry is not the root package's next
  semantic version and does not version the root `[Unreleased]` notes.

The root checkout therefore remains **unreleased relative to the current
`CHANGELOG.md` `[Unreleased]` section**. The package version, `v3.5.1` tag, and
the version badge describe the last root release boundary; they do not claim
that the current unreleased changes have changelog parity with a new tag or
GitHub release.

Before the next root release, reconcile these surfaces together:

1. choose the next root version and update `pyproject.toml`;
2. move only the shipped `[Unreleased]` entries under that version heading;
3. create the matching root tag and GitHub release;
4. regenerate package and publication metadata; and
5. update the roadmap, `STATUS.md`, badge, and release records in one gate.

No release, tag, or external publication is created by local verification.
See [`TO-DO.md`](../../TO-DO.md) for the remaining external release action and
[`docs/guides/publication-runbook.md`](../guides/publication-runbook.md) for
provider-specific publishing steps.
