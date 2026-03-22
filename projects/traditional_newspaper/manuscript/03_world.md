# World

```{=latex}
\begin{multicols}{3}
```

**Correspondents and clocks**

```{=latex}
\noindent\textit{Geneva — composite string date}\par\smallskip
```

**WORLD.** Stem `03_world` follows `02_national` in the canonical ordering enforced by `manuscript_stems_ordered()`. Foreign copy often mixes diacritics, place names, and institution strings that challenge hyphenation dictionaries; this stub keeps ASCII for CI predictability while leaving hooks for Unicode later.

Diplomats described a routine session on shipping lanes without citing live AIS feeds. Maritime law citations would normally appear in footnotes; Pandoc and BibTeX handle those when `references.bib` keys match `\cite{}` invocations. Here the narrative stays self-contained so a failed bibliography pass still leaves readable body text.

Humanitarian coordinators outlined contingency thresholds for relief convoys. Numbers are round and fictional. The reproducible-build story is that the same markdown, preamble, and fonts yield the same PDF on the same TeX tree—timezone stamps on the cover page aside, which come from `\today` unless overridden in `config.yaml`.

Climate envoys restated long-term mitigation targets. A pull quote could be injected with `snippets.pull_quote` inside a raw LaTeX block if you want a centered italic rail between paragraphs. This file demonstrates ordinary paragraph flow instead, so the difference shows up when you diff manuscripts.

Regional editors summarized elections in unnamed capitals. Transition teams pledged continuity; opposition parties demanded audits. None of it hits an API. The lesson for template users is that **wire copy** can be swapped in file-by-file without touching infrastructure, provided paths and encodings stay valid.

Sports-adjacent diplomacy—hosting rights, visa rules for athletes—filled a short column inch. Multicolumn balance sometimes leaves a widow; LaTeX and `multicol` mitigate that better when paragraphs differ in length. That is why these slices vary slightly in structure rather than repeating one paragraph sixteen times.

Science attachés noted cooperation on Arctic monitoring. Cross-links to `14_science.md` are conceptual, not `\ref{}` based, because section labels across slices are a project policy choice. If you need literal “continued on page” jumps, encode them as static strings.

A closing paragraph references time zones only to remind builders that scheduled pipelines should set `TZ` explicitly on servers if log ordering matters. The manuscript itself remains timezone-agnostic text. World service ends here; business follows on the next folio.

**Depth notes.** Treaty depositaries track ratifications and entry-into-force dates. Legal editors distinguish reservations from interpretive declarations. World copy in real papers links to primary treaty texts; this stub stays generic so translators can swap languages without touching LaTeX escapes.

Sanctions programs layer primary restrictions, sectoral bans, and secondary pressure on third-country banks. Compliance teams screen entities against consolidated lists. The template screens markdown for broken image paths. Both activities are tedious and both prevent expensive mistakes.

Refugee law discussions hinge on non-refoulement, safe third countries, and durable solutions. Journalists cover displacement humanely by foregrounding voices; this file foregrounds column gutters instead. If you publish interviews, store consent metadata outside the manuscript or in a secured annex.

Central banks overseas react to Fed signals, commodity shocks, and domestic inflation targets. Currency desks watch carry trades and swap lines. Numeric tables would stress decimal alignment; paragraph mode is the current choice until someone contributes a validated table package setup for this project.

Cultural heritage disputes—repatriation of artifacts, digital scans versus physical return—appear in foreign sections when governments negotiate. Museums increasingly publish CC-licensed images; newspapers must still respect separate publicity rights for people photographed beside objects.

Science diplomacy pairs joint publications with summit photo ops. Fusion experiments and vaccine trials both benefit from shared protocols. `14_science.md` continues the thread; this world folio only sets the geopolitical stage in outline.

Maritime boundary cases blend UNCLOS articles with historic bay claims. Cartographers argue over baselines; editors argue over map captions. Figure captions here use simple sentences without nested braces to keep HTML conversion predictable.

World wraps again: string ordering in `discover_manuscript_files` is lexicographic within buckets. `03_world` always precedes `04_business` because `03` sorts before `04`. Renaming stems breaks that contract—update `PAGE_SLICES` and every test that asserts order.

```{=latex}
\end{multicols}
```
