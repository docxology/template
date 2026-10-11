# Fresh native-format evidence

Native acceptance requires an explicitly admitted installed SDK and independently
prepared runtime, tools and providers. Follow the source-owned
[required acceptance workflow](../../.github/workflows/platform-required-acceptance.yml):
`native-original` uses `infrastructure.reporting.native_installed_launcher
--mode original`; `complete` supplies a separate installed reader with the actual
original source, process and artifact context.

The [installed-wheel guide](../development/installed-wheel-matrix.md#separate-rendering-and-native-format-evidence)
lists every required launcher and lower-level producer flag, including exact SDK
implementation/hash, host, Mermaid and PDFium selections, provider wheels, fonts
and paired EPUB inputs. A bare checkout `scripts/gates/native_formats.py`
invocation cannot supply that admission context. Preparation is separate from
execution, which remains offline core mode and performs no publication. The
lower-level `--project templates/template_code_project` selection is diagnostic;
`--timeout` retains the admission, execution and observer budget.

The producer executes the complete current core plan with cleanup and shared
infrastructure tests explicitly omitted. Cleanup omission preserves frozen
publication inputs; the root infrastructure acceptance gate owns shared tests.
Resume and incremental reuse are disabled. Canonical analysis, rendering and
validation targets must execute in order, with every selected stage freshly
succeeded. Missing tools are blocked; actual failures and timeouts remain failed.

POSIX main-thread admission and finalization use the original real-time deadline;
the deadline exception bypasses ordinary observer error capture. Unsupported
thread/platform callers or an active caller-owned real-time timer remain blocked.
Prior signal state is restored. Post-launch evidence-write failures retain the
actual attempts in memory with exit precedence 130, 124, then 1; they cannot
become invocation exit 2. Private evidence leaves are created with held no-follow
directory descriptors and permissions 0700.

Pure public source/configuration/lock identity is frozen independently of mutable
deliverables. After regeneration settles, a separate final readiness fingerprint
binds stable deliverables. The producer emits a fresh partial receipt below
`output/readiness/`; it does not merge or rebind existing acceptance records.
Other required lanes remain unknown until their own producers supply evidence.

The versioned native execution record binds the actual installed interpreter,
worker process, complete plan and child attempts, exact source-owned artifacts,
native byte observations, tool executable bytes, version probes and real parser
and malformed-PDF negative controls. Every PDF page is freshly rasterized at
150 dpi and inspected for valid dimensions and nonuniform pixels. Raster and
font tools consume a private copy of the exact admitted PDF bytes; their command
receipts bind that input. The strict reader reconstructs all manuscript sections,
slide/reveal pairs and pitch-deck short/medium/long PDF/PPTX variants from source.
Inventory-only `validated: true` records cannot pass.

The v2 native execution record also compiles ordered content obligations from
the frozen, currently validated consumed manuscript bytes. Its deliberately
limited projection supports plain paragraphs, ATX headings and plain list items.
Unicode NFC, whitespace boundaries and named presentation ligatures are its
only text normalizations; numeric values, signs, units, punctuation and duplicate
occurrences remain significant. Math, citations, other markup and deck/print/book
projections remain explicit blockers. A zero supported-text collection is blocked.
The reader reconstructs the source hashes, order and policy rather than accepting
producer-supplied text obligations.

For supported PDF text, independent pdfplumber glyph observations must find each
token sequence in order. Mapped glyphs must remain inside the crop box and use at
least 9-point type. Their localized word regions in the actual 150-dpi raster
must contain visible ink under the versioned pixel policy. Rotated pages and
nonzero page origins remain unsupported geometry. Actual parser/library versions,
PDF/raster bytes, source contract and policy digests bind these narrower checks.
The strict reader reparses the PDF and recomputes the observations from admitted
pixels. This does not establish full scientific projection, heading placement,
figure fidelity, complete glyph visibility or typography quality.

Every PDF attempt requires a supervised valid-PDF positive baseline followed by
four actual valid mutants: changed numeric text, clipped text, tiny body type and
an opaque overlay over required text. A control counts only when parsing and real
raster/font tools succeed and the intended semantic, geometry or localized pixel
diagnostic appears with its original exit code. A setup exception, launch refusal,
timeout, forged observation or missing baseline cannot substitute for that result.

These observations establish narrower native conformance. The source-owned
`unsupported_native_controls()` declaration currently reports missing full-oracle
obligations for PDF, browser HTML, native DOCX/EPUB readers, projected slides,
pitch parity, newspaper print geometry and storybook localized pixel controls.
Full format acceptance remains **blocked** for those applicable declarations.
The full validator requires the original passing execution, no remaining blockers
and every required oracle; narrower conformance cannot satisfy that boundary.

Current release acceptance remains pending implementation and actual observation
of those required controls, followed by independent readback with the held live
reader operation. Receipt decoding cannot create that operation. The producer
retains validated conformance separately from exit 75 and missing full obligations;
actual failures and custody refusals remain failures. A nonblank raster proves
neither correct scientific content nor readable typography. Execution provenance
belongs to the supervised producer; independent review is required before a
release claim. No existing receipt is rewritten or promoted by this guidance.

## Next steps

Use the existing [Release boundary](../maintenance/release-boundary.md) for root
promotion through exact-revision acceptance, hosted handoff, tag/release and
retrieved-asset verification. Standalone project publishing follows the
[Publication runbook](publication-runbook.md); its versions and provider outcomes
remain separate from root acceptance.
