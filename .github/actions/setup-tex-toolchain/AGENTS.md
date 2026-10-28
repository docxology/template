# `setup-tex-toolchain` — agent notes

Cached `xelatex`/`bibtex` provisioning for the slow and rehearsal lanes. See
[README.md](README.md) for the steps, cache key, and callers.

## Contract

- Two steps only: `actions/cache` (pinned) then a cache-miss-guarded
  `apt-get install`. The install must stay conditional on
  `steps.texlive-cache.outputs.cache-hit != 'true'`.
- The cache key and paths are shared by both callers; changing them changes both
  lanes' compiled inputs at once, so treat a bump as a CI behavior change.
- The package set is exactly `texlive-xetex texlive-latex-extra
  texlive-bibtex-extra texlive-fonts-recommended lmodern`. Lane-specific probes
  and extra packages stay in the calling job.
- `ci.yml`'s TeX steps are intentionally separate: different package sets and
  different probes, so folding them in here would erase which lane prepares what.

## Editing

- Run `actionlint` after edits, keep [README.md](README.md) accurate, and check
  both callers still gate their own tests on the prepared binaries.
