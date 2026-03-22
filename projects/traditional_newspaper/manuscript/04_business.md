# Business

```{=latex}
\begin{multicols}{3}
```

**Markets desk**

**NEW YORK.** `04_business` carries the markets voice for this exemplar. Equity indices, yields, and currency pairs below are **not** streamed from exchanges. They stand in for how financial tables and dense numerals behave in narrow columns next to prose.

Traders quoted opening levels for a benchmark index described only as “the broad market.” Bond desks flagged a modest curve steepening narrative without attaching basis-point tables; adding a `tabular` environment in raw LaTeX would be the next step for true table stress. Commodity paragraphs mention energy and grains in passing.

Corporate reporters summarized earnings season etiquette: guidance, one-time charges, and adjusted metrics. Footnotes could disambiguate GAAP versus non-GAAP figures; this edition keeps a single narrative stream to simplify markdown validation. When you promote real data, generate tables from `projects/traditional_newspaper/src/` helpers and snapshot them for tests.

Mergers-and-acquisitions bankers mused about regulatory timing. Antitrust lawyers declined to comment, as they are fictional. The business point for the template is that italic tickers and parenthetical percentages compile cleanly when escaped properly; raw LaTeX blocks remain the escape hatch.

Small-business columnists advocated for predictable credit lines. Local angles tie forward to `11_local.md` conceptually. Inventory financing, seasonal hiring, and supplier terms get a sentence each to pad measure without repeating national copy.

Technology vendors placed enterprise software upgrades in the context of IT budgets. That bridges toward `05_technology.md` without embedding hyperlinks that might break HTML export rules. Cross-format consistency is a pipeline feature, not a single renderer trick.

A final markets wrap reiterated risk disclosures: past performance does not predict future results. The same disclaimer applies to template PDFs: a green build today does not guarantee fonts will remain available after OS upgrades. Pin TeX Live versions in documentation when teams care about pixel-identical output.

**Depth notes.** Corporate debt covenants trigger maintenance tests on leverage ratios. Restructuring advisors model recovery rates across capital structure layers. None of that math ships in this markdown; if you add equations, use Pandoc math delimiters and validate labels.

Retail investors face order-routing incentives and payment-for-order-flow debates. Regulators weigh transparency against execution quality. Business pages sometimes explain mechanics with diagrams; the template’s second figure is geometric, not financial.

Commercial real estate cap rates compress when risk-free yields move. Developers underwrite projects with sensitivity tables. Tables in LaTeX need `booktabs` for many style guides; check whether your preamble loads them before shipping investor-facing PDFs.

Labor markets tie wage growth to productivity and demographics. Immigration policy shifts the supply curve for skills. Opinion folios argue values; business folios cite payrolls. Keep the separation crisp so readers know which slices carry byline accountability.

ESG ratings disagree across providers; greenwashing accusations follow. Sustainability-linked bonds tie coupons to KPIs. Disclosures appear in footnotes in real filings; this manuscript uses inline prose to avoid `}`-heavy footnote machinery until needed.

Insurance markets diversify catastrophe risk through reinsurance and cat bonds. Climate change shifts loss distributions. Actuaries model tail risk; PDF pipelines model missing figure paths. Both professions log assumptions.

International tax reform discussions cover pillar one and pillar two frameworks. Transfer pricing documentation fills cabinets. Template documentation fills `docs/`; keep business commentary here aligned with what legal approves externally.

**Closing.** `04_business` sits mid-edition. It should feel numerate even without tables. Technology coverage continues next with stack-specific prose.

```{=latex}
\end{multicols}
```
