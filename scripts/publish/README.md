# Publishing Scripts

This directory contains scripts for packaging and distributing template/ outputs — both to PyPI (for the template infrastructure itself) and to the docxology/publishing repo (for finished manuscripts and ebooks).

For the full modular release path from rendered project to standalone public
GitHub mirror, real Zenodo DOI, optional mirrors, and archival handoff, start at
[`../../docs/guides/publication-runbook.md`](../../docs/guides/publication-runbook.md).

## Scripts

| Script | Purpose |
|---|---|
| `test_pypi.py` | Build → TestPyPI upload → fresh-venv install → `template doctor` |
| `verify_install.py` | Verify the published package installs correctly from PyPI |
| `upload_template_project.py` | Upload a rendered exemplar project to all configured platforms (Zenodo, HuggingFace, OSF, etc.) |
| `upload_gold_refinement.py` | Original hand-tuned reference uploader for the gold-standard exemplar |
| `publish_project_release.py` | Core GitHub release + Zenodo DOI orchestrator for an already-created standalone public repository |
| `export_for_publishing.py` | **Bridge script** — bundle template/ outputs for the docxology/publishing repo |

---

## Bridge: template/ → docxology/publishing

The `export_for_publishing.py` script is the formal handoff point between this repo's rendering pipeline and the downstream publishing pipeline in `~/Documents/GitHub/publishing/`.

### Two-repo architecture

```
template/                          publishing/
├── projects/<name>/               ├── workspace/
│   ├── manuscript/                │   └── imports/
│   │   └── config.yaml            │       └── <name>-<timestamp>/
│   └── output/                    │           ├── manifest.json
│       ├── pdf/                   │           ├── pdf/
│       ├── ebook/                 │           ├── ebook/
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
./run.sh --project templates/my_book --pipeline --core-only

# Step 2: export
uv run python scripts/publish/export_for_publishing.py \
    --project templates/my_book

# Step 3: in the publishing repo
cd ~/Documents/GitHub/publishing
uv run docpub import workspace/imports/my_book-latest/manifest.json
uv run docpub distribute --platform gumroad
```

### What export_for_publishing.py does

1. Resolves the project root from the qualified project name
2. Reads `manuscript/config.yaml` for title, author, and metadata
3. Scans `output/pdf/`, `output/ebook/`, and `output/metadata/` for generated artifacts
4. Creates a timestamped subdirectory under `--output-dir` (default: `~/Documents/GitHub/publishing/workspace/imports/`)
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
    "pdf": [{"filename": "my_book_combined.pdf", "sha256": "...", "size_bytes": 123456}],
    "epub": [{"filename": "my_book.epub", "sha256": "...", "size_bytes": 78901}],
    "metadata": [{"filename": "onix.xml", "sha256": "...", "size_bytes": 4321}]
  }
}
```

### Prerequisites

- The template pipeline has been run and `output/` is populated
- `~/Documents/GitHub/publishing/` exists (clone of docxology/publishing)
- The `workspace/imports/` directory exists (created automatically if missing)

---

## PyPI Publishing Workflow

### 1. TestPyPI dry run

```bash
export TEST_PYPI_API_TOKEN="pypi-xxxx..."
uv run python scripts/publish/test_pypi.py
```

### 2. Production publish

```bash
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="$PYPI_TOKEN"
twine upload dist/*
```

Never pass API tokens as command-line arguments — they appear in process listings and logs.

### 3. Post-publish verification

```bash
uv run python scripts/publish/verify_install.py
```

### Optional environment variables

| Variable | Purpose | Default |
|---|---|---|
| `TEST_PYPI_API_TOKEN` | TestPyPI upload token | required for test_pypi.py |
| `PACKAGE_NAME` | Override package name | `template` |
| `INDEX_URL` | Custom package index URL | `https://pypi.org/simple/` |

---

## Troubleshooting

### twine not found

`test_pypi.py` auto-installs twine; if that fails: `pip install twine`

### Build failures

```bash
uv sync --all-groups  # verify dependency resolution
```

### TestPyPI upload rejects package

- Verify package name is available on TestPyPI
- Version must be unique (TestPyPI requires version bump for re-upload)
- Ensure `TEST_PYPI_API_TOKEN` has upload scope

### Export: no artifacts found

Run the pipeline first:
```bash
./run.sh --project templates/my_book --pipeline --core-only
```

Check that `output/pdf/` contains files after the render stage.

### Symlink `latest` not updating

The script removes the old symlink before creating a new one. If it fails (e.g. permissions), delete manually:
```bash
rm ~/Documents/GitHub/publishing/workspace/imports/latest
```

## See also

- [`AGENTS.md`](AGENTS.md) — agent-facing guide with CI integration examples
- [`../../infrastructure/publishing/AGENTS.md`](../../infrastructure/publishing/AGENTS.md) — publishing infrastructure
- [`../../docs/maintenance/publishing-export-pipeline.md`](../../docs/maintenance/publishing-export-pipeline.md) — design document for the two-repo pipeline
