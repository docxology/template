# Publishing readiness

This is a durable operator checklist, not a statement that any external account,
token, provider API, DOI, repository setting, or artifact is currently ready.
Older platform snapshots become stale quickly; re-verify external state from the
provider's official documentation and record the date and exact source revision.

## Keep the decisions separate

Report these as independent states:

1. **Engineering:** tests, lint, types, security, confidentiality, and generated
   artifact guards passed for the named revision.
2. **Evidence and scholarship:** manuscript claims, citations, statistics,
   figures, and captions are source-current and reviewed.
3. **Rendered artifact:** the intended PDF/web/archive payload was regenerated
   from that revision and passed structural and accessibility gates.
4. **Provider readiness:** the adapter, current provider API, account policy,
   credentials, quota, and destination permissions were checked.
5. **Authority:** the owner approved the exact payload and external destination.
6. **Outcome:** remote push, release, deposit, DOI registration, or publication
   actually succeeded and was independently verified.

A local pass establishes none of the later states. An implemented adapter does
not prove an account or provider is ready. A dry-run does not prove a live write
will succeed. A successful upload does not prove scientific or owner approval.

## Source-current manuscript preflight

Set one qualified project name and run the gates against the same reviewed
revision. Replace the placeholder literally rather than relying on a default
project:

```bash
PROJECT="templates/<name>"

uv run python -m infrastructure.validation.cli prerender \
  "projects/$PROJECT/manuscript" --repo-root .

uv run python -m infrastructure.reference.citation.cli validate \
  "projects/$PROJECT/manuscript/references.bib" --strict

uv run python -m infrastructure.reference.verification verify \
  "projects/$PROJECT/manuscript/references.bib" \
  --live --as-of-year <YEAR>

uv run python -m infrastructure.validation.cli evidence \
  "projects/$PROJECT" --fail-on-issues

uv run python -m infrastructure.validation.cli publication-audit \
  --project "$PROJECT" --rendered --strict \
  --require-figure-accessibility --format markdown
```

The live verifier depends on external resolvers. Record resolver/network
failures and `unchecked` or `unverifiable` references honestly; warning status
is not evidence that a citation exists. An offline cache-only run is useful for
replay but must not be reported as a live check. The figure-accessibility gate
checks that required descriptions are present, not that the prose is
scientifically adequate; review captions, legends, encodings, and alt text by
hand. The publication audit with `--rendered` must consume artifacts regenerated
from the same source revision, not a convenient older hydrated copy.

## Provider rehearsal

Before any credentialed command:

- inspect `git status --short --branch`, the exact project/output root, and the
  payload manifest;
- run `scripts/audit/check_tracked_all.py` and the generated-artifact/secret
  gates so private sidecars and local paths cannot cross the public boundary;
- verify current CLI help and provider documentation instead of copying old
  endpoint, token-scope, free-tier, endorsement, or quota claims;
- use a least-privilege test credential and sandbox destination where the
  provider actually supports them;
- preserve receipts outside source-authored docs unless the repository defines
  a canonical generated-evidence owner.

Commit semantics differ by entry point:

- `scripts/publish/publish_project_release.py` can perform real external writes
  by default. Every rehearsal must pass `--dry-run`; Zenodo's sandbox default is
  separate from dry-run, and `--production` changes the destination.
- `scripts/runner/archive_publication.py` and upload-runner commands are dry-run
  unless `--commit` is supplied.
- Direct provider CLIs may have different semantics. Confirm with `--help` at
  the reviewed revision; never infer safety from a neighboring command.

Do not place real tokens on the command line, in documentation, or in tracked
`.env` files. Account creation, terms acceptance, endorsements, payment/quota
decisions, and release approval remain with the human/provider authority.

## Live publication checklist

Proceed only when the owner has approved the exact manifest and destination:

- bind the manifest and generated receipts to the reviewed commit;
- confirm the local and upstream branch/remote SHAs and preserve unrelated
  dirty work;
- confirm credentials came from the intended secret store without printing
  values or credentialed URLs;
- make one bounded provider write; do not retry an ambiguous timeout blindly;
- capture a redacted provider identifier/URL and independently read it back;
- verify the public payload contains no private paths, secrets, stale variables,
  omitted figures, or unreviewed generated prose;
- record publication outcome separately from engineering, scholarship, owner
  approval, push, and release status.

If a required network, credential, renderer, reviewer, or authority is
unavailable, the honest result is `unchecked`, `skipped`, or
`blocked-external`—never `passed` or `published`.

## Related

- [`../guides/publication-runbook.md`](../guides/publication-runbook.md)
- [`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md)
- [`../security/credential-rotation-handoff.md`](../security/credential-rotation-handoff.md)
- [`release-boundary.md`](release-boundary.md)
- [`archival-targets.md`](archival-targets.md)
