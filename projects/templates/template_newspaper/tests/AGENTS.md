# AGENTS — tests/

- Add a test with every engine change. Logic gets a unit test; layout changes
  also get a **visual** render check (rasterize and look).
- Integration tests render the *real* edition from `../content/` — keep them
  asserting page count (12), trim, and `all_pages_fit`.
- Use `tmp_path` for any written PDF/figure; never write into `../output/`.
- Keep the suite fast (< a few seconds) and deterministic.
