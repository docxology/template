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

The manual `platform-native-preflight.yml` diagnostic is bounded at 12000
seconds, still below the unchanged 14,400-second whole-operation budget. Two
hosted 900-second cold runs first measured an older bound below the lifecycle's
cost: 406-564 seconds elapsed before the supervised worker started, and neither
worker had a complete outcome when the clock expired. The 1,800-second bound is
likewise measured below the cost: the hosted required-acceptance native
inventory spent 10,264.8 seconds on its first exemplar without completing it, so
any bound below roughly 10,300 seconds ends before one exemplar can finish. The
preflight reserves 30 seconds at the launch boundary and 15 seconds at the
supervised-worker boundary so the inner owner can return, reap its worker and
retain process/cleanup/guardian receipts before the outer watcher ends. The
diagnostic remains incomplete, is not a release receipt, and never authorizes
publication. The release path's 14,400-second whole-operation budget is
unchanged.

Both native lanes run the strict rendered publication-evidence audit first
(`infrastructure.validation.cli publication-audit --rendered --strict
--require-figure-accessibility`) in the same submodule-initialized checkout, over
the scope the lane itself prepares: the preflight's representative exemplar
(`PREFLIGHT_SCOPE`) and the complete public roster for `--mode original`. The
supervised worker applies that predicate to its reference root before any stage
executes, so a stale or incomplete rendered receipt fails in seconds instead of
after the bounded native lifecycle. The gate adds no admission and skips or
weakens no native check; the lane still owns every native observation.

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

Original native stdout/stderr observations use
`template-native-tool-stream-observation-v1`: their absolute producer `path` is a
historical label, never an artifact edge or a reader-side filesystem nomination.
The ToolAPI wrapper separately binds the retained public stream bytes with exact
repository-relative `path`/`sha256`/`bytes` objects. Portable readback checks those
bytes against the versioned original hash, size, basename and decoded text after
the producer is gone. Strict closure still rejects absolute/traversal artifact
bindings and retains every wrapper, process and stream; neither transport nor
versioned observation DATA grants original execution custody.

Linux consuming-loader qualification uses an inherited read-only descriptor for
the exact held compiler output: `LD_AUDIT=/proc/self/fd/<fd>`. This avoids
[glibc's bounded audit-name buffer](https://github.com/bminor/glibc/blob/glibc-2.40/elf/dl-main.h),
which silently omits names of 255 bytes or more, including real nested stage
paths. Only the audited child inherits the descriptor; ordinary children and its
guardian do not. The v5 native process and loader lifecycle bind the descriptor
to the original compiler inode. Independent readback still requires complete
callbacks, mapped helper/body equality, the terminal roster and signed OS exit;
a short path, environment commitment or serialized descriptor alone grants no
acceptance. The descriptor closes with owned observation cleanup, without
changing the executable, compiler output, callbacks or existing clocks.

The finite PDF-text component compiles ordered content obligations from
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

## Complete Source-owned oracle requirements

The full boundary is the typed `NativeOracleSpecification` produced by
`compile_native_oracle_obligations`, not a static list saying controls are
unimplemented. It reconstructs the exact source/configuration, artifact roster,
diagram occurrences, whole control suites and required witness axes from held
Source. The strict reader requires equality with that freshly compiled graph.
The specification deliberately has no pass, fulfilled or release-authority field.

| Applicable Source artifacts | Required control families |
| --- | --- |
| Every selected PDF | `pdf`, including the declared complete scientific-source/control/replay obligation |
| Browser HTML | `html` and `html_semantic` |
| DOCX | `docx`, `docx_scientific`, and `docx_diagrams` when Source contains diagrams |
| EPUB | `epub`, `epub_scientific`, and `epub_diagrams` when Source contains diagrams |
| Manuscript slides and Reveal companions | `projection`, `pptx`, `manuscript_slides`, with the declared Reveal-specific obligations |
| Pitch short/medium/long PDF and PPTX companions | `projection`, `pptx`, `configured_pitch`; all three pairs are mandatory |
| Configured newspaper editions and storybook pages/contact sheet | `configured_print` over the complete Source-selected roster |

Original analysis/domain/hydration-to-consumed-byte lineage and portable replay
remain explicit requirements. A matching package readback, narrow text/raster
component, observed adapter status or decoded receipt cannot discharge the full
graph. Actual positive originals, every complete selected control suite, all
source-survival/layout/visual witnesses and independent Current readback must
satisfy their source-owned predicates. Unknown roles, missing axes, failed
controls, custody refusals and unsupported projections remain failures or
blockers; they cannot disappear through status adaptation.

This guide describes the contract, not the qualification of a particular run.
Release acceptance remains pending until the exact Source has genuine complete
workflow evidence and independently admitted reader custody. No existing receipt
is rewritten or promoted by this guidance.

## Next steps

Use the existing [Release boundary](../maintenance/release-boundary.md) for root
promotion through exact-revision acceptance, hosted handoff, tag/release and
retrieved-asset verification. Standalone project publishing follows the
[Publication runbook](publication-runbook.md); its versions and provider outcomes
remain separate from root acceptance.
