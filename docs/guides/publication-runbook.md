# Publication runbook

Use this page as the front door when a project is ready to leave the local
template checkout and become a public, citable publication.

The publication workflow is modular. The GitHub plus Zenodo path is the core
release. Other targets are optional mirrors that can be added after the DOI and
standalone repository exist.

## Scope

| Need | Canonical tool |
| --- | --- |
| Render and validate the project | `scripts/runner/execute_pipeline.py`, `scripts/pipeline/stage_04_validate.py` |
| Create a DOI-bearing Zenodo release and GitHub release | `scripts/publish/publish_project_release.py` |
| Record durable identifiers in project docs | `infrastructure.publishing.status_report` |
| Publish optional mirrors | `scripts/publish/upload_template_project.py` |
| Archive executable bundles | `scripts/runner/archive_publication.py` |
| Export to the separate `docxology/publishing` repo | `scripts/publish/export_for_publishing.py` |

`publish_project_release.py` does not create the standalone GitHub repository.
Create the public repository first, then use the script to attach the release
asset and cross-link it with Zenodo.

## Required publication state

Use qualified project names for pipeline and release commands, for example
`templates/template_code_project`. The stable source of public exemplar names
and current publication status is
[`docs/_generated/publication_records.md`](../_generated/publication_records.md).

Before a real release, the project should have:

- `projects/<qualified-name>/manuscript/config.yaml` with `paper.title`,
  `paper.version`, `authors`, `keywords`, and a `publication` block.
- A rendered combined PDF under either `output/<qualified-name>/pdf/` or
  `projects/<qualified-name>/output/pdf/`.
- A public standalone repository such as `docxology/template_code_project`.
- A GitHub token with repository release permissions.
- A Zenodo token. Use `ZENODO_SANDBOX_TOKEN` for dry rehearsals and
  `ZENODO_PROD_TOKEN` for a real DOI.

Recommended `.env` keys:

```dotenv
GITHUB_TOKEN=...
GITHUB_REPO=docxology/template_code_project
ZENODO_SANDBOX_TOKEN=...
ZENODO_PROD_TOKEN=...
```

The release script loads the repo-root `.env` automatically. Command-line token
flags and exported environment variables override `.env`.

## Preflight

Run the local gates before touching public APIs:

```bash
PROJECT=templates/template_code_project

uv sync
uv run python scripts/runner/execute_pipeline.py --project "$PROJECT" --core-only
uv run python scripts/pipeline/stage_04_validate.py --project "$PROJECT"
uv run python -m infrastructure.publishing.credential_check --only github zenodo --env-file .env
```

Optional but useful for release notes and release dashboards:

```bash
uv run python -m infrastructure.reporting.release_readiness \
  --out output/release_readiness.md
uv run python scripts/docgen/publication_records.py --refresh-external
```

## First real release

For a first public release where the PDF cover must already contain the real
Zenodo concept DOI, use the reserve-first flow:

```bash
PROJECT=templates/template_code_project
REPO=docxology/template_code_project
TAG=v1.0.0

uv run python scripts/publish/publish_project_release.py \
  --project "$PROJECT" \
  --tag "$TAG" \
  --repo "$REPO" \
  --production \
  --reserve-doi-first
```

What this does:

1. Creates a Zenodo draft and reserves the DOI pair.
2. Writes `publication.doi` as the stable concept DOI.
3. Writes `publication.version_doi` and `publication.version_record` for the
   first immutable version.
4. Re-renders the PDF so the cover carries the concept DOI.
5. Uploads the DOI-bearing PDF to Zenodo and publishes it.
6. Creates the GitHub release and attaches the release-bundle PDF.
7. Writes `output/<project>/release_bundle/RELEASE_RECEIPT.json`.

Commit the changed publication sidecars after checking the receipt:

```bash
uv run python -m infrastructure.publishing.status_report \
  --project "projects/$PROJECT" --write
uv run python scripts/docgen/publication_records.py --refresh-external
```

Review and commit the updated `manuscript/config.yaml`, `CITATION.cff`,
`.zenodo.json`, generated publication records, project README publishing-status
block, and release-bundle receipt if the project tracks it.

## New version of an existing DOI series

When `publication.doi` already contains the concept DOI, publish a new immutable
Zenodo version:

```bash
PROJECT=templates/template_code_project
REPO=docxology/template_code_project
TAG=v1.0.1

uv run python scripts/publish/publish_project_release.py \
  --project "$PROJECT" \
  --tag "$TAG" \
  --repo "$REPO" \
  --production \
  --new-version
```

The workflow keeps `publication.doi` stable and updates only
`publication.version_doi` plus `publication.version_record`.

## Standalone GitHub mirror

The monorepo remains the render source of truth. The standalone repository is a
publication mirror for source, DOI metadata, GitHub releases, and tracked public
artifacts.

Minimum mirror contents:

- Project source tree from `projects/<qualified-name>/`.
- Project-local `output/` tree when files are within the public output ceiling.
- `CITATION.cff`, `.zenodo.json`, `README.md`, and `manuscript/config.yaml`.
- Git tag matching the release tag passed to `publish_project_release.py`.

