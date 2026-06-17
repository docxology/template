# `setup-python-env` composite action

Shared CI setup: provision [`uv`](https://github.com/astral-sh/setup-uv) (with a
`uv.lock`-keyed cache) and install Python via `actions/setup-python`. Factored
out of [`../../workflows/ci.yml`](../../workflows/ci.yml) so the pinned action
SHAs and cache configuration live in one place instead of being copy-pasted
across ~12 jobs.

## Usage

```yaml
steps:
  - uses: actions/checkout@<sha>          # REQUIRED first — see below
  - uses: ./.github/actions/setup-python-env
    # with:
    #   python-version: ${{ matrix.python-version }}   # omit for the 3.12 default
  - run: uv sync                          # per-job dependency groups stay explicit
```

`actions/checkout` must run first: a local composite action's files are only
present in the workspace after checkout.

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `python-version` | `"3.12"` | Version passed to `actions/setup-python`. Matrix jobs pass `${{ matrix.python-version }}`. |

## Scope

Used by every Python job in `ci.yml`. The `detect` and `actionlint` jobs are
checkout-only and do not use it. Each calling job keeps its own `uv sync …`
line so optional groups (`rendering` / `monitoring` / `discopy`) remain visible
per job.
