# Archival Targets — insurance against single-vendor archival concentration

> Created 2026-05-20. Addresses World-Threat-Model RedTeam attack A10 (Zenodo / arXiv / DOI vendor concentration) at low cost.

## Why this guide exists

The current publishing pipeline targets:

- **Zenodo** (CERN-backed) — primary archive, DOI assignment
- **arXiv** (Cornell) — scholarly entry, preprint tracking
- **GitHub** — source code + template diffusion

These institutions have been stable for 15–20 years and are likely safe through the next decade. But the World Threat Model run flagged that on the **multi-decade horizon** the template claims (30–50 years), even CERN/Cornell policy changes are non-zero, and a template that puts all archival eggs in those three baskets is over-concentrated.

This guide documents two cheap parallel archival targets that buy genuine multi-decade insurance: **IPFS** (or content-addressed equivalents) and **Software Heritage**.

## Parallel archival principle

For any artifact that matters multi-decadally (published manuscript PDF + Zenodo deposit + source-code snapshot at publication), pin it to at least 3 of the following independent archival systems:

| System | What it preserves | Permanence horizon | Vendor risk |
| --- | --- | --- | --- |
| **Zenodo** (CERN) | Files + metadata + DOI | 50+ years (institutional commitment) | Single-institution policy risk |
| **arXiv** (Cornell) | Preprint + LaTeX source | 30+ years | Single-institution policy risk |
| **GitHub** (Microsoft) | Source code + history | Until Microsoft says otherwise | High brand-vendor risk |
| **Software Heritage** | Source code (cross-host harvested) | 100+ year mission, library-funded | Low — French gov + UNESCO partnership |
| **IPFS pin** (Pinata, Filecoin, Web3.Storage) | Files by content hash | Depends on pinning service | Distributed; needs at least 2 pins |
| **Internet Archive** | Web pages, PDFs | 30+ years; mission-aligned | Single-org policy risk |

The strategy is **redundancy across independent failure domains**, not picking a single winner. Pick 3 from the above for every multi-decade-relevant artifact.

## Recommended default: Zenodo + Software Heritage + 2 IPFS pins

For each publication:

1. **Primary**: Zenodo deposit with DOI (already in `infrastructure/publishing/`)
2. **Source-code mirror**: Software Heritage automatically harvests from GitHub; verify after each release at `https://archive.softwareheritage.org/browse/origin/?origin_url=<repo_url>`
3. **Content-addressed redundancy**: two independent IPFS pins (e.g., Pinata + Web3.Storage), with the CIDs (content identifiers) recorded in the Zenodo metadata

## What goes in each artifact bundle

A "publication" in this context means a manuscript + its reproducibility bundle. The archived bundle should include:

- **The rendered PDF** (Stage 5 output) — the human-readable canonical artifact
- **The Markdown manuscript sources** (`projects/<name>/manuscript/`) — durable plain-text
- **A frozen lockfile** (`uv.lock` snapshot at publication commit)
- **The source-code commit hash** (linked to the GitHub commit + Software Heritage snapshot)
- **A `MANIFEST.json`** listing all files + their SHA-256 hashes
- **A `PROVENANCE.json`** with build environment metadata (Python version, OS, deterministic seed values used)

The current publishing pipeline produces some of these; the rest are the gap this guide is addressing.

## Implementation

The code lives at `infrastructure/publishing/archival/` (`providers.py`,
`orchestrate.py`, `models.py`; driven by the opt-in Stage 13 wrapper
`scripts/09_archive_publication.py`). The public entry point is
`archive_publication()`:

```python
def archive_publication(
    bundle: Path,
    *,
    providers: list[ArchivalProvider],
    dry_run: bool = True,
    output_receipts_path: Path | None = None,
) -> ArchivalRun:
    """Mirror a publication bundle to N independent archival targets.

    dry_run defaults to True; pass dry_run=False to perform real deposits.
    Never raises on a per-provider failure — failures surface as
    status="error" receipts inside the returned ArchivalRun. Each receipt
    records the target name, the URL / DOI / CID / SWHID of the deposited
    artifact, a timestamp, and any partial-failure mode.
    """
```

