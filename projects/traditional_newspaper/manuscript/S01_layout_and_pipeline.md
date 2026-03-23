# Supplement: Layout and pipeline

```{=latex}
\begin{figure}[!ht]
\centering
\includegraphics[width=\linewidth]{../output/figures/section_banner_S01_layout_and_pipeline.png}
\caption{Supplement banner marking the layout-and-pipeline desk; monochrome PNG from \texttt{generate\_section\_banners.py}.}
\label{fig:banner_S01_layout_and_pipeline}
\end{figure}
\begin{figure}[!ht]
\centering
\includegraphics[width=0.92\linewidth]{../output/figures/layout_schematic.png}
\caption{Not to scale schematic from NewspaperLayout: tabloid sheet, dashed box is text area inside margins, shaded regions are three body columns with gutters. Values align with preamble geometry and layout\_spec.py.}
\label{fig:layout_schematic}
\end{figure}
\begin{multicols}{3}
```

**How this PDF is built.** Sixteen markdown slices under `projects/traditional_newspaper/manuscript/` are discovered by `infrastructure.rendering.manuscript_discovery.discover_manuscript_files`, combined in stem order, and separated by `\newpage` inside `infrastructure.rendering.pdf_renderer.PDFRenderer` before Pandoc emits LaTeX. Tabloid paper (11 in × 17 in) and `\usepackage{multicol}` come from `manuscript/preamble.md`; column separation matches `src/newspaper/layout_spec.py` (`LAYOUT.column_sep_in`). Figure~\ref{fig:layout_schematic} (above this column block) summarizes the same numbers as a grid diagram.

The masthead PNG is produced by `scripts/generate_masthead.py` calling `newspaper.masthead.render_masthead_png` during Stage 02 analysis. Optional environment variables `NEWSPAPER_TITLE` and `NEWSPAPER_TAGLINE` override banner text without editing Python. In the combined PDF it is captioned as Figure~\ref{fig:masthead}. A companion schematic ships from `scripts/generate_layout_schematic.py` via `render_layout_schematic_png`, giving a second captioned figure for float and caption testing.

**Stage ordering (core pipeline).** `execute_pipeline.py` and `./run.sh --core-only` run, among others: environment setup, tests, analysis scripts (including both figure generators when present), PDF rendering, validation, and output copy. Analysis writes into `projects/traditional_newspaper/output/`; copy stages mirror selected artifacts into `output/traditional_newspaper/` for distribution. Exact stage labels appear in console logs with progress markers.

**Manuscript combination.** Each slice file is read as UTF-8 text. Preamble metadata from `preamble.md` injects geometry and packages. Title page fields derive from `config.yaml` (`paper.title`, authors, version, date). Bibliography entries live in `references.bib`; `\cite{template2026gazette}` appears on the front page and here to exercise BibTeX wiring.

**Word counts.** `scripts/report_manuscript_stats.py` walks `all_tracked_manuscript_basenames()` and emits `output/data/manuscript_stats.json` with per-file words, lines, and bytes. CI or humans can diff that JSON across branches to catch accidental truncation. It is a thin orchestrator: no analytics logic beyond counting.

**Why tabloid.** The 11×17 inch choice stresses wide measure and long vertical flow compared to letter paper. Three columns mimic newspaper grids while remaining simple `multicol` environments—no custom column balancers. If you shrink paper, update `NewspaperLayout` constants, regenerate `layout_schematic.png`, and rerun tests that assert geometry text in captions still matches code.

**Floats versus multicol.** Standard `figure` floats are not supported inside `multicols`; the layout schematic therefore sits before `\begin{multicols}{3}` in this slice, matching the front page pattern (masthead float, then three-column body). Use `\includegraphics` without a float if you ever need art mid-column.

**Slides and web.** The same stems feed Beamer slides and HTML web output via infrastructure renderers. Figure captions pass through Lua filters for HTML; keep `\caption{}` text free of unmatched braces so extraction regexes succeed.

**Checkpointing and resume.** Root pipeline scripts support checkpoints so long builds can restart after transient failures. Newspaper builds are shorter than some monographs, but CI timeouts still happen—resume flags save compute. Read `docs/operational/config/checkpoint-resume.md` for semantics; behavior is uniform across projects.

**Multi-project runs.** `./run.sh --all-projects` executes many exemplars sequentially. Infrastructure tests may run once up front. When debugging `traditional_newspaper` alone, pass `--project traditional_newspaper` to avoid unrelated failures blocking iteration.

**Environment variables.** Beyond masthead overrides, `LOG_LEVEL` tunes verbosity, `MPLBACKEND=Agg` ensures headless matplotlib, and `PROJECT_DIR` helps scripts resolve paths when invoked from unexpected working directories. Document any new vars in `scripts/AGENTS.md`.

**BibTeX keys.** `template2026gazette` in `references.bib` exists to exercise citation machinery. Replace with your publication entry when forking; keep keys ASCII and stable so diffs stay readable.

**Figure path normalization.** `_pdf_tex_transforms.fix_figure_paths` rewrites `../output/figures/` to `../figures/` relative to the compile directory inside `output/.../pdf/`. If you add figures, place PNGs under `projects/traditional_newspaper/output/figures/` before copy, or under final `output/traditional_newspaper/figures/` after pipeline—know which stage consumes which path.

**Extending slice count.** If you truly need seventeen core folios, you must edit `PAGE_SLICES`, rename files, and update every test asserting `16`. Prefer supplemental `S*` files for extra prose—it avoids renumbering tourism.

**Teaching use.** Instructors can assign students to modify one slice, regenerate PDFs, and explain diff in log output. The constrained structure makes grading objective: does inventory pass? do captions resolve? do tests stay green?

**Handover checklist (extended).** Before merging a layout change, capture: (1) `git diff` on `preamble.md` and `layout_spec.py`, (2) regenerated `layout_schematic.png` if constants moved, (3) `manuscript_stats.json` after `report_manuscript_stats.py`, (4) PDF validator output excerpt showing zero `??` references, (5) a one-line note in the PR describing float behavior on the front page. Reviewers use the checklist to avoid approving partial state where code and figures disagree.

This supplemental folio appears **after** the sixteen edition pages and **before** the glossary slice, per the template’s ordering: main numeric sections, then `S*`, then `98_*`, then `99_*` if present.

```{=latex}
\noindent For citation metadata see \cite{template2026gazette}.
\par\smallskip
```

```{=latex}
\end{multicols}
```
