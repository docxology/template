# Public output policy

Canonical outputs for public exemplars are reproducible publication evidence,
not disposable local cache. They may be tracked only when the repository's
generated-artifact allowlist admits their exact location and the producing
source/configuration is also tracked.

The boundary is:

- `projects/templates/*/output/` and corresponding public `output/templates/*/`
  artifacts may be tracked when they are canonical publication evidence.
- Outputs for private lifecycle projects, local forks, experiments, coverage,
  editor indexes, and transient render state remain ignored and prohibited.
- Generated files are never edited by hand to satisfy a gate. Fix the producer,
  regenerate, and verify deterministic drift instead.
- Text publication artifacts must not retain `/Users/<name>/` or
  `/home/<name>/` prefixes. Manifest snapshots and the copy stage normalize
  those prefixes to `<home>` before hashing or publication; the generated-state
  audit rejects any machine-local path that escapes that boundary.
- `scripts/audit/check_tracked_generated_artifacts.py` enforces generated-state
  policy; `scripts/audit/check_tracked_all.py` enforces confidentiality across
  projects, fonds, rules, and tools.

When policy and an old prose statement disagree, the executable guards and
their tests are authoritative. Update the prose and add a drift regression.
