# Stage 10 — Executable Bundle (opt-in stage)

> Created 2026-05-20. Design document for an opt-in long-horizon artifact path. The stage contract is declared in `pipeline.yaml` for traceability, but `PipelineExecutor` filters `bundle` / `archival` tags out of default runs; invoke `scripts/08_executable_bundle.py` directly when intentionally producing this artifact. Addresses World-Threat-Model findings at the 5-15-year horizon where PDF-as-primary-deliverable becomes legacy and executable-artifact-as-primary becomes the norm.
>
> **Naming note:** this guide and its filename predate the later insertion of
> the Ebook Generation and Metadata Package stages into `pipeline.yaml`
> (`docs/maintenance/publishing-export-pipeline.md` was fixed for the same
> drift in a prior pass). In the *current* `pipeline.yaml` numbering,
> Executable Bundle is **Stage 12** and Archival Publication is **Stage 13**
> (see CLAUDE.md's stage table); "Stage 10" in this filename/prose is the
> historical name kept for URL/reference stability, not the live stage index.
> The table below uses the current, correct numbering.

## Why this stage exists

The World Threat Model run identified that:

- At 5-year horizon (~2031): PDF transitions from primary to archival; the working medium is an executable bundle
- At 10-year horizon (~2036): static PDF is a compatibility output, not the primary deliverable
- At 15+ year horizon: PDF is the citation fossil; the unit-of-research is a container + code + data + claim graph

The default core pipeline ends with output validation and copy-output delivery. There is no default stage that produces a **container + lockfile + agent-runnable manifest** as a parallel artifact. This is the gap Stage 10 fills when invoked explicitly.

## What Stage 10 produces

For each project, a single `output/<project>/executable_bundle/` directory containing:

```
executable_bundle/
├── Dockerfile                       # Reproducible build environment
├── docker-compose.yml               # One-command run
├── lockfile/
│   ├── uv.lock                      # Pinned Python deps
│   ├── apt-packages.lock            # Pinned OS packages
│   └── tlmgr-packages.lock          # Pinned LaTeX packages
├── manifest.json                    # Agent-runnable manifest (see schema below)
├── data/                            # Snapshot of input data (or pointers + SHA-256s)
├── source/                          # Snapshot of projects/<project>/{src,scripts,manuscript}
├── README.md                        # "How to reproduce this publication"
└── PROVENANCE.json                  # Build environment + commit hash + deterministic seeds
```

## Manifest schema

```json
{
  "schema_version": "1.0",
  "project_name": "template_code_project",
  "commit_hash": "abc123...",
  "rendered_at": "2026-05-20T12:00:00Z",
  "renderer": "template/v1.0.0",
  "entry_points": {
    "reproduce_all": "docker compose run reproduce",
    "tests": "docker compose run tests",
    "render_pdf": "docker compose run render",
    "verify_claims": "docker compose run verify"
  },
  "claims": [
    {
      "id": "figure_03_panel_b",
      "manuscript_section": "03_results.md / Figure 3 panel (b)",
      "value": 0.4271,
      "tolerance": 0.0003,
      "verifier_function": "projects.template_code_project.src.analysis.compute_convergence_rate",
      "verifier_args": {"n_trials": 1000, "seed": 42}
    }
  ],
  "external_data": [
    {
      "url": "https://example.org/dataset.csv",
      "sha256": "...",
      "size_bytes": 12345
    }
  ],
  "archival_receipts": {
    "zenodo_doi": "10.5281/zenodo.19139090",
    "software_heritage_swhid": "swh:1:dir:...",
    "ipfs_cid_primary": "Qm...",
    "ipfs_cid_redundant": "Qm..."
  }
}
```

The manifest is **the contract** between this template and any future agentic verifier. An agent in 2036 reading this manifest can:

1. Reconstitute the build environment from the Dockerfile + lockfiles
2. Re-execute each claim's verifier function
3. Compare against the pinned value within tolerance
4. Report PASS/FAIL per claim

## Relationship to existing stages

| Stage | Produces | Status |
| --- | --- | --- |
| Stage 0: Clean | empty output | existing |
| Stage 1: Env setup | dependency check | existing |
| Stage 2: Infra tests | 60% coverage signal | existing |
| Stage 3: Project tests | 90% coverage signal | existing |
| Stage 4: Analysis | figures + data | existing |
| Stage 5: PDF rendering | static PDF (archival artifact) | existing |
| Stage 6: Validation | quality report | existing |
| Stage 7: LLM draft assistance | LLM-aided review | existing (relabeled 2026-05-20) |
| Stage 8: LLM translations | zh/hi/ru abstracts | existing |
| Stage 9: Copy outputs | final deliverables to output/ | existing |
| Stage 10: Ebook generation | EPUB/MOBI/DOCX | opt-in (`ebook` tag) |
| Stage 11: Metadata package | ONIX/metadata.json/content.opf | opt-in (`metadata` tag) |
| **Stage 12: Executable bundle** | **container + lockfile + manifest** | **implemented as an opt-in stage** |
| **Stage 13: Archival publication** | **dry-run or committed archival manifest/deposits** | **implemented as an opt-in stage** |

The declared Executable Bundle stage depends on PDF rendering and is filtered out of default runs by its `bundle` tag. Archival Publication depends on Executable Bundle and is filtered out by its `archival` tag. The default full run still ends with Copy Outputs; invoke these long-horizon stages directly when intentionally producing bundles or archival records.

## Why "parallel to Stage 5" not "replacing Stage 5"

- PDF retains long-term archival value (LaTeX → PDF is 50+ year stable)
- Zenodo DOIs bind to PDFs in current practice
- Citation infrastructure expects PDFs
- The executable bundle is the *working* artifact; the PDF is the *citing* artifact
- A template trying to be useful at both 2-year and 20-year horizons needs both

## Implementation status

Implemented pieces:

1. `scripts/08_executable_bundle.py` builds `output/<project>/executable_bundle/`.
2. `infrastructure/rendering/manifest.py` reads `tests/regression/pinned_values/<project>.json` when present and writes `manifest.json`.
3. `infrastructure/rendering/dockerfile_gen.py` writes a Dockerfile and `docker-compose.yml`.
4. `pipeline.yaml` declares the `Executable Bundle` stage with tag `bundle`; default runs filter it out.
5. `scripts/09_archive_publication.py` and the `Archival Publication` stage provide the downstream opt-in archival path.

Remaining hardening:

1. Add a dedicated `--bundle-only` `run.sh` convenience flag if direct script invocation proves awkward.
2. Cross-test the public canonical exemplars in CI with the generated container.
3. Decide whether reproducibility should be byte-identical or content-equivalent when timestamps are present.
4. Add a dedicated CI job once container runtime availability is stable.

## Out of scope for v1

- Cross-project bundles (multi-project deliverables) — single-project only initially
- GPU support in the container — CPU only
- Network access at reproduction time — bundle is self-contained
- Re-execution of LLM stages (Stage 7/8) — these stay optional and skipped in the bundle

## Open questions

1. **Container image size.** A LaTeX-full base image is ~2-3 GB. Acceptable, or should we ship a slim image + on-demand `tlmgr install`?
2. **Long-term Dockerfile compatibility.** Docker itself may be succeeded by 2036. Should the bundle also include a `nix` flake or a `Guix` manifest as alternative reproducibility primitives?
3. **External-data policy.** Datasets that can't be redistributed (license restrictions) — how does the manifest reference them while remaining reproducible?
4. **Backward compatibility with existing publications.** Do we retroactively generate bundles for already-published manuscripts via the Zenodo DOI 10.5281/zenodo.19139090?

These need decisions before treating the bundle as a release gate.

## Status

**Opt-in implementation.** The stage contract is declared in `pipeline.yaml`, and the direct script writes a bundle. It is not part of default, `--core-only`, or LLM-inclusive full runs.

## Related

- [`README.md`](README.md) — guide hub
- [`regression-testing.md`](regression-testing.md) — the `pinned_values/` source for the manifest's claims section
- [`archival-targets.md`](archival-targets.md) — the archival receipts captured in the manifest
- [`infrastructure/core/pipeline/pipeline.yaml`](../../infrastructure/core/pipeline/pipeline.yaml) — declared Stage 12 (Executable Bundle) and Stage 13 (Archival Publication) contracts
