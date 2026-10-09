"""Real header admission and finite aggregate/occurrence boundary controls."""

from io import BytesIO

import pytest
from PIL import Image

from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    MAX_SOURCE_IMAGE_OCCURRENCES,
    SourceImageDecodeBudget,
)


def test_actual_png_header_is_admitted_before_pixel_decode() -> None:
    stream = BytesIO()
    Image.new("RGB", (80, 48), "white").save(stream, format="PNG")
    budget = SourceImageDecodeBudget(1)
    with Image.open(BytesIO(stream.getvalue())) as original:
        budget.admit_header(original.width, original.height)
        assert budget.decoded_pixels == 3840
        original.load()
    assert budget.admitted_occurrences == 1


def test_aggregate_decode_admission_refuses_third_maximum_header_without_allocation() -> None:
    budget = SourceImageDecodeBudget(3)
    budget.admit_header(10_000, 6000)
    budget.admit_header(10_000, 6000)
    with pytest.raises(ValueError, match="aggregate decoded-pixel"):
        budget.admit_header(1, 1)
    assert budget.decoded_pixels == 120_000_000
    assert budget.admitted_occurrences == 2


def test_occurrence_closure_is_bounded_before_source_decoding() -> None:
    with pytest.raises(ValueError, match="occurrence closure"):
        SourceImageDecodeBudget(MAX_SOURCE_IMAGE_OCCURRENCES + 1)
    budget = SourceImageDecodeBudget(1)
    budget.admit_header(1, 1)
    with pytest.raises(ValueError, match="undeclared original occurrence"):
        budget.admit_header(1, 1)
    assert budget.decoded_pixels == 1 and budget.admitted_occurrences == 1


def test_per_image_limit_stays_unchanged_and_rejection_preserves_counters() -> None:
    budget = SourceImageDecodeBudget(1)
    with pytest.raises(ValueError, match="per-image pixel"):
        budget.admit_header(60_000_001, 1)
    assert budget.decoded_pixels == 0 and budget.admitted_occurrences == 0


@pytest.mark.parametrize("width,height", [(0, 1), (1, 0), (-1, 1), (True, 1), (1, False)])
def test_malformed_source_header_dimensions_are_not_admitted(width: int, height: int) -> None:
    budget = SourceImageDecodeBudget(1)
    with pytest.raises(ValueError, match="positive integers"):
        budget.admit_header(width, height)
    assert budget.decoded_pixels == 0 and budget.admitted_occurrences == 0
