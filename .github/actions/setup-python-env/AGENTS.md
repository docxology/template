# `setup-python-env` — technical reference

Composite action wrapping the shared CI Python setup. See
[`README.md`](README.md) for usage and inputs.

## Steps (in order)

1. `astral-sh/setup-uv` — SHA-pinned; `enable-cache: true`,
   `cache-dependency-glob: "**/uv.lock"`.
2. `actions/setup-python` — SHA-pinned; `python-version` from the input
   (default `"3.12"`).

It deliberately does **not** run `actions/checkout` (the caller does, first) and
does **not** run `uv sync` (kept explicit per job so dependency groups stay
visible).

## Invariants

- Third-party `uses:` are pinned to a full commit SHA with a `# vX.Y.Z` comment,
  matching [`../../workflows/ci.yml`](../../workflows/ci.yml).
- The SHAs here are the single source of truth for the setup block; bump them
  here, not per job.
- Changing inputs or step order requires updating the "Shared setup" section of
  [`../../workflows/AGENTS.md`](../../workflows/AGENTS.md) in the same change.

## Verification

- `actionlint` (CI `actionlint` job) validates this action and its callers.
- Behavioural proof is the next CI run: GitHub Actions ordering (local action
  resolves only post-checkout) cannot be exercised by local `actionlint`.
