# Testing Philosophy

A layout engine has two kinds of correctness, and they need two kinds of test.

## 1. Logic — automated, deterministic

The pure modules (`geometry`, `config`, `content`, `typography`, `figures`) and
the render *contract* are covered by `pytest`:

- column arithmetic reconstructs the width exactly;
- strict loaders accept valid data and reject invalid data with the right
  message;
- `register_fonts` always returns usable names; the stylesheet defines every
  required style; headlines never split words;
- `generate_all` writes every figure as a valid PNG;
- the real edition renders to a valid PDF of **exactly 12 pages** at the correct
  trim with **no over-set page**, and a synthetic minimal edition exercises every
  template branch.

Coverage runs ~99% branch coverage as of the 2026-06-25 deep review (up from
~95% at 53 tests); the enforced gate (`fail_under` in `pyproject.toml`) is 90%.

## 2. Appearance — visual, mandatory

No assertion can tell you a page *looks* like a newspaper. So the development
loop — and the agent contract (`agent_instructions.md`) — requires rasterizing
the pages and looking at them after any layout change:

```bash
pdftoppm -png -r 100 output/pdf/the-triplicate.pdf /tmp/p   # then inspect each
```

This project was built that way: the italic-headline bug, the under-set
classifieds and the over-wide columns were all caught by *looking at the render*,
not by reading code. A green test suite is necessary but not sufficient; the eye
is the final gate.

## The over-set rule

`all_pages_fit == False` means a reader would lose copy. Treat it as a test
failure: the render report exists precisely so this can be asserted in CI.
