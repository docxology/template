# Publishing readiness — what we can upload today vs. what needs a token

> Status snapshot: 2026-06-27. Covers the full 12-platform publishing surface in
> `infrastructure/publishing/` and a concrete per-platform assessment of the
> `template_gold_refinement` exemplar. Re-verify external state before citing as live.

## TL;DR

Every adapter is implemented, registered first-class, and dry-run verified end
to end. What separates "publishable today" from "blocked" is **credentials and
account policy**, not code. There are three tiers:

- **Tier A — publishable today, no account/token.** Software Heritage (real
  archival of a public repo) and arXiv *tarball preparation* (local only).
- **Tier B — needs one free token/account, then fully automated.** TestPyPI,
  Pinata (IPFS), Netlify, Cloudflare Pages, GitHub Pages, HuggingFace Hub, OSF.
  Zenodo and GitHub Releases also live here (already exercised in production).
- **Tier C — blocked on more than a token.** arXiv *posting* (needs
  endorsement), Web3.Storage (adapter needs the new Storacha/w3up auth).

## Tier A — publishable today (no account, no token)

| Platform | What it does | Action | Notes |
| --- | --- | --- | --- |
| **Software Heritage** | Permanent source-code archive (SWHID) of a public Git repo | `archival_cli --providers software_heritage --commit` (or the adapter) | No token. Only works on a **public** GitHub repo. Idempotent; safe to re-run. The one free *real* publish available right now. |
| **arXiv (prepare)** | Builds the submission tarball locally | `prepare_arxiv_submission(...)` | No network, no account. Posting is Tier C (endorsement). |

## Tier B — needs one free token/account, then fully automated

Create the account, generate a scoped token, drop it in the repo-root `.env`
(gitignored), and the adapter runs unattended. **You create the account and
token; I cannot create accounts, enter passwords, accept terms, or solve
CAPTCHAs** — those stay with you. Once the token is in `.env`, I run the upload.

| Platform | Sign-up → token page | Scope | `.env` variable | Free tier |
| --- | --- | --- | --- | --- |
| **TestPyPI** | test.pypi.org/account/register → Account → API tokens | "Entire account" (first upload) | `TESTPYPI_TOKEN` | Yes (test index) |
| **Pinata** (IPFS) | app.pinata.cloud → API Keys → New Key | pinFileToIPFS / admin | `PINATA_JWT` | Yes (1 GB) |
| **Netlify** | app.netlify.com → User settings → Applications → New access token | personal access token | `NETLIFY_AUTH_TOKEN` | Yes |
| **Cloudflare Pages** | dash.cloudflare.com → My Profile → API Tokens | "Cloudflare Pages: Edit" template | `CLOUDFLARE_API_TOKEN` | Yes (generous) |
| **GitHub Pages** | uses a GitHub token | `repo` / Pages write | `GITHUB_TOKEN` (or `gh auth token`) | Yes |
| **HuggingFace Hub** | huggingface.co/settings/tokens | **write** | `HUGGINGFACE_TOKEN` / `HF_TOKEN` | Yes |
| **OSF** | osf.io/settings/tokens | `osf.full_write` | `OSF_TOKEN` | Yes |
| **Zenodo** | zenodo.org → Applications → Personal access tokens | deposit:write, deposit:actions | `ZENODO_PROD_TOKEN` / `ZENODO_SANDBOX_TOKEN` | Yes (already in production use) |
| **GitHub Releases** | github.com tokens or `gh auth token` | `repo` | `GITHUB_TOKEN` | Yes (already in production use) |

PyPI policy reminder: a **real** PyPI upload is permanent — the name + version
are claimed forever and cannot be re-uploaded. Current decision: **TestPyPI
only**, which is safe and repeatable.

## Tier C — blocked on more than a token

| Platform | Blocker | Path forward |
| --- | --- | --- |
| **arXiv (post)** | Endorsement. As of **2026-01-21** an institutional email alone no longer qualifies. Need (a) institutional email + prior authorship in that domain, or (b) a personal endorsement from an established author in the same domain. | Prepare the tarball now; pursue a personal endorsement, or post via an endorsed co-author. Zenodo already provides a citable DOI in the meantime. |
| **Web3.Storage** | Migrated to the Storacha/w3up auth model; the adapter targets the legacy `api.web3.storage` token flow. | Update `IPFSWeb3StorageProvider` to w3up before issuing a token. Pinata already covers the IPFS use case. |

