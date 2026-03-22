# Front Page

```{=latex}
\begin{figure}[!t]
\centering
\includegraphics[width=\linewidth]{../output/figures/masthead.png}
\caption{Deterministic nameplate raster from render\_masthead\_png, built during pipeline analysis. Override title and tagline with environment variables NEWSPAPER\_TITLE and NEWSPAPER\_TAGLINE. Outputs to masthead.png in project output figures.}
\label{fig:masthead}
\end{figure}
\vspace{0.6em}
\begin{multicols}{3}
```

**Late edition** — Lead item for the Template Gazette demonstration edition.

```{=latex}
\noindent Citation hook: \cite{template2026gazette}.
\par\smallskip
```

```{=latex}
\noindent\textbf{\Large Pipeline declares print deadline}\par\smallskip
\textit{By Staff — City Desk}\par\smallskip
```

**CITY.** The research template treats this folio as `01_front_page` in `PAGE_SLICES`: the first body slice after title front matter, carrying the edition nameplate and the opening multicolumn jump. Nothing here is wired to a live CMS; paragraphs are static so PDF, HTML, and slide exports stay bitwise reproducible when seeds and inputs are fixed.

Readers should treat quotations and attributions as **layout fixtures**, not reporting. The point is to stress hyphenation, column breaks, and float placement (for example the captioned masthead above) across XeLaTeX runs. When you change paper size or `\columnsep` in `preamble.md`, this page should reflow without hand-tweaking each paragraph.

**Continued on folio with national briefs.** The sixteen core markdown files map one-to-one to edition pages in the combined document. `discover_manuscript_files` sorts numeric stems, then supplemental `S*` files, then `98_*` glossary material. That ordering is intentional: the glossary must not insert itself between “news” slices during pagination tests.

A secondary headline block can be ordinary Markdown bold, or raw LaTeX from `newspaper.snippets` if you need small caps labels or rule lines. This exemplar keeps most body copy in Markdown so Pandoc’s writer path stays exercised.

The pipeline copies deliverables from `projects/traditional_newspaper/output/` into `output/traditional_newspaper/` after validation. If a figure path breaks, the combined build logs the missing asset but the lesson is the same: relative `\includegraphics` paths are resolved from the interim PDF directory, so `../output/figures/` remains the stable spelling from manuscript files.

Editors reviewing the PDF should skim captions and glossary rows for terminology; implementers should read `S01_layout_and_pipeline.md` and the optional `S02` / `S03` supplements for geometry, validation, and output surfaces.

**Jump page notes.** Above-the-fold hierarchy in print is a spatial puzzle: nameplate, lead headline, dominant art, then secondary heads. This PDF stacks the masthead float, a LaTeX headline block, and Markdown bold deks. Web renditions may reflow that hierarchy with CSS grid; parity across formats is aspirational, not guaranteed without extra stylesheet work.

Datelines traditionally carry city names in caps with a long dash. Wire services standardized the glyph; Unicode offers em dash alternatives. Pick one house style and encode it consistently in markdown sources to avoid mixed punctuation in archives.

Running heads and folios differ by publication; academic articles use different headers than newspapers. The combined manuscript template injects title metadata from `config.yaml`; section-specific running heads would require LaTeX fancyhdr configuration beyond this exemplar.

Advertising adjacency rules—brand safety—matter for commercial papers. This build has no ads, so news-adjacent layout conflicts do not appear. If you add display ads, reserve figure floats or static boxes in the preamble.

Syndication and licensing of front-page designs themselves are rare, but typeface licenses are not. Confirm you have rights to embed fonts in PDFs you redistribute. XeLaTeX fontspec calls pull system fonts unless you bundle OTF files.

Emergency banners (“extra” editions) would override normal grids. Template users could toggle a YAML flag in future work to prepend a raw LaTeX alert box—out of scope today.

The front page closes; national news continues on `02_national.md` without a literal “see page” pointer because PDF page numbers depend on build.

```{=latex}
\end{multicols}
```
