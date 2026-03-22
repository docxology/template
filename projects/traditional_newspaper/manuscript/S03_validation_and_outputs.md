# Supplement: Validation and outputs

```{=latex}
\begin{multicols}{3}
```

**Markdown validation.** Run `python3 -m infrastructure.validation.cli markdown projects/traditional_newspaper/manuscript/` before large merges. The CLI checks reference integrity, image paths, and other structural rules configurable per project. Failures should block PDF generation in CI the same way failing tests do.

**PDF validation.** After render, `python3 -m infrastructure.validation.cli pdf output/traditional_newspaper/pdf/` scans for unresolved citations (`[?]`), reference tokens (`??`), and common LaTeX warnings surfaced in text extraction. Treat warnings as debt even when builds succeed.

**Combined artifact paths.** Combined markdown often lands at `output/traditional_newspaper/pdf/_combined_manuscript.md` during debugging; the compiled PDF is `traditional_newspaper_combined.pdf` (exact names follow renderer conventions). Individual section PDFs help bisect errors when one slice breaks LaTeX.

**Web output.** `WebRenderer` produces HTML under `output/traditional_newspaper/web/`. Figures embedded via raw LaTeX become `<figure>` elements when Lua filters recognize `\begin{figure}` blocks. Verify captions render after changing caption text.

**Slides.** Beamer slides per stem land in `output/traditional_newspaper/slides/`. Slide builds can fail independently of the combined PDF if a single section includes incompatible raw TeX—keep slides in CI if your team relies on them.

**Data outputs.** `manuscript_stats.json` tracks word counts. Future analysis scripts could emit CSV metrics on column heights or paragraph counts—implement in `src/` with tests, then call from `scripts/`.

**Integrity and checksums.** Optional integrity modules hash outputs for provenance. Steganography tooling (`secure_run.sh`) post-processes PDFs without mutating originals; security-focused teams may enable it.

**Failure triage order.** When a build breaks, read the LaTeX log tail, identify the first undefined control sequence or missing file, fix that, and rebuild. Pandoc errors precede LaTeX errors chronologically in logs—start at the earliest failure.

**Environment reproducibility.** Document `uv` version, Python version, and TeX distribution in your lab handbook. Container images in `infrastructure/docker/` help teammates match environments without sharing laptops.

**Cross-project lessons.** Other projects in the monorepo use the same validation entry points; fixes to shared infrastructure benefit everyone. File issues upstream when validators misfire on legitimate markdown patterns.

```{=latex}
\end{multicols}
```
