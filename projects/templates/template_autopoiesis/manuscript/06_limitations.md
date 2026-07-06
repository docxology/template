## Limitations

### Reserved slots are excluded from the effective product space

The {{RESERVED_SLOT_COUNT}} reserved slots (`{{RESERVED_SLOT_NAMES}}`) are
present in the grammar for structural reasons but do not contribute to the
effective product size.  Their options are not currently consumed by the
materialization logic, so the true combinatoric space is
{{EFFECTIVE_PRODUCT_SIZE}} cells, not {{PRODUCT_SIZE}}.

### No child-PDF rendering in CI

Generated children write manuscript stubs but do not run Pandoc/Chrome
rendering within CI.  The `render_child_manuscript()` function returns a
`{"success": False, "reason": "..."}` dict unless a full rendering toolchain
is available.

### Within-platform guarantee only

The determinism guarantee holds within a single Python version and platform.

### Grammar does not self-modify

The autopoiesis metaphor is figurative — the grammar does not rewrite itself
based on generated children.  Self-referential modification is out of scope
for this exemplar.
