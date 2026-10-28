# `run-safety-scan` — agent notes

Shared safety scan: Bandit MEDIUM+ (`-c bandit.yaml`) and the lexical no-mocks
gate. See [README.md](README.md) for the command table and callers.

## Contract

- [`scan.sh`](scan.sh) is the only place those two commands are written. Both
  the composite step here and `run-public-lint`'s parallel wave execute this
  file, so the ci.yml lint job and the hardening security job cannot drift.
- Each gate runs as a background child with its own log; the script waits for
  all children and exits non-zero when any failed. Never replace that with a
  fire-and-forget launch — a lost failure would silently unblock a finding.
- `NO_MOCKS` and `BANDIT_TARGETS` accept only explicit values; an unsupported
  value exits 2 instead of scanning a narrower surface.
- `bandit.yaml` owns path exclusions and the LOW allow-list. Do not add
  exclusions here; a genuine new finding must fail the job.

## Editing

- Run `actionlint` and `shellcheck .github/actions/run-safety-scan/scan.sh`
  after changes, and keep [README.md](README.md) in step.
