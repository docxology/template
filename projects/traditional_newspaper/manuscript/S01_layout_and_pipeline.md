# Supplement: Layout and pipeline

```{=latex}
\begin{multicols}{3}
```

**How this PDF is built.** Sixteen markdown slices under `projects/traditional_newspaper/manuscript/` are discovered by `infrastructure.rendering.manuscript_discovery.discover_manuscript_files`, combined in stem order, and separated by `\newpage` inside `infrastructure.rendering.pdf_renderer.PDFRenderer` before Pandoc emits LaTeX. Tabloid paper (11 in × 17 in) and `\usepackage{multicol}` come from `manuscript/preamble.md`; column separation matches `src/newspaper/layout_spec.py` (`LAYOUT.column_sep_in`). Figure~\ref{fig:layout_schematic} summarizes the same numbers as a grid diagram.

```{=latex}
\begin{figure}[!ht]
\centering
\includegraphics[width=0.92\linewidth]{../output/figures/layout_schematic.png}
\caption{Not to scale schematic from NewspaperLayout: tabloid sheet, dashed box is text area inside margins, shaded regions are three body columns with gutters. Values align with preamble geometry and layout\_spec.py.}
\label{fig:layout_schematic}
\end{figure}
\par\smallskip
```

The masthead PNG is produced by `scripts/generate_masthead.py` calling `newspaper.masthead.render_masthead_png` during Stage 02 analysis. Optional environment variables `NEWSPAPER_TITLE` and `NEWSPAPER_TAGLINE` override banner text without editing Python. In the combined PDF it is captioned as Figure~\ref{fig:masthead}. A companion schematic ships from `scripts/generate_layout_schematic.py` via `render_layout_schematic_png`, giving a second captioned figure for float and caption testing.

**Stage ordering (core pipeline).** `execute_pipeline.py` and `./run.sh --core-only` run, among others: environment setup, tests, analysis scripts (including both figure generators when present), PDF rendering, validation, and output copy. Analysis writes into `projects/traditional_newspaper/output/`; copy stages mirror selected artifacts into `output/traditional_newspaper/` for distribution. Exact stage labels appear in console logs with progress markers.

**Manuscript combination.** Each slice file is read as UTF-8 text. Preamble metadata from `preamble.md` injects geometry and packages. Title page fields derive from `config.yaml` (`paper.title`, authors, version, date). Bibliography entries live in `references.bib`; `\cite{template2026gazette}` appears on the front page and here to exercise BibTeX wiring.

**Word counts.** `scripts/report_manuscript_stats.py` walks `all_tracked_manuscript_basenames()` and emits `output/data/manuscript_stats.json` with per-file words, lines, and bytes. CI or humans can diff that JSON across branches to catch accidental truncation. It is a thin orchestrator: no analytics logic beyond counting.

**Why tabloid.** The 11×17 inch choice stresses wide measure and long vertical flow compared to letter paper. Three columns mimic newspaper grids while remaining simple `multicol` environments—no custom column balancers. If you shrink paper, update `NewspaperLayout` constants, regenerate `layout_schematic.png`, and rerun tests that assert geometry text in captions still matches code.

**Floats inside multicols.** LaTeX floats interact oddly with `multicol` in some cases. This supplement places figures early in the slice; if you see drift, consider `[!ht]` tweaks or `strip` environments from wider LaTeX cookbooks—only after measuring warnings in `_combined_manuscript.log`.

**Slides and web.** The same stems feed Beamer slides and HTML web output via infrastructure renderers. Figure captions pass through Lua filters for HTML; keep `\caption{}` text free of unmatched braces so extraction regexes succeed.

This supplemental folio appears **after** the sixteen edition pages and **before** the glossary slice, per the template’s ordering: main numeric sections, then `S*`, then `98_*`, then `99_*` if present.

```{=latex}
\noindent For citation metadata see \cite{template2026gazette}.
\par\smallskip
```

```{=latex}
\end{multicols}
```
