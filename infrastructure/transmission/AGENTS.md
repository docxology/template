# infrastructure/transmission — agent contract

Shared transmission-artifact machinery used by both the rendering layer
(bookends around combined manuscripts) and the publishing layer (release
workflow bookends). Extracted from `infrastructure/publishing/` by
`RENDERING-LAYERING-1` to remove the rendering -> publishing inversion.

## Invariants

1. `infrastructure/publishing/transmission_*.py` shims re-export this
   package's surface; old import paths keep resolving. New code imports
   `infrastructure.transmission.<module>`.
2. `tests/infra_tests/rendering/test_layering.py` fails if any
   `infrastructure/rendering` module imports `infrastructure.publishing` or
   `infrastructure.reporting`.
3. The documented transmission -> publishing edge in
   `transmission_bookends.build_transmission_context` (release metadata) is
   the accepted coupling; do not add new publishing imports to the family
   without updating the README coupling note.

## Public surface

`write_transmission_bookends`, `transmission_bookends_enabled`,
`BEGIN_FILENAME`, `END_FILENAME`, `TransmissionContext`,
`write_transmission_diagram`, `write_transmission_barcode_strip`,
`validate_transmission_bookend_pages` (see `README.md` module table).

## Cross-refs

- `infrastructure/publishing/AGENTS.md` and `infrastructure/rendering/AGENTS.md`
  — the two consumer layers.
- `tests/infra_tests/rendering/test_layering.py` — the layering guard.
