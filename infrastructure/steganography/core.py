"""Steganography core orchestrator.

``SteganographyProcessor`` chains the individual steganographic techniques
(overlays, barcodes, metadata, hashing, encryption) into a single
``process()`` call that takes an input PDF and writes a fully-augmented
output PDF.
"""

from __future__ import annotations

import io
import os
import shutil
import tempfile
from pathlib import Path

from dataclasses import dataclass, field

from infrastructure.core.logging_utils import get_logger, log_operation
from infrastructure.steganography.config import DocumentMetadata, SteganographyConfig

logger = get_logger(__name__)


@dataclass
class BarcodeBuildContext:
    """Metadata fields passed to the barcode strip overlay builder."""

    title: str = ""
    authors: list[str] | None = field(default_factory=list)
    keywords: list[str] | None = field(default_factory=list)
    author_emails: list[str] | None = field(default_factory=list)
    document_id: str = ""
    hashes: dict[str, str] = field(default_factory=dict)
    source_filename: str = ""
    source_file_size: int = 0


class SteganographyProcessor:
    """Orchestrates steganographic PDF post-processing.

    Usage::

        from infrastructure.steganography import SteganographyProcessor, SteganographyConfig

        processor = SteganographyProcessor(SteganographyConfig.all_enabled())
        processor.process(Path("paper.pdf"), Path("paper_steganography.pdf"))
    """

    def __init__(self, config: SteganographyConfig | None = None):
        self.config = config or SteganographyConfig()
        self._document_id: str = ""
        self._hashes: dict[str, str] = {}
        self._metadata_extra: dict[str, str] = {}

    # ── Public API ───────────────────────────────────────────────────

    @log_operation("steganography.process")
    def process(
        self,
        input_pdf: Path,
        output_pdf: Path | None = None,
        title: str = "",
        authors: list[str] | None = None,
        keywords: list[str] | None = None,
        author_emails: list[str] | None = None,
    ) -> Path:
        """Run all enabled steganographic techniques on *input_pdf*.

        Args:
            input_pdf: Source PDF to augment.
            output_pdf: Where to write the augmented PDF.  Defaults to
                        ``<input_stem><suffix>.pdf``.
            title: Document title (used in barcodes/metadata).
            authors: Author names for metadata.
            keywords: Keyword list for metadata.

        Returns:
            Path to the generated steganography PDF.
        """
        if not self.config.enabled:
            logger.info("Steganography disabled — skipping processing")
            return input_pdf

        if not input_pdf.exists():
            raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

        if output_pdf is None:
            output_pdf = input_pdf.with_stem(input_pdf.stem + self.config.output_suffix)

        logger.info("╔══ Steganography Processing ═══════════════════════════════╗")
        logger.info(f"║  Input:  {input_pdf.name}")
        logger.info(f"║  Output: {output_pdf.name}")

        # Start with a working copy
        working_pdf = self._make_working_copy(input_pdf)

        try:
            # 1. Compute hashes of the *original* PDF
            if self.config.hashing_enabled:
                self._step_hashing(input_pdf)

            # 2. Generate document ID
            from infrastructure.steganography.encryption import generate_document_id

            self._document_id = generate_document_id()
            logger.info(f"║  Doc-ID: {self._document_id}")

            # 3. Apply overlays and barcodes (merged onto each page)
            if self.config.overlays_enabled or self.config.barcodes_enabled:
                bc_ctx = BarcodeBuildContext(
                    title=title,
                    authors=authors or [],
                    keywords=keywords or [],
                    author_emails=author_emails or [],
                    document_id=self._document_id,
                    hashes=self._hashes,
                    source_filename=input_pdf.name if input_pdf else "",
                    source_file_size=input_pdf.stat().st_size
                    if input_pdf and input_pdf.exists()
                    else 0,
                )
                working_pdf = self._step_overlays_and_barcodes(working_pdf, bc_ctx)

            # 4. Inject metadata
            if self.config.metadata_enabled:
                working_pdf = self._step_metadata(
                    working_pdf,
                    title=title,
                    authors=authors,
                    keywords=keywords,
                )

            # 5. Encrypt (password protection)
            if self.config.encryption_enabled and self.config.pdf_password:
                working_pdf = self._step_encryption(working_pdf)

            # 6. Write hash manifest sidecar
            if self.config.hashing_enabled and self.config.manifest_enabled:
                self._step_manifest(input_pdf)

            # Copy working file to final destination
            shutil.copy2(str(working_pdf), str(output_pdf))
            logger.info(f"║  ✓ Steganography PDF written: {output_pdf.name}")
            logger.info("╚═══════════════════════════════════════════════════════════╝")
            return output_pdf

        finally:
            # Clean up temp files
            if working_pdf != input_pdf and working_pdf.exists():
                try:
                    working_pdf.unlink()
                except OSError as e:
                    logger.debug(f"Failed to delete working PDF {working_pdf}: {e}")

    # ── Private pipeline steps ───────────────────────────────────────

    def _make_working_copy(self, input_pdf: Path) -> Path:
        """Copy the input PDF to a temp file for in-place mutations."""
        fd, tmp_str = tempfile.mkstemp(suffix=".pdf", prefix="steg_")
        os.close(fd)
        tmp = Path(tmp_str)
        shutil.copy2(str(input_pdf), str(tmp))
        return tmp

    def _step_hashing(self, pdf_path: Path) -> None:
        """Compute file hashes and store for later use."""
        from infrastructure.steganography.hashing import compute_file_hashes

        self._hashes = compute_file_hashes(pdf_path, algorithms=self.config.hash_algorithms)
        for algo, digest in self._hashes.items():
            logger.info(f"║  {algo.upper()}: {digest[:32] + '…'}")

    def _step_overlays_and_barcodes(
        self,
        working_pdf: Path,
        ctx: BarcodeBuildContext,
    ) -> Path:
        """Merge overlay and barcode pages onto every page of the PDF."""
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            raise ImportError("The 'pypdf' package is required. Install with: pip install pypdf")

        reader = PdfReader(str(working_pdf))
        writer = PdfWriter()
        total_pages = len(reader.pages)

        hash_short = ""
        if ctx.hashes:
            first_algo = next(iter(ctx.hashes))
            hash_short = ctx.hashes[first_algo][:16]

        # Build QR overlay data once if in QR mode
        qr_overlay_data = ""
        if self.config.overlays_enabled and self.config.overlay_mode == "qr":
            from infrastructure.steganography.barcodes import build_barcode_payload

            qr_overlay_data = self.config.overlay_qr_data or build_barcode_payload(
                title=ctx.title,
                hashes=ctx.hashes,
                document_id=ctx.document_id,
            )

        for page_idx, page in enumerate(reader.pages):
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            # ── Full-page overlay (text, QR, or none) ────────────
            if self.config.overlays_enabled and self.config.overlay_mode != "none":
                if self.config.overlay_mode == "qr":
                    from infrastructure.steganography.overlays import create_qr_overlay

                    wm_bytes = create_qr_overlay(
                        page_width,
                        page_height,
                        qr_data=qr_overlay_data,
                        opacity=self.config.overlay_opacity,
                    )
                else:  # 'text' (default)
                    from infrastructure.steganography.overlays import create_watermark_overlay

                    wm_bytes = create_watermark_overlay(
                        page_width,
                        page_height,
                        text=self.config.overlay_text,
                        opacity=self.config.overlay_opacity,
                        color_rgb=self.config.overlay_color_rgb,
                        font_size=self.config.overlay_font_size,
                        repeat_count=self.config.overlay_repeat_count,
                    )
                wm_page = PdfReader(io.BytesIO(wm_bytes)).pages[0]
                page.merge_page(wm_page)

            # ── Footer overlay (always if overlays enabled) ──────
            if self.config.overlays_enabled:
                from infrastructure.steganography.overlays import (
                    FooterConfig,
                    create_footer_overlay,
                    create_invisible_text_overlay,
                )

                footer_cfg = FooterConfig(
                    document_id=ctx.document_id,
                    page_number=page_idx + 1,
                    total_pages=total_pages,
                    hash_short=hash_short,
                    title=ctx.title,
                    authors=", ".join(a for a in ctx.authors if a) if ctx.authors else "",
                    source_filename=ctx.source_filename,
                    source_file_size=ctx.source_file_size,
                )
                footer_bytes = create_footer_overlay(page_width, page_height, footer_cfg)
                footer_page = PdfReader(io.BytesIO(footer_bytes)).pages[0]
                page.merge_page(footer_page)

                # Invisible text layer (first page only)
                if page_idx == 0:
                    hidden_data = f"STEG_ID:{ctx.document_id}|TITLE:{ctx.title}|HASHES:{hash_short}"
                    inv_bytes = create_invisible_text_overlay(page_width, page_height, hidden_data)
                    inv_page = PdfReader(io.BytesIO(inv_bytes)).pages[0]
                    page.merge_page(inv_page)

            # ── Barcode strip ────────────────────────────────────
            if self.config.barcodes_enabled:
                from infrastructure.steganography.barcodes import (
                    build_barcode_payload,
                    create_barcode_strip_overlay,
                )

                qr_payload = build_barcode_payload(
                    title=ctx.title,
                    hashes=ctx.hashes,
                    document_id=ctx.document_id,
                )
                c128_payload = f"ID:{ctx.document_id[:16]}|P:{page_idx + 1}"

                bc_bytes = create_barcode_strip_overlay(
                    page_width,
                    page_height,
                    qr_data=self.config.barcode_content or qr_payload,
                    code128_data=c128_payload,
                    title=ctx.title,
                    authors=ctx.authors,
                    keywords=ctx.keywords,
                    author_emails=ctx.author_emails,
                    document_id=ctx.document_id,
                    hashes=ctx.hashes,
                    source_filename=ctx.source_filename,
                    total_pages=total_pages,
                    source_file_size=ctx.source_file_size,
                )
                bc_page = PdfReader(io.BytesIO(bc_bytes)).pages[0]
                page.merge_page(bc_page)

            writer.add_page(page)

        # Write merged PDF back to the working file
        out_path = working_pdf.with_suffix(".merged.pdf")
        with open(out_path, "wb") as fh:
            writer.write(fh)

        # Replace working copy
        working_pdf.unlink()
        out_path.rename(working_pdf)
        logger.info(f"║  ✓ Overlays and barcodes applied to {total_pages} pages")
        return working_pdf

    def _step_metadata(
        self,
        working_pdf: Path,
        title: str = "",
        authors: list[str] | None = None,
        keywords: list[str] | None = None,
    ) -> Path:
        """Inject metadata into the PDF."""
        import json
        from infrastructure.steganography.metadata import (
            build_document_metadata,
            build_xmp_packet,
            inject_pdf_metadata,
        )

        doc = DocumentMetadata(
            title=title,
            authors=authors,
            hashes=self._hashes,
            document_id=self._document_id,
            keywords=keywords,
        )
        meta = build_document_metadata(doc)
        xmp = build_xmp_packet(doc)

        manifest_dict = {
            "document_id": self._document_id,
            "hashes": self._hashes,
            "title": title,
            "steganography_applied": True,
        }
        attachments = {"stego_manifest.json": json.dumps(manifest_dict, indent=2).encode("utf-8")}

        inject_pdf_metadata(
            working_pdf, working_pdf, metadata=meta, xmp_string=xmp, attachments=attachments
        )
        logger.info("║  ✓ Metadata, XMP, and manifest attachment injected")
        return working_pdf

    def _step_encryption(self, working_pdf: Path) -> Path:
        """Apply PDF password protection."""
        from infrastructure.steganography.encryption import apply_pdf_password

        enc_path = working_pdf.with_suffix(".enc.pdf")
        apply_pdf_password(
            working_pdf,
            enc_path,
            user_password=self.config.pdf_password or "",
        )
        working_pdf.unlink()
        enc_path.rename(working_pdf)
        logger.info("║  ✓ PDF password protection applied")
        return working_pdf

    def _step_manifest(self, original_pdf: Path) -> None:
        """Write the JSON hash manifest sidecar."""
        from infrastructure.steganography.hashing import write_hash_manifest

        write_hash_manifest(
            original_pdf,
            self._hashes,
            extra={
                "document_id": self._document_id,
                "steganography_applied": "true",
            },
        )
        logger.info("║  ✓ Hash manifest written")


# ── Convenience function ─────────────────────────────────────────────────


def process_pdf(
    input_pdf: Path,
    output_pdf: Path | None = None,
    config: SteganographyConfig | None = None,
    title: str = "",
    authors: list[str] | None = None,
    keywords: list[str] | None = None,
    author_emails: list[str] | None = None,
) -> Path:
    """Convenience function — create a processor and run it.

    Args:
        input_pdf: Source PDF.
        output_pdf: Output path (auto-derived if None).
        config: Steganography config (all-enabled if None).
        title: Document title.
        authors: Author names.
        keywords: Keywords.

    Returns:
        Path to the steganography PDF.
    """
    if config is None:
        config = SteganographyConfig.all_enabled()

    processor = SteganographyProcessor(config)
    return processor.process(
        input_pdf,
        output_pdf=output_pdf,
        title=title,
        authors=authors,
        keywords=keywords,
        author_emails=author_emails,
    )
