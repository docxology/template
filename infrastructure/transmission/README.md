# infrastructure/transmission

Shared transmission-artifact machinery: BEGIN/END bookends written around
combined manuscripts, the publication-pairing diagram and barcode strip, the
bookend page-span check, and the underlying models.

## Why a separate package

Both the **rendering** layer (writes bookends around combined PDF/HTML
manuscripts) and the **publishing** layer (release workflow writes bookends
for release artifacts) operate on these artifacts. Housing the family in
publishing created a rendering -> publishing layering inversion; housing it
in rendering would have created the mirror-image publishing -> rendering
inversion. ``infrastructure/transmission`` is the shared leaf both layers
import (`RENDERING-LAYERING-1`).

## Coupling note

``transmission_bookends.build_transmission_context`` consumes publishing
release-metadata surfaces (zenodo_urls, metadata_from_config,
publication_ledger, release_pairing) — that transmission -> publishing edge is
a documented exception; it never flows rendering -> publishing. The
`tests/infra_tests/rendering/test_layering.py` guard enforces the
rendering-side prohibition.

## Modules

| Module | Role |
| --- | --- |
| `transmission_bookends.py` | BEGIN/END bookend markdown generation, enabled-check, context building. |
| `transmission_models.py` | `TransmissionContext` model. |
| `transmission_figure.py` | Publication-pairing figure writer. |
| `transmission_barcode_strip.py` | Transmission integrity barcode strip. |
| `transmission_page_check.py` | Bookend single-page-span validation. |

## Backwards compatibility

`infrastructure/publishing/transmission_*.py` remain as explicit re-export
shims so historical imports keep resolving; new code imports from
`infrastructure.transmission` directly.
