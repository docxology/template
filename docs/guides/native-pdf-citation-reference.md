# Independent scientific PDF citation references

Combined manuscript PDFs use the real Pandoc natbib writer and BibTeX
`plainnat` style. A citeproc HTML or Office label does not establish the PDF
label. The independent reference in
[native_pdf_citations.py](../../infrastructure/reporting/native_pdf_citations.py)
uses frozen original sources, the complete bibliography union, original
pre-citeproc Pandoc AST, typography configuration and extracted source preamble.
Manuscript-produced TeX, `.aux`, `.bbl` and PDF text are diagnostic material.

`observe_natbib_reference(root, directory, *, ast_bytes, sources,
bibliographies, config, preamble, crossref_keys, env, deadline, run_id,
artifact_id)` creates one fresh confined leaf below `output/readiness`.
Source, bibliography and configuration inputs are ordered `(relative_path,
bytes)` tuples. Preamble is an optional tuple. The PDF source worker must
independently reconstruct and bind the original AST and exact rendered source
inputs before calling this supplementary observer. An arbitrary caller-supplied
AST is insufficient release evidence.

Each original `Cite` retains its keys, mode, prefix and suffix. Actual Pandoc
maps these to narrative, parenthetical, author-suppressed and multi-citation
natbib commands. A bounded balanced parser also retains explicit `cite`,
`citep`, `citet`, `citealp`, `citealt`, `citeauthor`, `citeyear`, `citeyearpar`
and `citetext` commands, stars and optional notes. Literal code remains code.
Source-declared exact crossref keys are recorded separately. Mixed citation and
crossref groups, body macro/state changes, residual raw environments and
unrecognized citation commands retain blockers. Their scientific content
requires the separate full-source native projection.

The oracle renders all occurrences together against the complete cited set.
Actual BibTeX determines author/editor/corporate/key fallbacks, multiple-author
names, nonnumeric years and `a`/`b` suffixes. Expected names and years are never
guessed from a regex. Actual `nocite` source state is retained. Additional
bibliography styles and external/dynamic preamble inputs require a separately
admitted contract. Each process must really finish with original and effective
exit zero, without timeout, cleanup error or custody refusal.

[native_pdf_citation_runtime.py](../../infrastructure/reporting/native_pdf_citation_runtime.py)
runs a diagnostic discovery compilation and a fresh final compilation. Each
uses XeTeX with explicit `-fmt=xelatex`, BibTeX, two subsequent XeTeX passes and
the independent native PDF backend. TeX `.fls` inputs and successful
`xdvipdfmx --kpathsea-debug=4` file opens identify the actual styles, format,
configuration, maps and font files. Their bytes are retained before final
execution and checked afterward; a changed or expanded final dependency set
refuses acceptance. Original executable and consumed-input before/after
observations and actual process records are preserved.

[native_pdf_citation_replay.py](../../infrastructure/reporting/native_pdf_citation_replay.py)
regenerates the reference on the current reader from independently reconstructed
source inputs. It checks original actual tool outcomes and retained dependency
bytes, then compares reader-local style/font/dependency content identities.
Original producer paths are observations; replay never opens them. Receipt
hashes preserve local custody and do not authenticate remote execution.

`inspect_natbib_citations(pdf, rasters, reference, *, deadline)` checks ordered
non-whitespace native citation glyphs, glyph font sizes, crop bounds and
localized ink on complete actual 150-dpi PNG pages. It uses the existing native
PDF resource ceilings, minimum font size and visibility thresholds. It joins
a word-wrap hyphen only across observed line/page geometry and only when the
result exactly matches the independently rendered reference. Explicit source
punctuation remains required. Full prose placement, whitespace semantics,
footnote/table layout, crossrefs and mathematical obligations remain separate
mandatory source/native checks. This citation observation cannot establish
complete scientific PDF acceptance by itself or relax any root release gate.

The focused tests render actual references and a separate complete-source PDF,
then exercise valid changed, omitted, white-hidden and reordered native PDF
controls. Parser failures and nonzero tool exits cannot satisfy those semantic
negative controls. The disposable producer is removed before any reader checks.
A separate source-audited Python 3.14 interpreter then rebuilds the reference
from a transported request and the current reader's installed native tools.

```bash
uv run pytest tests/infra_tests/reporting/test_native_pdf_citations.py -q
```

Native tools must be installed in the selected test environment. Each test keeps
the existing 60-second component deadline. Child startup, execution and cleanup
consume the original deadline; a later step cannot extend it.

See [Testing and reproducibility](testing-and-reproducibility.md) for the
repository's complete required verification procedure.
