"""Steganography core orchestrator.

``SteganographyProcessor`` chains the individual steganographic techniques
(overlays, barcodes, metadata, hashing, encryption) into a single
``process()`` call that takes an input PDF and writes a fully-augmented
output PDF.
"""

import io
import shutil
import tempfile
from pathlib import Path

from dataclasses import asdict, dataclass, field

from infrastructure.core.logging.utils import get_logger, log_operation
from infrastructure.steganography.artifact_paths import (
    hash_manifest_path,
    owned_secure_pdf_sha256,
    prepare_secure_pdf_ownership,
    secure_file_sha256,
    secure_pdf_path,
)
from infrastructure.steganography.config import (
    BuildIdentity,
    DocumentMetadata,
    SteganographyConfig,
    resolve_build_identity,
)

logger = get_logger(__name__)


@dataclass
class BarcodeBuildContext:
    """Metadata fields passed to the barcode strip overlay builder."""

    title: str = ""
    authors: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    author_emails: list[str] = field(default_factory=list)
    document_id: str = ""
    hashes: dict[str, str] = field(default_factory=dict)
    source_filename: str = ""
    source_file_size: int = 0
    timestamp: str | None = None


@dataclass(frozen=True)
class ProcessingContext:
    """Identity and configuration owned by exactly one processing invocation."""

    config: SteganographyConfig
    document_id: str
    hashes: dict[str, str]
    build: BuildIdentity
    source_file_size: int


