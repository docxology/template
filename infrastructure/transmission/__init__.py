"""Transmission bookends and page-check modules for rendered release
bundles (LaTeX single-page envelopes, barcode strips, figure embedding).

Consumed by the publishing release workflow and the rendering Stage 04
page-check step; module references in ``docs/guides/publishing-guide.md``
are resolved on disk by the documentation module-reference guard, which
requires a regular package (``__init__.py``) rather than an implicit
namespace package.
"""

__all__ = [
    "transmission_barcode_strip",
    "transmission_bookends",
    "transmission_figure",
    "transmission_models",
    "transmission_page_check",
]