After publishing, verify the mirror and the DOI matrix:

```bash
uv run python scripts/docgen/publication_records.py --refresh-external
```

Do not hand-edit `docs/_generated/publication_records.md`; regenerate it.

## Optional mirrors

After the core GitHub plus Zenodo release exists, publish optional mirrors from
the same rendered artifacts. Verify credentials first:

```bash
uv run python -m infrastructure.publishing.credential_check --env-file .env
```

Generic public exemplar uploader:

```bash
# Dry-run; project is the leaf name under projects/templates/.
uv run python scripts/publish/upload_template_project.py \
  --project template_code_project

# Real uploads to selected core mirrors.
uv run python scripts/publish/upload_template_project.py \
  --project template_code_project \
  --commit \
  --only pinata huggingface osf testpypi

# Include static-site hosts when their CLIs and tokens are configured.
uv run python scripts/publish/upload_template_project.py \
  --project template_code_project \
  --commit \
  --include-static
```

The generic uploader expects an already rendered project-local PDF at
`projects/templates/<name>/output/pdf/<name>_combined.pdf` and writes a receipt
to `output/templates/<name>/upload_receipts.json`.

## Platform surface

The registry in `infrastructure.publishing.registry` has two tiers:

| Tier | Meaning |
| --- | --- |
| `first_class` | Implemented, tested, and locally verifiable. |
| `documented` | Publication intent is documented, but no live adapter is shipped. |

First-class platforms are Zenodo, GitHub Releases, arXiv tarball preparation,
PyPI/TestPyPI, IPFS Pinata, IPFS Web3.Storage, Software Heritage, GitHub Pages,
Cloudflare Pages, Netlify, HuggingFace Hub, and OSF.

Documented ebook, print, retail, and payment targets are Amazon KDP, Google Play
Books, Gumroad, Leanpub, Lulu, Draft2Digital, Stripe, and IngramSpark. Use
`scripts/publish/export_for_publishing.py` for the handoff to the separate
`docxology/publishing` distribution pipeline.

## Archival bundle

For long-horizon archival, build and archive an executable bundle:

```bash
PROJECT=templates/template_code_project

uv run python scripts/runner/bundle_executable.py --project "$PROJECT"
uv run python scripts/runner/archive_publication.py \
  --project "$PROJECT" \
  --providers zenodo software_heritage ipfs_pinata \
  --commit
```

The archival stage defaults to dry-run unless `--commit` is present.

## Final verification

`status_report.py --check` and `publication_records.py --refresh-external` verify
different things — run both, they are not substitutes for each other. `--check`
only asks "does the committed README block match what `config.yaml` currently
says" (fully offline, deterministic — catches a stale block, not a fabricated
claim). `--refresh-external` and `--verify-reachability` are the two commands
that actually leave the machine and ask GitHub/Zenodo whether the record is
real:

```bash
PROJECT=templates/template_code_project

# Offline: README publishing-status block matches config.yaml
uv run python -m infrastructure.publishing.status_report \
  --project "projects/$PROJECT" --check

# Live: refreshes the repo-wide DOI/GitHub matrix from the real GitHub REST API
# (repo + latest release) and the Zenodo Records API — the same class of check
# a manual `gh release view` + `curl https://zenodo.org/api/records/<id>` does.
uv run python scripts/docgen/publication_records.py --refresh-external

# Live, opt-in, display-only: HEAD-probes the public GitHub repo URL (not the
# rate-limited API) and the DOI resolver for THIS project's own config, and
# prints (never commits) a downgrade for any identifier that 404s/410s. Exists
# specifically because the offline --check trusts a non-empty DOI/repo field
# blindly — a private or deleted repo still reads "published" without this.
uv run python -m infrastructure.publishing.status_report \
  --project "projects/$PROJECT" --verify-reachability

uv run python scripts/audit/check_template_drift.py --strict
```

**Confirm the DOI actually landed on the rendered PDF cover** — `publication.doi`
being set in config is not proof the PDF was re-rendered after the write. Read
the real page text, don't trust the pipeline exit code:

```bash
pdftotext -f 1 -l 1 -layout \
  "output/$PROJECT/pdf/$(basename "$PROJECT")_combined.pdf" - | grep -i "10.5281/zenodo"
```

Then manually open the GitHub release, the Zenodo record page (confirm
`state`/`submitted` in the API JSON, not just that the URL loads), and any
optional mirror URLs recorded in `publication.published_artifacts`. The
committed source of truth is the project `publication` block plus generated
status/report files, not the machine-specific credential state.

## Deep dives

- [Publishing guide](publishing-guide.md)
- [Zenodo DOI strategy](zenodo-doi-strategy.md)
- [Publishing module reference](../modules/guides/publishing-module.md)
- [Publishing scripts](../../scripts/publish/README.md)
- [Archival targets](../maintenance/archival-targets.md)
- [Publication records](../_generated/publication_records.md)
