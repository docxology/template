"""PDF structure validation and auxiliary file repair utilities."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def validate_pdf_structure(pdf_path: Path) -> bool:
    """Check that a PDF file has valid trailer markers.

    A structurally valid PDF must end with a cross-reference table
    (``xref`` or ``startxref``) and a ``%%EOF`` marker.  When xelatex
    is killed by SIGPIPE (exit 141), the file may be truncated before
    these markers are written, producing a file that opens partially
    or not at all in some readers.

    Args:
        pdf_path: Path to the PDF file to validate.

    Returns:
        True if the PDF has valid structure, False otherwise.
    """
    try:
        with open(pdf_path, "rb") as f:
            # Read the last 4 KB -- xref + EOF are at the very end
            f.seek(0, 2)  # seek to end
            size = f.tell()
            tail_size = min(size, 4096)
            f.seek(size - tail_size)
            tail = f.read(tail_size)

        has_eof = b"%%EOF" in tail
        has_startxref = b"startxref" in tail
        if not has_eof or not has_startxref:
            logger.debug(
                f"  PDF validation: %%EOF={has_eof}, startxref={has_startxref} "
                f"in {pdf_path.name} ({size:,} bytes)"
            )
            return False
        return True
    except Exception as e:  # noqa: BLE001
        logger.debug(f"  PDF validation skipped: {e}")
        return False


def repair_truncated_aux(aux_file: Path) -> None:
    """Repair a truncated .aux file by removing the last incomplete entry."""
    if not aux_file.exists():
        return

    try:
        content = aux_file.read_text(encoding="utf-8", errors="replace")
        if not content:
            return

        lines = content.split("\n")

        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return

        # Check if the last line has balanced braces
        last_line = lines[-1]
        brace_depth = last_line.count("{") - last_line.count("}")

        if brace_depth != 0:
            # Last line is incomplete -- remove it
            removed = lines.pop()
            logger.info(
                f"  ✓ Repaired truncated .aux: removed incomplete entry "
                f"({len(removed)} chars, brace depth {brace_depth})"
            )

            # Also check the new last line in case multiple lines were truncated
            while lines and lines[-1].strip():
                new_last = lines[-1]
                depth = new_last.count("{") - new_last.count("}")
                if depth != 0:
                    lines.pop()
                else:
                    break

            # Write the repaired content
            _tmp = aux_file.with_suffix(aux_file.suffix + ".tmp")
            try:
                _tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
                _tmp.replace(aux_file)
            except Exception:  # noqa: BLE001
                _tmp.unlink(missing_ok=True)
                raise
    except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001
        logger.debug(f"  .aux repair skipped: {e}")
