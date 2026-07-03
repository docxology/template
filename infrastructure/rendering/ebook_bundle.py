"""EbookBundleManager — orchestrates all ebook formats and metadata for a project.

This module ties together the individual rendering modules (EPUB, MOBI, DOCX) and
the metadata package generator into a single high-level ``generate_all`` call.

Usage::

    from infrastructure.rendering.ebook_bundle import EbookBundleManager
    from pathlib import Path

    manager = EbookBundleManager()
    outputs = manager.generate_all(
        project_root=Path("projects/my_book"),
        combined_md=Path("projects/my_book/output/combined.md"),
        output_dir=Path("projects/my_book/output/ebook"),
        bibliography=Path("projects/my_book/manuscript/references.bib"),
        cover_image=Path("projects/my_book/manuscript/cover.png"),
    )
    # outputs == {
    #     "epub":          Path(".../output/ebook/book.epub"),
    #     "mobi":          Path(".../output/ebook/book.mobi"),
    #     "docx":          Path(".../output/ebook/book.docx"),
    #     "onix_xml":      Path(".../output/ebook/metadata/onix.xml"),
    #     "metadata_json": Path(".../output/ebook/metadata/metadata.json"),
    #     "opf":           Path(".../output/ebook/metadata/package.opf"),
    # }
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.metadata_package import (
    PublicationMetadata,
    generate_metadata_package,
)
from infrastructure.rendering.docx_renderer import render_docx
from infrastructure.rendering.epub_renderer import render_epub
from infrastructure.rendering.mobi_renderer import render_mobi

logger = get_logger(__name__)


# ── Result dataclass ───────────────────────────────────────────────────────────


@dataclass
class EbookBundleResult:
    """Outcome of a full ebook bundle generation run.

    Attributes:
        outputs: Mapping of format key → output :class:`~pathlib.Path`.
            Keys present depend on which formats succeeded.
        errors: Mapping of format key → error message for any formats that
            failed (missing binary, conversion error, etc.).
        duration_seconds: Total wall-clock time for the entire bundle.
    """

    outputs: dict[str, Path] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    duration_seconds: float = 0.0

    @property
    def ok(self) -> bool:
        """True if at least one format was produced without errors."""
        return bool(self.outputs)

    @property
    def all_succeeded(self) -> bool:
        """True if every requested format succeeded."""
        return not self.errors


# ── Auto-discovery helpers ────────────────────────────────────────────────────


def _find_combined_markdown(project_root: Path) -> Path | None:
    """Find a combined markdown file in the project's output tree."""
    output_dir = project_root / "output"
    candidates = [
        output_dir / "combined.md",
        output_dir / "manuscript_combined.md",
    ]
    candidates.extend(sorted(output_dir.rglob("*_combined.md")))
    candidates.extend(sorted(output_dir.rglob("combined*.md")))
    for c in candidates:
        if c.is_file():
            return c
    return None


