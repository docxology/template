# Supplement: Typography and measure

```{=latex}
\begin{multicols}{3}
```

**Body copy and column measure.** This exemplar sets a nine-point body in the `NewspaperLayout` dataclass (`body_font_pt`) for documentation parity; the default Pandoc LaTeX template may map point sizes differently unless you extend the template. Measure—the line length inside a column—interacts with hyphenation and justification. Narrow columns tolerate fewer characters per line, increasing hyphenation frequency and rag texture.

**Font choices.** XeLaTeX via `fontspec` can load system serif faces for a newsroom feel. Changing fonts requires editing the template or preamble, then visual-regression review. Keep ASCII-heavy test manuscripts when debugging font issues so failures isolate typography from Unicode edge cases.

**Rivers and ladders.** Typographers watch for vertical gaps aligning across lines (“rivers”) and repeated word stacks (“ladders”). Automated detectors exist; human proofreaders still catch context-specific ugliness. Multicolumn setting amplifies rivers because adjacent columns create vertical rhythm interactions.

**Hyphenation patterns.** TeX loads language-specific hyphenation tables. Set `babel` or `polyglossia` languages if you mix locales in one edition. Wrong languages yield bad breaks and can confuse spellcheck-adjacent tools.

**Widows and orphans.** Publishing style guides limit single lines stranded at column tops or bottoms. `\clubpenalty` and `\widowpenalty` tweaks live in advanced LaTeX tuning; this project leaves defaults to keep the preamble small.

**Small caps and section rails.** `newspaper.snippets.section_label` emits `\textsc{}` labels suitable for department markers. Pair with `rule_line()` for classic newspaper chrome. Escape user-supplied strings—snippets already guard LaTeX specials.

**Quotes and dashes.** Curly quotes via Unicode in markdown pass through Pandoc. Em dashes versus en dashes follow house style; consistency beats personal taste when collaborating. ASCII-only sources simplify diffs but feel cold—pick consciously.

**Figures and captions.** Caption text should explain what a non-expert sees, not repeat the title. Autonumbering via `\caption` supplies “Figure 1,” “Figure 2,” etc. Cross-reference with `Figure~\ref{fig:key}` to avoid bad breaks before numbers.

**Print versus screen.** PDFs for print need bleed and color profiles if sent to commercial presses; screen PDFs skip bleed. This template targets on-screen proofing and office printers; prepress engineers should extend geometry accordingly.

**Accessibility.** Tagged PDF improves screen-reader navigation. Adding structure requires LaTeX packages and discipline about heading levels. Web HTML may remain the more accessible surface for some audiences—render both when possible.

**Maintenance.** When bumping TeX Live, re-run the full project pipeline and spot-check hyphenation changes in the longest slices (`02`–`04` national/world/business depth sections). Typography regressions are subtle; diffing PDFs is noisy—prefer targeted visual review.

**Longer read: rhythm and grid.** Newspaper typography historically paired condensed headlines with generous body leading in competing publications; the tension between density and legibility never resolves universally. Digital interfaces borrowed print metaphors—cards, columns, rails—while adding infinite scroll and responsive breakpoints. This PDF chooses a fixed page size to make regression tangible: the same text either fits or overflows, and engineers see the failure immediately rather than hiding it behind CSS `overflow:auto`.

**Tables and numerals.** Tabular figures align currency and counts on baselines when fonts supply true lining numerals. Old-style figures in prose look elegant but jar in tables. If you introduce financial tables to this edition, select a font with both sets or enable `fontspec` OpenType features explicitly. Markdown pipe tables through Pandoc may require `booktabs` and `siunitx` for publication polish—test with a minimal example before scaling.

**Drop caps and ornaments.** Feature sections sometimes open with a dropped initial letter. Implementing drop caps in LaTeX is package-specific (`lettrine`). They interact badly with `multicols` unless opening paragraphs span full width; plan a single-column intro or accept simplified styling.

**Kerning pairs.** Professional fonts include kerning tables; TeX applies them automatically. Custom logos in mastheads drawn with matplotlib bypass TeX kerning—acceptable for raster nameplates, less so for body text. Keep matplotlib for figures, TeX for paragraphs.

**Line breaking in URLs.** Long bare URLs in monospace overflow columns. Use `\url` from `hyperref` or `\path` with breakable hints. Pandoc may wrap differently than raw LaTeX—validate both PDF and HTML when URLs appear in footnotes or references.

**Character encoding.** UTF-8 source files allow curly quotes and emojis; not every LaTeX font includes emoji glyphs. Restrict symbols to what your font supports or fall back to graphic inclusion for rare characters.

**Print color.** Black-only printing ignores RGB figures unless converted. Masthead and schematic use neutral grays and black lines to survive grayscale rip tests. Adding color charts requires CMYK thought and ink limits for commercial print.

**Baseline grid purism.** Some designers snap baselines to a fixed grid across spreads. LaTeX plus `multicol` does not enforce strict baseline grids without heavy customization. Accept minor drift or invest in ConTeXt-level tooling if your art director demands pixel-perfect alignment.

**Readability metrics.** Automated scores like Flesch–Kincaid mislead for technical writing. Use them cautiously on supplements aimed at broad audiences; ignore them for glossary definitions where precision beats simplicity.

**Closing.** Typography is constraint satisfaction under taste. This supplement records constraints (`LAYOUT`, preamble packages) so taste can iterate without losing reproducibility.

```{=latex}
\end{multicols}
```
