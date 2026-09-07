"""Validate transmission bookends occupy exactly one PDF page each."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

BEGIN_MARKER = "BEGINNING OF TRANSMISSION"
END_MARKER = "END OF TRANSMISSION"
OVERFLOW_MARKER = "Integrity QR strip"


def _page_has_marker(text: str, marker: str) -> bool:
    return marker in text or f"<!-- {marker} -->" in text


@dataclass(frozen=True)
class TransmissionPageCheckResult:
    """Outcome of transmission bookend page-span validation."""

    valid: bool
    page_count: int
    begin_pages: tuple[int, ...]
    end_pages: tuple[int, ...]
    issues: tuple[str, ...]


def _extract_page_texts(pdf_path: Path) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    texts: list[str] = []
    for page in reader.pages:
        raw = page.extract_text() or ""
        texts.append(raw)
    return texts


def check_transmission_bookend_pages(pdf_path: Path) -> TransmissionPageCheckResult:
    """Assert begin/end bookends each fit on a single dedicated page."""
    if not pdf_path.is_file():
        return TransmissionPageCheckResult(
            valid=False,
            page_count=0,
            begin_pages=(),
            end_pages=(),
            issues=(f"PDF not found: {pdf_path}",),
        )

    texts = _extract_page_texts(pdf_path)
    page_count = len(texts)
    if page_count == 0:
        return TransmissionPageCheckResult(
            valid=False,
            page_count=0,
            begin_pages=(),
            end_pages=(),
            issues=("PDF has no pages",),
        )

    begin_pages = tuple(index + 1 for index, text in enumerate(texts) if _page_has_marker(text, BEGIN_MARKER))
    end_pages = tuple(index + 1 for index, text in enumerate(texts) if _page_has_marker(text, END_MARKER))
    issues: list[str] = []

    if not begin_pages:
        issues.append(f"Missing {BEGIN_MARKER} marker")
    elif begin_pages[0] != 1:
        issues.append(f"{BEGIN_MARKER} must be on page 1, found on page(s) {begin_pages}")
    elif len(begin_pages) > 1:
        issues.append(f"{BEGIN_MARKER} spans multiple pages: {begin_pages}")
    elif END_MARKER in texts[0] or _page_has_marker(texts[0], END_MARKER):
        issues.append(f"Page 1 contains both {BEGIN_MARKER} and {END_MARKER}")

    if not end_pages:
        issues.append(f"Missing {END_MARKER} marker")
    elif end_pages[-1] != page_count:
        issues.append(f"{END_MARKER} must be on last page ({page_count}), found on page(s) {end_pages}")
    elif len(end_pages) > 1:
        issues.append(f"{END_MARKER} spans multiple pages: {end_pages}")

    for page_num in begin_pages[1:]:
        issues.append(f"{BEGIN_MARKER} repeated on page {page_num}")

    for page_num in end_pages[:-1]:
        issues.append(f"{END_MARKER} appears before final page on page {page_num}")

    if len(texts) > 1 and BEGIN_MARKER in texts[0] and OVERFLOW_MARKER in texts[1]:
        issues.append(
            "Begin bookend overflow: integrity strip marker appears on page 2 (bookend content likely spans >1 page)"
        )

    valid = not issues
    return TransmissionPageCheckResult(
        valid=valid,
        page_count=page_count,
        begin_pages=begin_pages,
        end_pages=end_pages,
        issues=tuple(issues),
    )


def validate_transmission_bookend_pages(pdf_path: Path) -> bool:
    """Run page-span check and log issues. Returns True when valid."""
    result = check_transmission_bookend_pages(pdf_path)
    if result.valid:
        logger.info(
            "Transmission bookends OK: begin page %s, end page %s (%d pages)",
            result.begin_pages[0] if result.begin_pages else "?",
            result.end_pages[-1] if result.end_pages else "?",
            result.page_count,
        )
        return True
    for issue in result.issues:
        logger.error("Transmission page check: %s", issue)
    return False


def main() -> int:
    """CLI entry point for transmission bookend page-span validation."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Validate transmission bookend single-page contract")
    parser.add_argument("pdf", type=Path, help="Combined PDF path")
    args = parser.parse_args()
    result = check_transmission_bookend_pages(args.pdf)
    if result.valid:
        print(
            f"OK: begin page {result.begin_pages[0]}, end page {result.end_pages[-1]}, {result.page_count} pages total"
        )
        return 0
    for issue in result.issues:
        print(f"FAIL: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
