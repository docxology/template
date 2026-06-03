# Test Patterns

- **Real-edition integration:** load `../content/` and render to `tmp_path`;
  assert `%PDF-` header, 12 pages (token count *and* `RenderResult.page_count`),
  792×1224 trim, and `all_pages_fit`.
- **Synthetic minimal edition:** hand-build a 2-page `Edition` exercising every
  template (`front` with rail/lead/figure/drop-cap/pull-quote, `classified` with
  `generic` + `display` boxes) so branch coverage doesn't depend on the shipped
  content.
- **Strict-loader errors:** assert on substrings of the error message (the bad
  value and "allowed"), matching the documented contract.
- **Degradation:** a missing image path must render (placeholder), not raise.
- **No `output/` writes:** always use `tmp_path`.
