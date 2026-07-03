# Publishing Export Pipeline

> Created 2026-07-02. Design document for the two-repo publication workflow:
> how `template/` (this repo) and `docxology/publishing` work together to
> take a finished manuscript from rendered artifact to confirmed marketplace
> listing.

## Overview

The research template system spans two repositories with complementary
responsibilities:

| Repository | Role |
|---|---|
| `docxology/template` (`template/`) | Produces artifacts: PDF, EPUB, MOBI, DOCX, metadata packages |
| `docxology/publishing` (`publishing/`) | Distributes artifacts: cross-posts to Gumroad, Leanpub, Stripe, etc. |

The **handoff point** is `scripts/publish/export_for_publishing.py`, which
bundles a project's `output/` directory into a timestamped import package that
the publishing repo can consume.

---

## Workflow diagram

```
template/                              publishing/
─────────────────────────────          ──────────────────────────────────────
 projects/<name>/
   manuscript/config.yaml ──────────→  (read for metadata)
   output/
     pdf/                 ──────────→  bundle → workspace/imports/
     ebook/               ──────────→  bundle
     metadata/            ──────────→  bundle
                                             │
scripts/publish/                             │
  export_for_publishing.py ───────────→  manifest.json (+ symlink latest/)
                                             │
                                             ▼
                                       docpub import manifest.json
                                             │
                                  ┌──────────┴──────────────┐
                                  ▼          ▼              ▼
                               Gumroad   Leanpub         Stripe
                              (PDF+EPUB) (EPUB only)  (direct sale)
                                  │
                                  └──→  [confirmation receipts]
```

### ASCII pipeline flow

```
[1] RENDER (template/)
    ./run.sh --project templates/<name> --pipeline --core-only
         │
         ▼ produces
    projects/<name>/output/
      pdf/  ebook/  metadata/

[2] EXPORT (template/)
    uv run python scripts/publish/export_for_publishing.py --project templates/<name>
         │
         ▼ creates
    publishing/workspace/imports/<name>-<timestamp>/
      manifest.json
      pdf/
      epub/
      metadata/
    publishing/workspace/imports/latest  → <name>-<timestamp>  (symlink)

[3] IMPORT (publishing/)
    cd ~/Documents/GitHub/publishing
    uv run docpub import workspace/imports/latest/manifest.json
         │
         ▼ validates + stages artifacts

[4] DISTRIBUTE (publishing/)
    uv run docpub distribute --platform gumroad
    uv run docpub distribute --platform leanpub
    uv run docpub distribute --platform stripe
         │
         ▼
    [per-platform receipts written to workspace/receipts/]
```

---

## What each repo does

### template/ (this repo)

The template repo's rendering pipeline produces all publication-ready
artifacts. Each stage writes to `projects/<name>/output/`:

| Stage | Output location | Format |
|---|---|---|
| Stage 5: PDF Rendering | `output/pdf/` | `<name>_combined.pdf` |
| Stage 10: EPUB/MOBI | `output/ebook/` | `<name>.epub`, `<name>.mobi` |
| Stage 11: Metadata package | `output/metadata/` | `onix.xml`, `metadata.json`, `content.opf` |

Stage 10 and Stage 11 are opt-in stages (tagged `bundle` and `archival`
respectively). Invoke them explicitly:

```bash
uv run python scripts/08_executable_bundle.py --project templates/<name>
uv run python scripts/09_archive_publication.py --project templates/<name>
```

### scripts/publish/export_for_publishing.py

The bridge script:

1. Resolves the project root from the qualified name (e.g. `templates/my_book`)
2. Reads `manuscript/config.yaml` for title, author, ISBN, DOI, license, etc.
3. Scans `output/pdf/`, `output/ebook/`, and `output/metadata/`
4. Creates a timestamped bundle under `--output-dir`
5. Copies all discovered artifacts into the bundle
6. Writes `manifest.json` with paths, SHA-256 checksums, timestamps, and config metadata
7. Updates the `latest` symlink

### publishing/ (docxology/publishing repo)

The publishing repo reads the manifest and cross-posts to configured
marketplaces. It owns:

- Marketplace credential management (`credentials/`)
- Platform adapters (Gumroad, Leanpub, Stripe, Amazon KDP)
- Pricing and listing metadata
- Sales data collection and reporting

---

## Manifest schema

The manifest written by `export_for_publishing.py` is the contract between
the two repos:

```json
{
  "schema_version": "1.0",
  "exported_at": "2026-07-02T12:00:00Z",
  "project": "templates/my_book",
  "source_root": "/Users/.../template/projects/templates/my_book",
  "metadata": {
    "title": "My Book Title",
    "author": "Author Name",
    "doi": "10.5281/zenodo.XXXXXXXX",
    "isbn13": "978-...",
    "license": "CC-BY-4.0",
    "publisher": "Research Template Press",
    "publication_date": "2026-07-01",
    "keywords": ["keyword1", "keyword2"],
    "github_repo": "docxology/my-book"
  },
  "artifacts": {
    "pdf": [
      {
        "filename": "my_book_combined.pdf",
        "path": "pdf/my_book_combined.pdf",
        "sha256": "abc123...",
        "size_bytes": 2345678
      }
    ],
    "epub": [
      {
        "filename": "my_book.epub",
        "path": "epub/my_book.epub",
        "sha256": "def456...",
        "size_bytes": 890123
      }
    ],
    "metadata": [
      {
        "filename": "onix.xml",
        "path": "metadata/onix.xml",
        "sha256": "ghi789...",
        "size_bytes": 4567
      },
      {
        "filename": "metadata.json",
        "path": "metadata/metadata.json",
        "sha256": "jkl012...",
        "size_bytes": 1234
      }
    ]
  }
}
```