class SteganographyProcessor:
    """Orchestrates steganographic PDF post-processing.

    Usage::

        from infrastructure.steganography import SteganographyProcessor, SteganographyConfig

        processor = SteganographyProcessor(SteganographyConfig.all_enabled())
        processor.process(Path("paper.pdf"), Path("paper_steganography.pdf"))
    """

    def __init__(
        self,
        config: SteganographyConfig | None = None,
        *,
        repo_root: Path | None = None,
        protect_output: bool = False,
    ):
        """Initialize a processor with optional build provenance and output ownership checks."""
        self.config = config or SteganographyConfig()
        self.repo_root = repo_root
        self.protect_output = protect_output

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
        *,
        deterministic: bool | None = None,
    ) -> Path:
        """Run all enabled steganographic techniques on *input_pdf*.

        Args:
            input_pdf: Source PDF to augment.
            output_pdf: Where to write the augmented PDF.  Defaults to
                        ``<input_stem><suffix>.pdf``.
            title: Document title (used in barcodes/metadata).
            authors: Author names for metadata.
            keywords: Keyword list for metadata.
            author_emails: Optional list of author email addresses for barcode metadata.
            deterministic: Override build identity mode for this PDF. By default,
                honor the legacy environment setting.

        Returns:
            Path to the generated steganography PDF.
        """
        config = SteganographyConfig.from_dict(asdict(self.config))
        if not config.enabled:
            logger.info("Steganography disabled — skipping processing")
            return input_pdf
        if not input_pdf.exists():
            raise FileNotFoundError(f"Input PDF not found: {input_pdf}")
        if output_pdf is None:
            output_pdf = secure_pdf_path(input_pdf, config.output_suffix)

        from infrastructure.steganography.encryption import generate_document_id
        from infrastructure.steganography.publication import publish_artifacts, validate_destinations, validate_pdf

        manifest_path = hash_manifest_path(input_pdf) if config.hashing_enabled and config.manifest_enabled else None
        destinations = [output_pdf, *([manifest_path] if manifest_path is not None else [])]
        if config.kmyth_enabled:
            for artifact in config.kmyth_seal_artifacts:
                target = output_pdf if artifact == "pdf" else manifest_path
                if target is not None:
                    destinations.append(target.with_name(target.name + config.kmyth_output_suffix))
        validate_destinations(input_pdf, destinations)
        expected_pdf = None
        if self.protect_output:
            previous = None
            if output_pdf.exists():
                previous = owned_secure_pdf_sha256(input_pdf, output_pdf)
                if previous is None:
                    raise ValueError(
                        f"Cannot replace a custom secure PDF without matching source evidence: {output_pdf}"
                    )
            expected_pdf = (output_pdf, previous)

        if config.kmyth_enabled and not config.kmyth_overwrite:
            selected = []
            for artifact in config.kmyth_seal_artifacts:
                target = output_pdf if artifact == "pdf" else manifest_path
                sealed = target.with_name(target.name + config.kmyth_output_suffix) if target is not None else None
                if sealed is not None and sealed.exists():
                    if config.kmyth_required:
                        raise FileExistsError(sealed)
                    logger.warning("Kmyth sidecar already exists; preserving %s", sealed.name)
                else:
                    selected.append(artifact)
            config.kmyth_seal_artifacts = selected

        logger.info("Steganography processing %s → %s", input_pdf.name, output_pdf.name)
        with tempfile.TemporaryDirectory(prefix=".steganography-", dir=output_pdf.parent) as temporary:
            directory = Path(temporary)
            working_pdf = directory / "working.pdf"
            shutil.copy2(input_pdf, working_pdf)
            build = resolve_build_identity(repo_root=self.repo_root, deterministic=deterministic)
            ctx = ProcessingContext(
                config=config,
                document_id=generate_document_id(deterministic=build.deterministic, timestamp=build.timestamp),
                hashes=self._step_hashing(working_pdf, config) if config.hashing_enabled else {},
                build=build,
                source_file_size=working_pdf.stat().st_size,
            )
            if config.overlays_enabled or config.barcodes_enabled:
                barcode_context = BarcodeBuildContext(
                    title=title,
                    authors=list(authors or []),
                    keywords=list(keywords or []),
                    author_emails=list(author_emails or []),
                    document_id=ctx.document_id,
                    hashes=ctx.hashes,
                    source_filename=input_pdf.name,
                    source_file_size=ctx.source_file_size,
                    timestamp=ctx.build.timestamp,
                )
                working_pdf = self._step_overlays_and_barcodes(working_pdf, barcode_context, config)
            if config.metadata_enabled:
                working_pdf = self._step_metadata(working_pdf, ctx, title=title, authors=authors, keywords=keywords)
            if config.encryption_enabled and config.pdf_password:
                working_pdf = self._step_encryption(working_pdf, config)
            validate_pdf(working_pdf, password=config.pdf_password)

            # No public artifact is changed until all required producers succeed.
            artifact_evidence = None
            if self.protect_output:
                secure_digest = secure_file_sha256(working_pdf)
                artifact_evidence = {"secure_pdf": output_pdf.name, "secure_pdf_sha256": secure_digest}
            staged_manifest = (
                self._step_manifest(input_pdf, ctx, directory / "manifest.json", artifact_evidence=artifact_evidence)
                if manifest_path
                else None
            )
            artifacts = {output_pdf: working_pdf}
            if manifest_path is not None and staged_manifest is not None:
                artifacts[manifest_path] = staged_manifest
            sealed_destinations: set[Path] = set()
            if config.kmyth_enabled:
                for sealed in self._step_kmyth(working_pdf, staged_manifest, config):
                    original = (
                        working_pdf if sealed.name == working_pdf.name + config.kmyth_output_suffix else staged_manifest
                    )
                    if original is None:
                        raise ValueError("Kmyth returned an unselected artifact")
                    destination = output_pdf if original == working_pdf else manifest_path
                    if destination is None:
                        raise ValueError("Kmyth returned an artifact without a destination")
                    target = destination.with_name(destination.name + config.kmyth_output_suffix)
                    artifacts[target] = sealed
                    sealed_destinations.add(target)
            ownership = (
                prepare_secure_pdf_ownership(input_pdf, output_pdf, artifact_evidence["secure_pdf_sha256"])
                if artifact_evidence is not None
                else None
            )
            publish_artifacts(
                artifacts,
                source=input_pdf,
                no_overwrite=sealed_destinations if not config.kmyth_overwrite else None,
                expected_pdf=expected_pdf,
                ownership=ownership,
            )
        logger.info("Steganography PDF written: %s", output_pdf.name)
        return output_pdf

    # ── Private pipeline steps ───────────────────────────────────────

    def _step_hashing(self, pdf_path: Path, config: SteganographyConfig) -> dict[str, str]:
        """Compute hashes for this invocation, never processor instance state."""
        from infrastructure.steganography.hashing import compute_file_hashes

        return compute_file_hashes(pdf_path, algorithms=config.hash_algorithms)

    def _step_overlays_and_barcodes(
        self,
        working_pdf: Path,
        ctx: BarcodeBuildContext,
        config: SteganographyConfig,
    ) -> Path:
        """Merge overlay and barcode pages onto every page of the PDF."""
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            raise ImportError("The 'pypdf' package is required. Install with: pip install pypdf") from None

        reader = PdfReader(str(working_pdf))
        writer = PdfWriter()
        writer.clone_document_from_reader(reader)
        total_pages = len(reader.pages)

        hash_short = ""
        if ctx.hashes:
            first_algo = next(iter(ctx.hashes))
            hash_short = ctx.hashes[first_algo][:16]

        # Build QR overlay data once if in QR mode
        qr_overlay_data = ""
        if config.overlays_enabled and config.overlay_mode == "qr":
            from infrastructure.steganography.barcodes import build_barcode_payload

            qr_overlay_data = config.overlay_qr_data or build_barcode_payload(
                title=ctx.title,
                hashes=ctx.hashes,
                document_id=ctx.document_id,
                timestamp=ctx.timestamp,
            )

        for page_idx, page in enumerate(reader.pages):
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            out_page = writer.pages[page_idx]

            # ── Full-page overlay (text, QR, or none) ────────────
            if config.overlays_enabled and config.overlay_mode != "none":
                if config.overlay_mode == "qr":
                    from infrastructure.steganography.overlays import create_qr_overlay

                    wm_bytes = create_qr_overlay(
                        page_width,
                        page_height,
                        qr_data=qr_overlay_data,
                        opacity=config.overlay_opacity,
                    )
                else:  # 'text' (default)
                    from infrastructure.steganography.overlays import create_watermark_overlay

                    wm_bytes = create_watermark_overlay(
                        page_width,
                        page_height,
                        text=config.overlay_text,
                        opacity=config.overlay_opacity,
                        color_rgb=config.overlay_color_rgb,
                        font_size=config.overlay_font_size,
                        repeat_count=config.overlay_repeat_count,
                    )
                wm_page = PdfReader(io.BytesIO(wm_bytes)).pages[0]
                out_page.merge_page(wm_page)

            # ── Footer overlay (always if overlays enabled) ──────
            if config.overlays_enabled:
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
                footer_bytes = create_footer_overlay(page_width, page_height, footer_cfg, timestamp=ctx.timestamp)
                footer_page = PdfReader(io.BytesIO(footer_bytes)).pages[0]
                out_page.merge_page(footer_page)

                # Invisible text layer (first page only)
                if page_idx == 0:
                    hidden_data = f"STEG_ID:{ctx.document_id}|TITLE:{ctx.title}|HASHES:{hash_short}"
                    inv_bytes = create_invisible_text_overlay(page_width, page_height, hidden_data)
                    inv_page = PdfReader(io.BytesIO(inv_bytes)).pages[0]
                    out_page.merge_page(inv_page)

            # ── Barcode strip ────────────────────────────────────
            if config.barcodes_enabled:
                from infrastructure.steganography.barcodes import create_barcode_strip_overlay

                c128_payload = f"ID:{ctx.document_id[:16]}|P:{page_idx + 1}"

                bc_bytes = create_barcode_strip_overlay(
                    page_width,
                    page_height,
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
                    timestamp=ctx.timestamp,
                )
                bc_page = PdfReader(io.BytesIO(bc_bytes)).pages[0]
                out_page.merge_page(bc_page)

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
        ctx: ProcessingContext,
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
            hashes=ctx.hashes,
            document_id=ctx.document_id,
            keywords=keywords,
            timestamp=ctx.build.timestamp,
            extra={
                "GitCommit": ctx.build.git_commit or "unavailable",
                "GitCommitAvailable": str(bool(ctx.build.git_commit)).lower(),
            },
        )
        meta = build_document_metadata(doc)
        xmp = build_xmp_packet(doc)

        manifest_dict = {
            "document_id": ctx.document_id,
            "hashes": ctx.hashes,
            "title": title,
            "git_commit": ctx.build.git_commit,
            "git_commit_available": bool(ctx.build.git_commit),
            "steganography_applied": True,
        }
        attachments = {"stego_manifest.json": json.dumps(manifest_dict, indent=2).encode("utf-8")}

        inject_pdf_metadata(working_pdf, working_pdf, metadata=meta, xmp_string=xmp, attachments=attachments)
        logger.info("║  ✓ Metadata, XMP, and manifest attachment injected")
        return working_pdf

    def _step_encryption(self, working_pdf: Path, config: SteganographyConfig) -> Path:
        """Apply PDF password protection."""
        from infrastructure.steganography.encryption import apply_pdf_password

        enc_path = working_pdf.with_suffix(".enc.pdf")
        apply_pdf_password(
            working_pdf,
            enc_path,
            user_password=config.pdf_password or "",
            algorithm=config.pdf_encryption_algorithm,
        )
        working_pdf.unlink()
        enc_path.rename(working_pdf)
        logger.info("║  ✓ PDF password protection applied")
        return working_pdf

    def _step_manifest(
        self,
        original_pdf: Path,
        ctx: ProcessingContext,
        output_path: Path,
        *,
        artifact_evidence: dict[str, str] | None = None,
    ) -> Path:
        """Write the JSON hash manifest sidecar."""
        from infrastructure.steganography.hashing import write_hash_manifest

        manifest_path = write_hash_manifest(
            original_pdf,
            ctx.hashes,
            output_path=output_path,
            timestamp=ctx.build.timestamp,
            extra={
                "document_id": ctx.document_id,
                "source_size_bytes": ctx.source_file_size,
                "git_commit": ctx.build.git_commit,
                "git_commit_available": bool(ctx.build.git_commit),
                "steganography_applied": "true",
                **(artifact_evidence or {}),
            },
        )
        logger.info("║  ✓ Hash manifest written")
        return manifest_path

    def _step_kmyth(
        self, output_pdf: Path, manifest_path: Path | None, config: SteganographyConfig | None = None
    ) -> list[Path]:
        """Seal configured artifacts with Kmyth when explicitly enabled."""
        from infrastructure.steganography.kmyth_adapter import (
            KmythCommandError,
            KmythSealOptions,
            KmythUnavailableError,
            seal_file_with_kmyth,
            validate_kmyth_installation,
        )

        config = config or SteganographyConfig.from_dict(asdict(self.config))
        targets: list[Path] = []
        for artifact in config.kmyth_seal_artifacts:
            if artifact == "pdf":
                targets.append(output_pdf)
            elif artifact == "hash_manifest":
                if manifest_path is not None and manifest_path.exists():
                    targets.append(manifest_path)
                else:
                    logger.warning(
                        "Kmyth requested hash_manifest sealing, but no hash manifest exists. "
                        "Enable hashing_enabled and manifest_enabled to seal it."
                    )

        if not targets:
            message = "Kmyth enabled but no sealable artifacts were selected."
            if config.kmyth_required:
                raise KmythUnavailableError(message)
            logger.warning(message)
            return []

        options = KmythSealOptions.from_config(config)
        availability = validate_kmyth_installation(binary_dir=options.binary_dir, source_dir=options.source_dir)
        if not availability.available:
            if config.kmyth_required:
                raise KmythUnavailableError(availability.summary())
            logger.warning("Kmyth sealing skipped: %s", availability.summary())
            return []

        sealed: list[Path] = []
        for target in targets:
            try:
                sealed.append(seal_file_with_kmyth(target, options=options))
            except (KmythCommandError, KmythUnavailableError, FileExistsError, FileNotFoundError) as exc:
                if config.kmyth_required:
                    raise
                logger.warning("Kmyth sealing skipped for %s: %s", target.name, exc)
                return sealed

        logger.info("║  ✓ Kmyth TPM sidecars written: %s", ", ".join(path.name for path in sealed))
        return sealed


# ── Convenience function ─────────────────────────────────────────────────


def embed_steganography(
    input_pdf: Path,
    output_pdf: Path | None = None,
    config: SteganographyConfig | None = None,
    title: str = "",
    authors: list[str] | None = None,
    keywords: list[str] | None = None,
    author_emails: list[str] | None = None,
) -> Path:
    """Convenience function — create a processor and run it.

    Usage::

        from infrastructure.steganography import embed_steganography
        embed_steganography(Path("paper.pdf"), title="My Paper")

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
