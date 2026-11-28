# Publishing Scripts

This directory contains scripts for packaging and distributing template/ outputs — both to PyPI (for the template infrastructure itself) and to the docxology/publishing repo (for finished manuscripts and ebooks).

For the full modular release path from rendered project to standalone public
GitHub mirror, real Zenodo DOI, optional mirrors, and archival handoff, start at
[`../../docs/guides/publication-runbook.md`](../../docs/guides/publication-runbook.md).

## Scripts

| Script | Purpose |
|---|---|
| `test_pypi.py` | Build, upload to TestPyPI, retrieve the admitted bytes, and verify installation |
| `verify_install.py` | Verify an admitted wheel and its original SHA-256 in an offline environment |
| `upload_template_project.py` | Upload a rendered exemplar project to all configured platforms (Zenodo, HuggingFace, OSF, etc.) |
| `upload_gold_refinement.py` | Original hand-tuned reference uploader for the gold-standard exemplar |
| `publish_project_release.py` | Core GitHub release + Zenodo DOI orchestrator for an already-created standalone public repository |
| `sync_standalone_mirrors.py` | Sync public exemplars into their standalone publication repositories (dry-run by default; `--commit` to push) |
| `export_for_publishing.py` | **Bridge script** — bundle template/ outputs for the docxology/publishing repo |

Standalone installation can explicitly use `--install-projection` to replace
admitted monorepo provider paths with existing full Git commit pins. Advanced
also needs `--meta-provider` and `--meta-commit` for the Meta projection committed
from the same platform revision. Canonical source exports remain exact without
the flag. See [installation projection](../../docs/guides/standalone-install-projection.md)
for provenance, verification, and the separate public installation acceptance.

---

## Bridge: template/ → docxology/publishing

The `export_for_publishing.py` script bundles rendered output for a downstream publishing checkout. It writes to `output/publishing_exports/` by default; pass `--output-dir /path/to/publishing/workspace/imports` for a direct handoff.

### Two-repo architecture

```
template/                          publishing/
├── projects/<name>/               ├── workspace/
│   ├── manuscript/                │   └── imports/
│   │   └── config.yaml            │       └── <name>-<timestamp>/
│   └── output/                    │           ├── manifest.json
│       ├── pdf/                   │           ├── pdf/
│       ├── ebook/                 │           ├── epub/
│       ├── docx/                  │           ├── docx/
│       └── metadata/              │           └── metadata/
└── scripts/publish/               └── src/
    └── export_for_publishing.py       └── docxology_publishing/
```

`template/` **produces** artifacts. `publishing/` **distributes** them to marketplaces (Gumroad, Leanpub, Stripe, etc.).

### Workflow

1. **Render** — run the template pipeline to produce PDF, EPUB, MOBI, metadata packages
2. **Export** — run `export_for_publishing.py` to bundle outputs and write a `manifest.json`
3. **Import** — the publishing pipeline reads from `workspace/imports/` and cross-posts to platforms

```bash
# Step 1: render (from template/ root)
./run.sh --project templates/my_book --pipeline --mode core

# Step 2: export
uv run python scripts/publish/export_for_publishing.py \
    --project templates/my_book --output-dir /path/to/publishing/workspace/imports

# Step 3: in the publishing repo
cd /path/to/publishing
uv run docpub import workspace/imports/latest/manifest.json
uv run docpub distribute --platform gumroad
```

### What export_for_publishing.py does

1. Resolves the project root from the qualified project name
2. Resolves the authored manuscript config for title, author, and metadata. Standalone sources use `docs/manuscript/config.yaml`.
3. Scans `output/pdf/`, `output/ebook/`, `output/docx/`, and `output/metadata/` for generated artifacts
4. Creates a timestamped subdirectory under `--output-dir` (default: `output/publishing_exports/` under the selected repository)
5. Copies all discovered artifacts into the bundle subdirectory
6. Writes `manifest.json` with paths, checksums, timestamps, and config metadata
7. Creates/updates the `latest` symlink pointing to the new export

### Manifest schema

```json
{
  "schema_version": "1.0",
  "exported_at": "2026-07-02T12:00:00Z",
  "project": "templates/my_book",
  "source_root": "/path/to/template/projects/templates/my_book",
  "metadata": {
    "title": "My Book",
    "author": "Author Name",
    "isbn": "...",
    "license": "CC-BY-4.0"
  },
  "artifacts": {
    "pdf": [{"filename": "my_book_combined.pdf", "path": "pdf/my_book_combined.pdf", "sha256": "...", "size_bytes": 123456}],
    "epub": [{"filename": "my_book.epub", "path": "epub/my_book.epub", "sha256": "...", "size_bytes": 78901}],
    "metadata": [{"filename": "onix.xml", "path": "metadata/onix.xml", "sha256": "...", "size_bytes": 4321}],
    "docx": []
  }
}
```

### Prerequisites

- The template pipeline has been run and `output/` is populated
- For a direct handoff, supply the `workspace/imports/` directory of your chosen `docxology/publishing` checkout with `--output-dir`.
- The `workspace/imports/` directory exists (created automatically if missing)

---

## PyPI package checks

Run the commands from the repository root.

### Local build preview

Prepare the locked build backend. The local preview builds one wheel and one
source distribution in private scratch and returns their SHA-256 digests. It
uses no registry credentials.

```bash
uv sync --locked --group installed-build
uv run --no-sync python - <<'PYTHON'
from pathlib import Path

from infrastructure.publishing.pypi import PyPIAdapter, PyPIConfig

preview = PyPIAdapter(PyPIConfig(test=True), env={}).publish(Path.cwd(), dry_run=True)
if not preview.ok:
    raise SystemExit(preview.error)
for filename, sha256 in preview.receipt["artifacts"].items():
    print(sha256, filename)
PYTHON
```

### TestPyPI sandbox transfer

Run this only for an explicitly approved TestPyPI transfer. Supply
`TEST_PYPI_API_TOKEN` through the process environment. The script uploads the
admitted archives, retrieves the exact package version and hashes, and runs an
isolated installed check.

```bash
uv sync --locked --group installed-build --group publishing
uv run --no-sync python scripts/publish/test_pypi.py --timeout-seconds 600
```

Production PyPI promotion requires a separate reviewed release contract.
[Publishing adapter guide](../../infrastructure/publishing/pypi/README.md)

### Exact wheel installation check

Set `admitted_wheel` to the retained wheel path and `admitted_wheel_sha256` to
its original digest from the admission record. The verifier uses the prepared
locked runtime and checks the installed package offline.

```bash
uv run --no-sync python scripts/publish/verify_install.py \
  --wheel "$admitted_wheel" --sha256 "$admitted_wheel_sha256"
```

## Troubleshooting

### Missing publishing tools

Prepare the lock groups shown above for the requested operation. The scripts
check for the prepared build backend and, for TestPyPI transfer, Twine.

### Export: no artifacts found

Run the pipeline first:
```bash
./run.sh --project templates/my_book --pipeline --mode core
```

Check that `output/pdf/` contains files after the render stage.

### Symlink `latest` not updating

The exporter updates `latest` atomically under the chosen export root. Use a
writable destination and reserve `latest` for the exporter’s symlink. The
manifest for the newest bundle is `latest/manifest.json`.

## See also

- [`AGENTS.md`](AGENTS.md) — agent-facing publishing boundaries and verification commands
- [`../../infrastructure/publishing/AGENTS.md`](../../infrastructure/publishing/AGENTS.md) — publishing infrastructure
- [`../../docs/maintenance/publishing-export-pipeline.md`](../../docs/maintenance/publishing-export-pipeline.md) — design document for the two-repo pipeline