Concrete provider classes (`ZenodoProvider`, `IPFSPinataProvider`,
`IPFSWeb3StorageProvider`, `SoftwareHeritageProvider`) implement the
`ArchivalProvider` protocol; `load_credentials()` resolves their tokens.

The function:

1. Validates the bundle is complete (PDF, sources, lockfile, manifest)
2. For each target, calls the target-specific deposit API (Zenodo REST API, IPFS HTTP API, SWH save-code-now API)
3. Records every CID/DOI/SWHID in a receipts JSON written to the caller-supplied `output_receipts_path` (recommended: commit it alongside the publication)
4. Updates `STATUS.md` with the most recent successful archival run

## Credentials & secrets

- Zenodo API token: keep in `~/.zenodo/credentials` (per-user, not in repo)
- Pinata JWT: per-user, not in repo
- Web3.Storage token: per-user, not in repo
- Software Heritage: no token needed for save-code-now; uses GitHub URL

`load_credentials()` reads credentials from environment variables first
(`ZENODO_API_TOKEN`, `PINATA_JWT`, `WEB3_STORAGE_TOKEN`), then falls back to a
per-user JSON file at `~/.config/template-archival/credentials.json` — **never**
from any in-repo file. If credentials are missing, each provider emits a
structured per-target receipt indicating it was unreachable rather than raising.

## Verifying archival

After each publication run:

1. **Zenodo**: visit DOI URL, confirm files are listed and downloadable
2. **Software Heritage**: visit `https://archive.softwareheritage.org/browse/origin/?origin_url=<repo>` and confirm the latest commit is harvested
3. **IPFS**: `ipfs cat <CID>` from a fresh node should return the file; alternatively use a public gateway like `https://ipfs.io/ipfs/<CID>`
4. **Manifest**: every file in `MANIFEST.json` must be retrievable from at least 2 independent targets

The verification step is part of `STATUS.md` row "Publishing" — refresh quarterly.

## Disaster scenarios this addresses

| Scenario | Probability (50yr) | Mitigated by |
| --- | --- | --- |
| Zenodo discontinued / scope-changed | ~10% | Software Heritage + IPFS retain source + bundle |
| arXiv policy change makes preprints harder to deposit | ~20% | Zenodo + IPFS retain PDF |
| GitHub-the-brand replaced; URL changes | ~40% | Software Heritage retains code; IPFS retains bundle |
| All three IPFS pins lapse (no one paying) | ~70% over 50yr if not maintained | Zenodo + Software Heritage retain artifact even without IPFS |
| Single nation-state restricts access to one provider | ~50% | Multi-provider redundancy means at least one is reachable from anywhere |

## What this does NOT do

- **Does not** guarantee 50-year file readability — that depends on format durability (PDF/A, plain text, durable LaTeX), not archival redundancy. See `docs/maintenance/stage-10-executable-bundle.md` for the format-durability question.
- **Does not** preserve the *runnable* pipeline — that requires container snapshots, see `stage-10-executable-bundle.md`.
- **Does not** preserve external datasets — if your data lives at a third-party URL, archive it too (deposit a copy on Zenodo, or pin to IPFS) as part of the publication bundle.

## Status

Implemented as the opt-in Stage 13 archival path. `archive_publication()` and
its provider classes live in `infrastructure/publishing/archival/`; invoke via
`scripts/09_archive_publication.py` (dry-run by default — pass `--commit` plus
`--providers` for real deposits; see the CLAUDE.md quick-reference). See
[`MAINTAINERS.md`](../../MAINTAINERS.md) for the `infrastructure/publishing/` owner.

## Related

- [`README.md`](README.md) — guide hub
- [`stage-10-executable-bundle.md`](stage-10-executable-bundle.md) — the runnable-artifact direction
- [`infrastructure/publishing/`](../../infrastructure/publishing/) — current publishing module
- [`STATUS.md`](../../STATUS.md) — verification cadence
