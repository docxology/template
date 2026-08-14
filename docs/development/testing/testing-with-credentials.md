# Testing external and credentialed integrations

Credentialed provider calls are a separate, explicitly authorized lane. The
default test suite is hermetic: it uses temporary files, local HTTP servers,
dry-run adapters, and deterministic fixtures wherever possible. An ordinary
request to run tests does not authorize GitHub releases, Zenodo deposits,
uploads, deployments, account changes, or cleanup of remote resources.

## Current source contract

The root test configuration registers capability markers such as
`requires_ollama`, `requires_latex`, `requires_zenodo`, `requires_github`,
`requires_arxiv`, `requires_network`, and `requires_credentials`. Registration
does not prove that a collected test currently uses a marker. Check the exact
checkout before planning a live lane:

```bash
uv run pytest tests/ --collect-only -q -m requires_credentials
uv run pytest tests/ --collect-only -q -m requires_zenodo
uv run pytest tests/ --collect-only -q -m requires_github
```

A zero-test collection is `not applicable`, not a passed live integration
test. The authoritative hosted jobs and marker selection are in
[`../../../.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) and
[`../../../pyproject.toml`](../../../pyproject.toml).

## Default credential-free validation

Use the repository's maintained test contracts:

```bash
# Coverage-bearing infrastructure lane; excludes live/network/service lanes.
uv run python scripts/pipeline/stage_01_test.py --infra-only --infra-scope full

# One public project in its own pytest process.
uv run python scripts/pipeline/stage_01_test.py \
  --project templates/template_code_project --project-only
```

Run one project suite per process. Do not collect several project test trees in
one pytest process because their `tests.conftest` package names can collide.

Dry-run adapter tests establish request construction and failure behavior; they
do not establish credential validity, provider availability, account policy, or
permission to publish.

## Authorization checklist for a live lane

Before any external write, record all of the following:

1. The operator explicitly authorized the provider, target repository/account,
   payload, and write operation.
2. The target is a disposable sandbox or dedicated test resource. Production
   is not an acceptable default.
3. The exact payload and metadata passed local preflight and contain no
   local-only paths, secrets, stale generated evidence, or unintended files.
4. Credentials are least-privilege, short-lived where possible, and scoped to
   that target. Repository deletion or organization-wide administration is not
   needed for release tests.
5. The run has a unique, collision-resistant remote identifier and a bounded
   timeout.
6. Cleanup is an explicit, separately verified step. A test failure does not
   prove cleanup ran.
7. The result will be reported as `passed`, `failed`, `blocked`, `not run`,
   `not applicable`, or `unavailable`; a skip is never reported as a pass.

## Credential handling

Prefer provider-managed secret stores or environment variables supplied only
to the process that needs them. A repo-root `.env` is supported by some
publishing commands and is gitignored, but it remains plaintext local secret
material: restrict permissions and never copy it into fixtures, reports, or
generated artifacts.

```bash
chmod 600 .env
uv run python scripts/audit/check_staged_secrets.py
uv run python scripts/audit/check_tracked_secrets.py
```

Do not verify a secret with `echo`, include it on a command line, paste it into
a URL, or print a credentialed response. Command-line token flags can be
visible in process listings and shell history; prefer a narrowly scoped
environment variable.

Common publishing variables include:

| Provider | Variable | Boundary |
| --- | --- | --- |
| GitHub | `GITHUB_TOKEN`, `GITHUB_REPO` | Use a fine-grained token limited to a dedicated test repository. Do not grant repository deletion. |
| Zenodo sandbox | `ZENODO_SANDBOX_TOKEN` | Sandbox only unless production deposit authority is explicit. |
| Zenodo production | `ZENODO_PROD_TOKEN` | Production deposit; owner approval and release evidence required. |
| Pinata | `PINATA_JWT` | Scope to the intended pinning account and payload. |
| Hugging Face | `HUGGINGFACE_TOKEN` or `HF_TOKEN` | Write scope only for the target repository. |
| OSF | `OSF_TOKEN` | Limit to the intended project when the provider supports it. |

Consult the live CLI and publishing documentation for the exact variable used
by a provider. Never infer that a similarly named variable is accepted.

## Dry run before any provider call

The archival and multi-platform upload entry points are dry-run by default and
require `--commit` for writes:

```bash
uv run python scripts/runner/archive_publication.py \
  --project templates/template_code_project --providers software_heritage

uv run python scripts/publish/upload_gold_refinement.py --only testpypi
```

The unified GitHub/Zenodo release command is different: it performs real
provider work by default (against Zenodo sandbox unless `--production` is
given). Always pass `--dry-run` during rehearsal:

```bash
uv run python scripts/publish/publish_project_release.py \
  --project templates/template_code_project \
  --tag v0.0.0-rehearsal \
  --repo owner/dedicated-test-repository \
  --dry-run
```

Removing `--dry-run`, adding `--commit`, or adding `--production` is a material
authority change. Reconfirm the target, payload hashes, source revision, and
operator approval immediately before doing so.

## CI secrets

Credentialed CI should be a dedicated, protected workflow or environment, not
part of pull-request validation from untrusted forks. Bind secrets directly to
the one step that needs them:

```yaml
- name: Authorized sandbox integration
  if: github.event_name == 'workflow_dispatch'
  env:
    ZENODO_SANDBOX_TOKEN: ${{ secrets.ZENODO_SANDBOX_TOKEN }}
  run: uv run pytest tests/path/to/explicit_live_test.py -v
```

Do not write secrets to `.env` with shell `echo`, upload `.env` as an artifact,
or expose secrets to arbitrary pull-request code. Use GitHub environments and
required reviewers for production credentials.

## Local optional tools

Ollama and LaTeX are capability-gated but are not credentials. Their missing
tool behavior, explicit opt-out commands, and timeout policy are documented in
[`../optional-dependencies.md`](../optional-dependencies.md). Ollama can pull
large model data and execute local model code, so installation and model pulls
still require operator intent.

## Cleanup and incident handling

- Record every remote identifier created by a live run before attempting
  cleanup.
- Use provider-native listing/read APIs to verify the exact target before a
  delete operation.
- Do not run wildcard, account-wide, or repository-delete cleanup commands.
- If a credential may have appeared in output, logs, git history, or a URL,
  rotate it at the provider. Deleting the local value is not sufficient.
- Follow
  [`../../security/credential-rotation-handoff.md`](../../security/credential-rotation-handoff.md)
  for a confirmed leak.

## See also

- [`../../../tests/AGENTS.md`](../../../tests/AGENTS.md) — test-suite policy
- [`../../../.github/AGENTS.md`](../../../.github/AGENTS.md) — hosted CI jobs
- [`../optional-dependencies.md`](../optional-dependencies.md) — local capability gates
- [`../../security/threat-model.md`](../../security/threat-model.md) — publication and credential boundaries
- [`../../guides/publication-runbook.md`](../../guides/publication-runbook.md) — owner-operated release flow
