# Fresh native-format evidence

Run `uv run --no-sync --offline python scripts/gates/native_formats.py` after explicit environment
preparation. `--project templates/template_code_project` selects a diagnostic
subset; `--timeout` bounds admission, execution and observers together. Ordinary
execution stays in offline core mode. This command performs no publication.

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

These observations establish narrower native conformance. Full format acceptance
remains **blocked** for the remaining complete source-content/layout and visual controls,
including generic PDF, browser HTML, native DOCX/EPUB readers, projected slides,
pitch parity, newspaper print geometry and storybook localized pixel controls.
The producer can retain validated conformance while preserving exit 75 and the
missing full-acceptance obligations. A nonblank raster proves neither correct
scientific content nor readable typography. Receipts are auditable local evidence;
execution provenance still belongs to the supervised producer, and independent
review is required before a release claim.