def _find_cover_image(project_root: Path) -> Path | None:
    """Look for a cover image in standard manuscript locations."""
    candidates = [
        project_root / "manuscript" / "cover.png",
        project_root / "manuscript" / "cover.jpg",
        project_root / "manuscript" / "assets" / "cover.png",
        project_root / "manuscript" / "assets" / "cover.jpg",
        project_root / "output" / "figures" / "cover.png",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _read_config_metadata(project_root: Path) -> dict[str, Any] | None:
    """Read basic metadata from manuscript/config.yaml."""
    try:
        import yaml
    except ImportError:
        return None

    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return None
    try:
        with open(config_path, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            return loaded if isinstance(loaded, dict) else None
    except Exception:  # noqa: BLE001
        return None


def _metadata_from_config(config: dict[str, Any], project_root: Path) -> PublicationMetadata:
    """Construct a PublicationMetadata from manuscript/config.yaml contents."""
    paper = config.get("paper") or {}
    authors_raw = config.get("authors") or []
    publication = config.get("publication") or {}
    metadata = config.get("metadata") or {}
    keywords_raw = config.get("keywords") or []

    authors_list = []
    for a in authors_raw:
        entry: dict[str, str] = {"name": a.get("name", "Unknown Author")}
        if a.get("orcid"):
            entry["orcid"] = a["orcid"]
        if a.get("email"):
            entry["email"] = a["email"]
        authors_list.append(entry)

    price_raw = publication.get("price") or {}
    price: dict[str, object] = {}
    if isinstance(price_raw, dict) and "amount" in price_raw:
        price = {"amount": price_raw["amount"], "currency": price_raw.get("currency", "USD")}

    return PublicationMetadata(
        title=paper.get("title", project_root.name),
        subtitle=paper.get("subtitle", ""),
        authors=authors_list,
        doi=publication.get("doi", ""),
        isbn=publication.get("isbn", ""),
        publication_date=publication.get("date", ""),
        publisher=publication.get("publisher", metadata.get("publisher", "")),
        description=paper.get("description", ""),
        keywords=[str(k).strip() for k in keywords_raw if k],
        language=metadata.get("language", "en"),
        license=metadata.get("license", ""),
        price=price,
        page_count=publication.get("page_count", 0),
    )


# ── Manager ───────────────────────────────────────────────────────────────────


@dataclass
class EbookBundleManager:
    """Orchestrates multi-format ebook generation and metadata packaging.

    Each format failure is isolated: a missing calibre binary skips MOBI but
    still produces EPUB and DOCX.  Format errors are collected in
    :attr:`EbookBundleResult.errors` rather than raising.

    Attributes:
        pandoc_path: pandoc binary name or full path (default ``"pandoc"``).
        calibre_path: calibre ebook-convert binary (default
            ``"ebook-convert"``).
        skip_mobi: When ``True``, MOBI generation is skipped entirely (useful
            when calibre is not available in the environment).
        skip_docx: When ``True``, DOCX generation is skipped.
        extra_epub_args: Extra command-line args forwarded to pandoc for EPUB.
        extra_mobi_args: Extra command-line args forwarded to ebook-convert.
        extra_docx_args: Extra command-line args forwarded to pandoc for DOCX.
    """

    pandoc_path: str = "pandoc"
    calibre_path: str = "ebook-convert"
    skip_mobi: bool = False
    skip_docx: bool = False
    extra_epub_args: list[str] = field(default_factory=list)
    extra_mobi_args: list[str] = field(default_factory=list)
    extra_docx_args: list[str] = field(default_factory=list)

    def generate_all(
        self,
        project_root: Path,
        combined_md: Path,
        output_dir: Path,
        *,
        bibliography: Path | None = None,
        cover_image: Path | None = None,
        publication_metadata: PublicationMetadata | None = None,
    ) -> dict[str, Path]:
        """Generate EPUB, MOBI, DOCX, and metadata package for *project_root*.

        Format failures are non-fatal: each format is attempted independently.
        MOBI is silently skipped when calibre is unavailable unless
        :attr:`skip_mobi` is ``False`` (default behaviour logs a warning
        instead of raising).

        Args:
            project_root: Root directory of the project (used for stem naming
                and metadata discovery).
            combined_md: Combined-manuscript markdown file to render from.
            output_dir: Directory where all ebook artefacts are written.
            bibliography: Optional ``.bib`` file.
            cover_image: Optional cover image path. Auto-discovered from
                standard manuscript locations when ``None``.
            publication_metadata: Optional pre-built
                :class:`~infrastructure.publishing.metadata_package.PublicationMetadata`
                instance. When ``None`` a metadata object is derived from
                ``manuscript/config.yaml`` if present, else from the project
                directory name.

        Returns:
            Dict mapping format keys (``"epub"``, ``"mobi"``, ``"docx"``,
            ``"onix_xml"``, ``"metadata_json"``, ``"opf"``) to written
            :class:`~pathlib.Path` objects.  Missing keys indicate formats
            that failed or were skipped.

        Raises:
            FileNotFoundError: *combined_md* does not exist.
        """
        if not combined_md.is_file():
            raise FileNotFoundError(f"Combined markdown not found: {combined_md}")

        output_dir.mkdir(parents=True, exist_ok=True)
        stem = project_root.name or combined_md.stem
        outputs: dict[str, Path] = {}
        start = time.monotonic()

        # Auto-discover cover image if not supplied
        resolved_cover = cover_image or _find_cover_image(project_root)

        logger.info("EbookBundleManager: generating all formats for %r", stem)

        # ── EPUB ──────────────────────────────────────────────────────────────
        epub_path = output_dir / f"{stem}.epub"
        try:
            epub_result = render_epub(
                combined_md,
                epub_path,
                bibliography=bibliography,
                cover_image=resolved_cover,
                pandoc_path=self.pandoc_path,
                extra_args=self.extra_epub_args or None,
            )
            outputs["epub"] = epub_result.output_path
        except (RenderingError, FileNotFoundError) as exc:
            logger.warning("  EPUB generation failed: %s", exc)

        # ── MOBI ──────────────────────────────────────────────────────────────
        if not self.skip_mobi:
            mobi_path = output_dir / f"{stem}.mobi"
            try:
                mobi_result = render_mobi(
                    combined_md,
                    mobi_path,
                    bibliography=bibliography,
                    cover_image=resolved_cover,
                    pandoc_path=self.pandoc_path,
                    calibre_path=self.calibre_path,
                    extra_args=self.extra_mobi_args or None,
                )
                outputs["mobi"] = mobi_result.output_path
            except (RenderingError, FileNotFoundError) as exc:
                logger.warning("  MOBI generation failed (calibre may not be installed): %s", exc)
        else:
            logger.debug("  MOBI generation skipped (skip_mobi=True)")

        # ── DOCX ──────────────────────────────────────────────────────────────
        if not self.skip_docx:
            docx_path = output_dir / f"{stem}.docx"
            try:
                docx_result = render_docx(
                    combined_md,
                    docx_path,
                    bibliography=bibliography,
                    pandoc_path=self.pandoc_path,
                    extra_args=self.extra_docx_args or None,
                )
                outputs["docx"] = docx_result.output_path
            except (RenderingError, FileNotFoundError) as exc:
                logger.warning("  DOCX generation failed: %s", exc)
        else:
            logger.debug("  DOCX generation skipped (skip_docx=True)")

        # ── Metadata package ──────────────────────────────────────────────────
        if publication_metadata is not None:
            meta = publication_metadata
        else:
            config = _read_config_metadata(project_root)
            meta = _metadata_from_config(config, project_root) if config else _minimal_metadata(stem)

        metadata_dir = output_dir / "metadata"
        try:
            meta_paths = generate_metadata_package(meta, output_dir=metadata_dir)
            outputs.update(meta_paths)
        except Exception as exc:  # noqa: BLE001
            logger.warning("  Metadata package generation failed: %s", exc)

        duration = time.monotonic() - start
        logger.info(
            "EbookBundleManager done in %.1fs — produced: %s",
            duration,
            ", ".join(sorted(outputs)) or "none",
        )

        return dict(outputs)

    def generate_from_project(
        self,
        project_root: Path,
        output_dir: Path | None = None,
        *,
        bibliography: Path | None = None,
        cover_image: Path | None = None,
        publication_metadata: PublicationMetadata | None = None,
    ) -> dict[str, Path]:
        """Convenience wrapper that auto-discovers *combined_md* from the project tree.

        Searches ``project_root/output/`` for a combined markdown file before
        calling :meth:`generate_all`.

        Args:
            project_root: Root directory of the project.
            output_dir: Output directory; defaults to
                ``project_root/output/ebook/``.
            bibliography: Optional ``.bib`` file.
            cover_image: Optional cover image; auto-discovered if ``None``.
            publication_metadata: Optional pre-built metadata.

        Returns:
            Same mapping as :meth:`generate_all`.  Returns an empty dict when
            no combined markdown is found (logs a warning instead of raising).
        """
        combined_md = _find_combined_markdown(project_root)
        if combined_md is None:
            logger.warning(
                "EbookBundleManager: no combined markdown found in %s — run PDF rendering first to produce combined.md",
                project_root,
            )
            return {}

        out = output_dir or (project_root / "output" / "ebook")
        return self.generate_all(
            project_root,
            combined_md,
            out,
            bibliography=bibliography,
            cover_image=cover_image,
            publication_metadata=publication_metadata,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _minimal_metadata(stem: str) -> PublicationMetadata:
    """Build a bare-minimum PublicationMetadata from a project stem name."""
    return PublicationMetadata(
        title=stem.replace("_", " ").replace("-", " ").title(),
    )


__all__ = ["EbookBundleManager", "EbookBundleResult"]
