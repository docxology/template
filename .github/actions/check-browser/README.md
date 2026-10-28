# check-browser

Composite action: select the runner's **installed** Google Chrome for native
consumer controls, or fail.

```yaml
- name: Select the installed browser
  if: matrix.browser
  uses: ./.github/actions/check-browser
```

The action asserts, in order:

1. `/opt/google/chrome/chrome` exists, is executable, and is **not** a symlink —
   the hosted runner also exposes a development Chromium snapshot and aliases.
2. `/opt/google/chrome/resources.pak` exists, so the runtime is a complete
   application bundle rather than a bare binary.
3. `"$chrome" --version` succeeds, proving the runtime starts.
4. `CHROME_EXECUTABLE_PATH` is exported for the later native consumer.

Callers: the `test-infra` and `test-contract` jobs of
[`ci.yml`](../../workflows/ci.yml). Both previously carried byte-identical copies
of this block, so it now exists once.

[`setup-acceptance-documents`](../setup-acceptance-documents/action.yml) keeps its
own Linux check: it runs inside a branch that also prepares TeX, must fail with a
preparation-specific message, and selects the browser only for `native` mode. That
block is not identical, so it was deliberately not folded into this action.

## Editing

- Never weaken a `test` to a warning: a missing or aliased browser must fail the
  job, not silently skip native controls.
- Keep the export name `CHROME_EXECUTABLE_PATH`; the rendering and publication
  readers resolve it by that name.
- Run `actionlint` after edits and keep the sibling README/AGENTS pair current.
