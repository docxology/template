# Supplement: Validation and outputs

```{=latex}
\begin{figure}[!ht]
\centering
\includegraphics[width=\linewidth]{../output/figures/section_banner_S03_validation_and_outputs.png}
\caption{Validation supplement banner (B\&W).}
\label{fig:banner_S03_validation_and_outputs}
\end{figure}
\begin{figure}[!ht]
\centering
\includegraphics[width=0.92\linewidth]{../output/figures/wordcount_bars_bw.png}
\caption{Black-and-white horizontal bar chart of word counts per manuscript slice, generated from \texttt{manuscript\_stats.json} by \texttt{visualization\_wordcount\_bw.py} (runs after \texttt{report\_manuscript\_stats.py} in analysis). Bars use grayscale fills only.}
\label{fig:wordcount_bw}
\end{figure}
\begin{multicols}{3}
```

Figure~\ref{fig:wordcount_bw} summarizes edition word counts for quick sanity checks alongside validators below.

**Markdown validation.** Run `python3 -m infrastructure.validation.cli markdown projects/traditional_newspaper/manuscript/` before large merges. The CLI checks reference integrity, image paths, and other structural rules configurable per project. Failures should block PDF generation in CI the same way failing tests do.

**PDF validation.** After render, `python3 -m infrastructure.validation.cli pdf output/traditional_newspaper/pdf/` scans for unresolved citations (`[?]`), reference tokens (`??`), and common LaTeX warnings surfaced in text extraction. Treat warnings as debt even when builds succeed.

**Combined artifact paths.** Combined markdown often lands at `output/traditional_newspaper/pdf/_combined_manuscript.md` during debugging; the compiled PDF is `traditional_newspaper_combined.pdf` (exact names follow renderer conventions). Individual section PDFs help bisect errors when one slice breaks LaTeX.

**Web output.** `WebRenderer` produces HTML under `output/traditional_newspaper/web/`. Figures embedded via raw LaTeX become `<figure>` elements when Lua filters recognize `\begin{figure}` blocks. Verify captions render after changing caption text.

**Slides.** Beamer slides per stem land in `output/traditional_newspaper/slides/`. Slide builds can fail independently of the combined PDF if a single section includes incompatible raw TeX—keep slides in CI if your team relies on them.

**Data outputs.** `manuscript_stats.json` tracks word counts. `visualization_wordcount_bw.py` reads that JSON and writes `output/figures/wordcount_bars_bw.png` (monochrome bar chart, Figure~\ref{fig:wordcount_bw}).

**Integrity and checksums.** Optional integrity modules hash outputs for provenance. Steganography tooling (`secure_run.sh`) post-processes PDFs without mutating originals; security-focused teams may enable it.

**Failure triage order.** When a build breaks, read the LaTeX log tail, identify the first undefined control sequence or missing file, fix that, and rebuild. Pandoc errors precede LaTeX errors chronologically in logs—start at the earliest failure.

**Environment reproducibility.** Document `uv` version, Python version, and TeX distribution in your lab handbook. Container images in `infrastructure/docker/` help teammates match environments without sharing laptops.

**Cross-project lessons.** Other projects in the monorepo use the same validation entry points; fixes to shared infrastructure benefit everyone. File issues upstream when validators misfire on legitimate markdown patterns.

**Longer read: operational playbooks.** Treat validation logs like server logs: keep the last N successful artifacts, timestamp them, and attach commit SHAs. When a professor or reviewer asks “which PDF did you mean?”, the answer should be a git tag plus a CI run ID, not “the one on my desktop.” Copy stages that mirror `projects/*/output/` into `output/*/` exist precisely so deliverable paths stabilize for that conversation.

**Bisection tactics.** If combined PDF fails but individual slices succeed, binary-search which stem introduces the fault by temporarily moving half the markdown files aside—careful not to break `validate_inventory`—or by compiling partial combined markdown. Another approach: inspect `_combined_manuscript.tex` around the error line LaTeX reports.

**Performance.** Full XeLaTeX passes dominate pipeline time for large manuscripts. Caching unchanged slices is tempting but risks stale cross-references; prefer incremental development on single sections via `03_render_pdf.py` flags when available, then full combined builds before release.

**Artifact hygiene.** `output/` directories are disposable per project policy, yet humans treat them as precious. `.gitignore` keeps binaries out of version control; document regeneration commands in README so newcomers are not afraid to delete stale PDFs.

**Security scanning.** PDFs can embed JavaScript or launch actions; validators may flag anomalies. Trusted toolchains reduce surprise. Do not paste untrusted LaTeX from the internet into `preamble.md` without review.

**Accessibility retesting.** When figure captions change, rerun HTML export and spot-check screen-reader order: does the caption immediately follow the image in the DOM? Lua filter ordering can affect results.

**Localization.** Validation messages from CLIs are English today; wrapping them for i18n would help global teams. Manuscript content can be non-English if fonts and hyphenation languages align—validators should remain locale-agnostic.

**Contract tests.** `validate_inventory` is a contract: filenames implied by `sections.py` must exist. Adding optional supplements requires updating that tuple—treat it like an API semver bump for downstream stats scripts.

**Hand-off checklist.** Before declaring a release: all tests green, markdown validation clean, PDF validation clean, figures regenerated, `manuscript_stats.json` refreshed, and a human skimmed captions for typos. Automation covers everything except the last step—for now.

```{=latex}
\end{multicols}
```
