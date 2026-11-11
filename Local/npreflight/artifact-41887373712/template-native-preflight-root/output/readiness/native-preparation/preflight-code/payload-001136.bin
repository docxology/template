"""Reserve finite source image decoding before any RGBA/RGB allocation."""

from __future__ import annotations

MAX_SOURCE_IMAGE_PIXELS = 60_000_000
MAX_SOURCE_DECODED_PIXELS = 120_000_000
MAX_SOURCE_IMAGE_OCCURRENCES = 20_000


class SourceImageDecodeBudget:
    """Account for every separately retained original source image occurrence.

    Dimensions must come from the actual original image header. Repeated source
    assets reserve each held decoded copy; neither compressed size nor identical
    bytes excuse the aggregate decoded-memory obligation. A rejected admission
    never changes the already admitted counters.
    """

    def __init__(self, occurrences: int) -> None:
        if type(occurrences) is not int or not 0 <= occurrences <= MAX_SOURCE_IMAGE_OCCURRENCES:
            raise ValueError("source figure occurrence closure exceeds its finite decoding budget")
        self.expected_occurrences = occurrences
        self.admitted_occurrences = 0
        self.decoded_pixels = 0

    def admit_header(self, width: int, height: int) -> None:
        """Reserve before ImageOps/convert/copy can allocate decoded buffers."""
        if type(width) is not int or type(height) is not int or min(width, height) <= 0:
            raise ValueError("source image header dimensions are not finite positive integers")
        pixels = width * height
        if pixels > MAX_SOURCE_IMAGE_PIXELS:
            raise ValueError("source figure exceeds its existing per-image pixel budget")
        if self.admitted_occurrences >= self.expected_occurrences:
            raise ValueError("source image decoder consumed an undeclared original occurrence")
        if self.decoded_pixels + pixels > MAX_SOURCE_DECODED_PIXELS:
            raise ValueError("source figure closure exceeds its aggregate decoded-pixel budget")
        self.admitted_occurrences += 1
        self.decoded_pixels += pixels
