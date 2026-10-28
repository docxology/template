# `check-browser` — agent notes

Selects the installed Google Chrome runtime for native consumer controls. See
[README.md](README.md) for the assertions and callers.

## Contract

- The checks are blocking: file present, executable, not a symlink,
  `resources.pak` present, `--version` succeeds. Removing any one of them lets a
  Chromium development snapshot stand in for the supported runtime.
- The action exports `CHROME_EXECUTABLE_PATH` into `$GITHUB_ENV`; consumers read
  that exact name. Do not rename it or print a user-controlled path.
- Callers keep their own `if:` (`matrix.browser`, or unconditional in the
  `test-infra` prep). This action decides nothing about selection.
- `setup-acceptance-documents` intentionally keeps a separate Linux check: it
  fails with a preparation-specific message and runs inside the `native` branch
  that also prepares TeX. Do not merge the two without preserving that message.

## Editing

- Run `actionlint` after edits, keep [README.md](README.md) accurate, and confirm
  both `ci.yml` callers still gate on their original condition.
