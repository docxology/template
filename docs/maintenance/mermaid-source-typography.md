# Mermaid typography in template/

The Source-pinned Mermaid11.16.0 renderer declares **Template Liberation Sans** as its default diagram family. It uses the packaged, unchanged Liberation2.1.5 regular, bold, italic and bold-italic bodies under their included SIL Open Font License. This intentionally changes the previous system-dependent Trebuchet/Arial/Verdana default. Diagrams should be regenerated when adopting this release; the PNG cache binds the rendering policy and exact font inputs.

The renderer constructs fonts from whole ArrayBuffers, waits for their load before Mermaid lays out the diagram, and records consumed-buffer hashes. The original and independent Source reader use this same declared profile and independently admitted Source bytes. Standalone SVGs include the exact fonts actually used from this cohort and the complete OFL notice. This is template-owned embedding; CLI11's separate fontEmbed API remains unavailable.

Explicit Mermaid directives, frontmatter theme variables and authored font CSS continue to take precedence. For example, an explicit `themeVariables.fontFamily` remains an override. Other selected platform faces still require independent physical nominations in native acceptance. The bundled default does not replace unrelated web, document or project typography.

Changing typography requires full canonical output renewal and exact original/fresh native acceptance. Source buffer and body observations do not establish Chrome glyph-ID or shaping-provider equivalence, complete glyph/effect ink, document placement or loaded-provider/cache custody. Existing release gates and original clocks, retained-byte limits, pixel allocations and storage reserve apply unchanged.