---

## Per-platform notes

### Gumroad

- Accepts: PDF, EPUB, and any additional files (DOCX, source zip)
- Cover image: 1280×1920 px (portrait); provide as `output/assets/cover.jpg`
- Pricing: set in `publishing/credentials/credentials.yaml` under `gumroad.default_price`
- Snippet: product description sourced from `metadata.abstract` + DOI link

### Leanpub

- Accepts: EPUB only (generates PDF from its own toolchain)
- Requires: `leanpub_slug` in `manuscript/config.yaml` → `publication.leanpub_slug`
- EPUB must pass Leanpub's subset validation; use `docpub check --platform leanpub`

### Stripe (direct sale)

- Accepts: PDF (delivered as a download link)
- Requires: Stripe product ID or creates one on first run
- Price: from `publishing/credentials/credentials.yaml` → `stripe.price_usd`
- Fulfillment: Stripe handles delivery via signed S3/R2 URL

### Amazon KDP (Kindle Direct Publishing)

- Accepts: EPUB (for Kindle) + PDF (for print-on-demand)
- Requires: ISBN-13 in `manuscript/config.yaml` → `publication.isbn13`
- Metadata mapping: ONIX XML is converted to KDP metadata format
- Note: KDP review takes 24–72 hours; receipts are pending until approved

### IngramSpark (print-on-demand)

- Accepts: PDF (interior) + PDF (cover) — separate files
- Requires: ISBN-13 and BISAC subject codes
- Cover PDF: 300 DPI, exact trim-size spine calculation based on page count
- Use `docpub check --platform ingram` before submitting

---

## Configuration reference

### template/ side: `manuscript/config.yaml`

Fields read by `export_for_publishing.py`:

| Field | Type | Used for |
|---|---|---|
| `title` | string | manifest metadata |
| `author` / `authors` | string / list | manifest metadata |
| `isbn` / `isbn13` | string | Gumroad, Leanpub, KDP |
| `doi` | string | manifest, ONIX |
| `license` | string | manifest, listing text |
| `publisher` | string | ONIX, KDP |
| `publication_date` | string (ISO 8601) | ONIX, KDP |
| `keywords` | list | ONIX, Leanpub categories |
| `abstract` | string | listing description |
| `language` | string | ONIX (default: `en`) |
| `github_repo` | string | listing URL |
| `publication.leanpub_slug` | string | Leanpub platform |

### publishing/ side: `credentials/credentials.yaml`

See `credentials/credentials.yaml.template` for the full schema.

| Section | Key | Purpose |
|---|---|---|
| `gumroad` | `access_token` | API auth |
| `gumroad` | `default_price` | product price in USD |
| `leanpub` | `api_key` | API auth |
| `stripe` | `secret_key` | API auth |
| `stripe` | `price_usd` | product price |
| `kdp` | `email` + `password` | KDP web automation |
| `ingram` | `username` + `password` | IngramSpark portal |

---

## Troubleshooting

### "no artifacts found under output/"

The pipeline has not been run, or outputs were cleaned. Run:
```bash
./run.sh --project templates/<name> --pipeline --core-only
```

For EPUB/MOBI (Stage 10):
```bash
uv run python scripts/08_executable_bundle.py --project templates/<name>
```

### "Project not found: 'my_book'"

Use a qualified name:
```bash
uv run python scripts/publish/export_for_publishing.py --project templates/my_book
```

List available projects:
```bash
uv run python -m infrastructure.project.public_scope list
```

### Symlink `latest` not updating

Delete the stale symlink and re-run:
```bash
rm ~/Documents/GitHub/publishing/workspace/imports/latest
uv run python scripts/publish/export_for_publishing.py --project templates/<name>
```

### Manifest SHA-256 mismatch on import

The artifact was modified after export. Re-run the export:
```bash
uv run python scripts/publish/export_for_publishing.py --project templates/<name>
```

### Leanpub EPUB validation fails

Run the Leanpub pre-flight:
```bash
cd ~/Documents/GitHub/publishing
uv run docpub check --platform leanpub workspace/imports/latest/manifest.json
```

Common causes:
- Missing required metadata (title, author, language)
- Image DPI below 72 PPI
- Internal navigation (`toc.ncx`) missing headings

### Gumroad product already exists

Add `--update` to update the existing product listing instead of creating a new one:
```bash
uv run docpub distribute --platform gumroad --update
```

---

## Related

- [`scripts/publish/export_for_publishing.py`](../../scripts/publish/export_for_publishing.py) — the bridge script
- [`scripts/publish/README.md`](../../scripts/publish/README.md) — quick-start guide
- [`stage-10-executable-bundle.md`](stage-10-executable-bundle.md) — Stage 10 design
- [`archival-targets.md`](archival-targets.md) — long-horizon archival (Stage 11)
- [`private-projects-repo.md`](private-projects-repo.md) — private-projects sidecar contract
- [`infrastructure/publishing/AGENTS.md`](../../infrastructure/publishing/AGENTS.md) — publishing infrastructure
- [`../../publishing/workspace/README.md`](../../../../publishing/workspace/README.md) — workspace directory guide