## Validation performed (no account needed)

- **All 12 adapters** dry-run clean (correct endpoints/URLs, no network side
  effects).
- **PyPI pipeline** proven end-to-end except the push: `python -m build`
  produces sdist + wheel and `twine check` **PASSES**.
- **Adapter tests**: 13/13 new HuggingFace + OSF tests pass; full publishing
  suite 543 passed (the only failures are an unrelated missing optional
  `qrcode` package in the transmission-bookend code).

---

# `template_gold_refinement` — per-platform assessment

Readiness check (`validate_publication_readiness`): **ready_for_publication =
true, completeness 85/100**, no missing elements.

Artifacts present (real, not synthesized):

- Combined PDF — `output/pdf/template_gold_refinement_combined.pdf` (3.2 MB)
- Web build — `output/web/` (11 HTML files) → ready for static-site hosting
- `CITATION.cff`, `.zenodo.json`, `uv.lock`, `pyproject.toml`
- Already on **Zenodo**: concept DOI `10.5281/zenodo.20931955`, version DOI
  `10.5281/zenodo.20938523` (record `zenodo.org/records/20938523`)
- GitHub repo: `docxology/template_gold_refinement`

Fix applied this pass: the project `pyproject.toml` had no `readme`/`license`/
`keywords`, so a PyPI page would have rendered blank. Added them; the package
now builds and `twine check` **PASSES clean** (no warnings).

## Can it publish to each platform?

| Platform | Status for gold_refinement | What's needed |
| --- | --- | --- |
| **Zenodo** | ✅ Already published (DOI live) | New version via `publish_project_release.py --new-version` when content changes |
| **GitHub Releases** | ✅ Repo exists; release cut-able now | `GITHUB_TOKEN` (or `gh auth token`) |
| **Software Heritage** | ✅ **Publishable today** (repo is public) | Nothing — just your go-ahead to trigger the save |
| **arXiv (prepare)** | ✅ Tarball preparable now | — |
| **TestPyPI** | ✅ Builds clean (verified) | `TESTPYPI_TOKEN` |
| **HuggingFace Hub** | ✅ Ready (3.2 MB PDF < 10 MB inline ceiling) | `HUGGINGFACE_TOKEN` |
| **OSF** | ✅ Ready (PDF + bundle) | `OSF_TOKEN` |
| **Pinata** (IPFS) | ✅ Ready (bundle pins as one CID) | `PINATA_JWT` |
| **GitHub Pages** | ✅ `output/web/` ready | `GITHUB_TOKEN` |
| **Netlify** | ✅ `output/web/` ready | `NETLIFY_AUTH_TOKEN` + `netlify` CLI |
| **Cloudflare Pages** | ✅ `output/web/` ready | `CLOUDFLARE_API_TOKEN` + `wrangler` CLI |
| **arXiv (post)** | ⛔ Endorsement required | See Tier C |
| **Web3.Storage** | ⛔ Adapter needs Storacha update | See Tier C |

**Net:** gold_refinement can target **11 of 13** platforms. 2 are live/ready with
no token (Zenodo done, Software Heritage one-click), the remaining 8 each need a
single free token, and only arXiv-posting and Web3.Storage are genuinely blocked.

## Exact commands once a token is in `.env`

```bash
# Static site (web build already exists)
NETLIFY_AUTH_TOKEN=...  netlify deploy --dir projects/templates/template_gold_refinement/output/web --prod
CLOUDFLARE_API_TOKEN=... wrangler pages deploy projects/templates/template_gold_refinement/output/web --project-name gold-refinement

# IPFS pin of the publication bundle
uv run python -m infrastructure.publishing.archival_cli \
  --bundle output/templates/template_gold_refinement \
  --providers ipfs_pinata --commit

# Software Heritage (NO token needed — Tier A)
uv run python -m infrastructure.publishing.archival_cli \
  --bundle <file-with-repo-url> --providers software_heritage --commit

# TestPyPI (build already verified)
TESTPYPI_TOKEN=... uv run python -c "from pathlib import Path; \
from infrastructure.publishing.pypi import run_pypi_release; \
print(run_pypi_release(Path('projects/templates/template_gold_refinement'), test=True, dry_run=False))"
```

HuggingFace and OSF run through `HuggingFaceHubAdapter` / `OSFAdapter`
respectively (see each subpackage `README.md`).
