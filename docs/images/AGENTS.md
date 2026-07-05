# docs/images/ - Documentation Image Assets

## Purpose

This directory stores public image assets referenced by repository
documentation. Keep it limited to small, reviewable screenshots or diagrams
that support Markdown pages in `docs/`, `README.md`, or other tracked public
documentation.

## Rules

- Prefer project-generated figures under the relevant project `output/figures/`
  for manuscript content; use this directory only for repository documentation
  assets.
- Add or update `README.md` when adding assets so reviewers know what each image
  is for.
- Every asset here must be referenced from at least one Markdown page under
  `docs/` (or the root `README.md`); an unreferenced image is orphaned and
  should be removed, not accumulated.
- Do not store private project screenshots, credentials, local paths, browser
  profiles, or unredacted customer/user data here.
- Use lowercase, hyphenated filenames and PNG for screenshots.

## Current Assets

None currently. The directory previously held four screenshots of an
unrelated external tool ("Coasys Ops"/"Weave") that were never referenced by
any doc in this repo; they were removed as orphaned scaffolding.

## See Also

- [`../usage/image-management.md`](../usage/image-management.md)
- [`../AGENTS.md`](../AGENTS.md)
