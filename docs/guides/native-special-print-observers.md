# Source-native special print observers

`native_storybook_source` reconstructs ordered page PNGs from `content/story.yaml`
and the candidate's source-owned scene/text renderer in a private directory.
Every source caption line is independently bounded before admission. The
independent artifact reader compares decoded RGB pixels, checks each print
PDF page's configured media/crop geometry, permits only the full-page image
program, and checks ordered embedded image pixels. It constructs the contact
sheet itself from the source page order and labels rather than trusting the
producer's summary or contact-sheet builder. Unknown source keys and duplicate
YAML fields refuse.

`native_newspaper_source` derives visible text obligations from the configured
edition and its ordered page YAML files. It regenerates confined, known source
image resources and a private source render. Independently parsed PDF glyphs
must include all required source phrases and retain exact glyph order, font,
size, color and geometry, with finite bounds inside configured pages. Actual
Poppler raster subprocesses compare every complete page's decoded pixels,
including image placement and opaque overpainting. The producer's layout audit
and `all_pages_fit` flag remain diagnostic. Unsupported item/inline/image forms
refuse rather than degrading to image placeholders.

These are bounded artifact oracles, **not standalone portable receipt admission**.
Their references must be constructed from admitted current source, never accepted
from an unauthenticated producer report. Font resource aliases may change during a PDF rewrite; dereferenced font program,
encoding, metrics and descriptor remain exact. Native v4 callers must additionally
admit original run/specification, subprocess exits, bootstrap/source/tool/
interpreter/library/font before-and-after identity and artifact closure.
Source renderers choose platform fonts; reconstruction under a different font
selection cannot establish an original cross-platform render. Original admitted
font/render observations or appropriately licensed identical source resources
are required before removing that portability blocker. No system font binary
is exported by these modules. Scientific and other unsupported obligations are
unchanged.

## Actual bounded controls

`test_native_special_print.py` launches independent oracle child processes over
legitimate two-page source fixtures, retaining command/stdout/stderr and original
exit code alongside actual altered PDF/PNG bytes. Baselines exit 0; altered,
omitted, reordered, hidden, clipped, geometry, font, image, font-resource, PDF/PNG transparency and contact-order
mutants exit 1. Storybook pixel mutants retain the ordinary image-only PDF
program, so decoded image readback is exercised beyond an operator allowlist.
Newspaper hidden/image mutations preserve parseable original glyphs and fail the
native raster comparison. Parser/tool failures are not substituted for an
intended artifact rejection.

Full current-source positive observations were also executed for the actual
14-page storybook PDF/contact sheet and the configured 12-page newspaper PDF
with 24 successful original Poppler readback subprocesses. These local proofs
do not represent authenticated hosted transfer or cross-host custody admission.
The initial grouped test's timeout is retained as development evidence; splitting
controls per child and allowing bounded font-cache initialization preserves
original execution failures without treating them as successful negatives.
