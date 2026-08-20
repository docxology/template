"""EPUB rendering via pandoc.

Pandoc supports EPUB natively; this module wraps the subprocess invocation and
owns deterministic, bounded effective-package identity finalization.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import subprocess
import tempfile
import time
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._epub_cover_accessibility import apply_epub_cover_accessibility
from infrastructure.rendering._epub_package_validation import (
    _CONTAINER_MEMBER,
    _CONTAINER_NAMESPACE,
    _OPF_NAMESPACE,
    _preflight_members,
    _read_xml_member,
    _resolve_reference,
    validate_epub_package,
)
from infrastructure.rendering._output_text import _process_output_text

logger = get_logger(__name__)

_TIMEOUT_SECONDS = 120
_ERROR_CONTEXT_LIMIT = 500
_FIXED_EPUB_SOURCE_DATE_EPOCH = 315532800  # 1980-01-01T00:00:00Z; ZIP's earliest timestamp.
_MAX_SUPPORTED_SOURCE_DATE_EPOCH = 253402300799  # 9999-12-31T23:59:59Z.
_MAX_ZIP_SOURCE_DATE_EPOCH = 4354819198  # 2107-12-31T23:59:58Z.
_EPUB_IDENTIFIER_ALGORITHM = "template-epub-effective-package-v2"
_EPUB_IDENTIFIER_PLACEHOLDER = "urn:uuid:00000000-0000-5000-8000-000000000000"
_DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
_NCX_NAMESPACE = "http://www.daisy.org/z3986/2005/ncx/"
_NCX_MEDIA_TYPE = "application/x-dtbncx+xml"
_XML_ID_PATTERN = re.compile(r"(?:[^\W\d]|_)[\w.-]*\Z", flags=re.UNICODE)


@dataclass(frozen=True)
class EpubRenderResult:
    """Outcome of an EPUB render."""

    output_path: Path
    size_bytes: int
    duration_seconds: float


def _truncate_error_context(stderr_text: str) -> str:
    """Return bounded stderr/stdout context for RenderingError messages."""
    stripped = stderr_text.strip()
    if not stripped:
        return "no stderr captured"
    return stripped[:_ERROR_CONTEXT_LIMIT]


def _epub_source_date_epoch() -> int:
    """Return the caller's valid epoch or EPUB's documented fixed fallback.

    EPUB determinism is an explicit-input contract: ambient Git state must not
    influence package bytes.  A caller can pin a meaningful build time through
    ``SOURCE_DATE_EPOCH``; otherwise the earliest ZIP-safe epoch is used.
    """

    raw = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if not raw:
        return _FIXED_EPUB_SOURCE_DATE_EPOCH
    try:
        epoch = int(raw)
    except ValueError:
        logger.warning(
            "Ignoring invalid SOURCE_DATE_EPOCH=%r for EPUB; using fixed epoch %d.",
            raw,
            _FIXED_EPUB_SOURCE_DATE_EPOCH,
        )
        return _FIXED_EPUB_SOURCE_DATE_EPOCH
    if not 0 <= epoch <= _MAX_SUPPORTED_SOURCE_DATE_EPOCH:
        logger.warning(
            "Ignoring out-of-range SOURCE_DATE_EPOCH=%r for EPUB; using fixed epoch %d.",
            raw,
            _FIXED_EPUB_SOURCE_DATE_EPOCH,
        )
        return _FIXED_EPUB_SOURCE_DATE_EPOCH
    return epoch


def _zip_timestamp(source_date_epoch: int) -> tuple[int, int, int, int, int, int]:
    """Convert an epoch to ZIP's bounded, two-second-resolution timestamp."""

    bounded_epoch = min(
        max(source_date_epoch, _FIXED_EPUB_SOURCE_DATE_EPOCH),
        _MAX_ZIP_SOURCE_DATE_EPOCH,
    )
    moment = datetime.fromtimestamp(bounded_epoch, tz=timezone.utc)
    return (
        moment.year,
        moment.month,
        moment.day,
        moment.hour,
        moment.minute,
        moment.second - (moment.second % 2),
    )


def _package_identity_fields(
    archive: zipfile.ZipFile,
    members: dict[str, zipfile.ZipInfo],
) -> tuple[str, str, str]:
    """Return ``(OPF member, NCX member, shared identifier)`` for one EPUB."""

    container = _read_xml_member(archive, members, _CONTAINER_MEMBER)
    package_members: list[str] = []
    for rootfile in container.findall(f".//{{{_CONTAINER_NAMESPACE}}}rootfile"):
        if rootfile.get("media-type") != "application/oebps-package+xml":
            continue
        resolved = _resolve_reference(
            rootfile.get("full-path"),
            base=PurePosixPath(),
            allow_fragment=False,
        )
        if resolved is not None:
            package_members.append(resolved)
    if len(package_members) != 1:
        raise ValueError("deterministic EPUB identity requires exactly one OPF package")

    package_member = package_members[0]
    package = _read_xml_member(archive, members, package_member)
    if package.tag != f"{{{_OPF_NAMESPACE}}}package":
        raise ValueError("deterministic EPUB identity requires a valid OPF package root")
    unique_identifier_id = package.get("unique-identifier")
    if (
        unique_identifier_id is None
        or not unique_identifier_id
        or unique_identifier_id != unique_identifier_id.strip()
        or _XML_ID_PATTERN.fullmatch(unique_identifier_id) is None
    ):
        raise ValueError("EPUB OPF unique-identifier attribute must be a valid whitespace-free XML identifier")
    identifiers = [
        element
        for element in package.findall(f".//{{{_DC_NAMESPACE}}}identifier")
        if element.get("id") == unique_identifier_id
    ]
    if len(identifiers) != 1:
        raise ValueError("EPUB OPF unique-identifier must resolve to exactly one dc:identifier")
    identifier = "".join(str(value) for value in identifiers[0].itertext())
    if not identifier or identifier != identifier.strip():
        raise ValueError("EPUB OPF package identifier must be non-empty without surrounding whitespace")

    manifest = package.find(f"{{{_OPF_NAMESPACE}}}manifest")
    if manifest is None:
        raise ValueError("deterministic EPUB identity requires an OPF manifest")
    ncx_members: list[str] = []
    for item in manifest.findall(f"{{{_OPF_NAMESPACE}}}item"):
        if item.get("media-type") != _NCX_MEDIA_TYPE:
            continue
        resolved = _resolve_reference(
            item.get("href"),
            base=PurePosixPath(package_member).parent,
            allow_fragment=False,
        )
        if resolved is not None:
            ncx_members.append(resolved)
    if len(ncx_members) != 1:
        raise ValueError("deterministic EPUB identity requires exactly one NCX document")

    ncx_member = ncx_members[0]
    ncx = _read_xml_member(archive, members, ncx_member)
    if ncx.tag != f"{{{_NCX_NAMESPACE}}}ncx":
        raise ValueError("deterministic EPUB identity requires a valid NCX document root")
    navigation_uids = [
        element.get("content")
        for element in ncx.findall(f".//{{{_NCX_NAMESPACE}}}meta")
        if element.get("name") == "dtb:uid"
    ]
    if navigation_uids != [identifier]:
        raise ValueError("EPUB OPF dc:identifier and NCX dtb:uid must agree exactly")

    identifier_bytes = identifier.encode("utf-8")
    for member_name in (package_member, ncx_member):
        if archive.read(members[member_name]).count(identifier_bytes) != 1:
            raise ValueError(f"EPUB identifier must occur exactly once in {member_name}")
    return package_member, ncx_member, identifier


def _canonical_epub_identifier(
    archive: zipfile.ZipFile,
) -> tuple[str, str, str, str]:
    """Derive the UUID from canonical effective-package member names and bytes.

    ZIP metadata and member order do not participate. The OPF/NCX identifier
    values are normalized to one stable placeholder, breaking the otherwise
    circular dependency between the package bytes and their own identifier.
    """

    infos = archive.infolist()
    members = _preflight_members(infos)
    package_member, ncx_member, current_identifier = _package_identity_fields(archive, members)
    current_bytes = current_identifier.encode("utf-8")
    placeholder_bytes = _EPUB_IDENTIFIER_PLACEHOLDER.encode("utf-8")

    digest = hashlib.sha256()
    for value in (_EPUB_IDENTIFIER_ALGORITHM.encode("utf-8"),):
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    identity_members = {package_member, ncx_member}
    for info in sorted(infos, key=lambda candidate: candidate.filename):
        name_bytes = info.filename.encode("utf-8")
        payload = b"" if info.is_dir() else archive.read(info)
        if info.filename in identity_members:
            payload = payload.replace(current_bytes, placeholder_bytes, 1)
        for value in (name_bytes, payload):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)

    seed = f"{_EPUB_IDENTIFIER_ALGORITHM}:{digest.hexdigest()}"
    expected_identifier = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, seed)}"
    return expected_identifier, current_identifier, package_member, ncx_member


def _normalize_epub_archive(
    epub_path: Path,
    *,
    source_date_epoch: int,
) -> str:
    """Atomically finalize package identity and deterministic ZIP metadata.

    Member order, compression type, comments, and permission attributes are
    retained.  In particular, Pandoc's first uncompressed ``mimetype`` member
    remains first and uncompressed as required by the EPUB container format.
    """

    if epub_path.is_symlink():
        raise ValueError(f"refusing to normalize EPUB through symlink: {epub_path}")

    original_mode = stat.S_IMODE(epub_path.stat().st_mode)
    normalized_timestamp = _zip_timestamp(source_date_epoch)
    temporary_path: Path | None = None
    try:
        with zipfile.ZipFile(epub_path, "r") as source:
            expected_identifier, current_identifier, package_member, ncx_member = _canonical_epub_identifier(source)
            if current_identifier not in {_EPUB_IDENTIFIER_PLACEHOLDER, expected_identifier}:
                raise ValueError("EPUB package identifier does not match its effective package content")
            current_bytes = current_identifier.encode("utf-8")
            expected_bytes = expected_identifier.encode("utf-8")
            identity_members = {package_member, ncx_member}
            with tempfile.NamedTemporaryFile(
                prefix=f".{epub_path.name}.",
                suffix=".tmp",
                dir=epub_path.parent,
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
            with zipfile.ZipFile(temporary_path, "w") as destination:
                destination.comment = source.comment
                for source_info in source.infolist():
                    payload = b"" if source_info.is_dir() else source.read(source_info)
                    if source_info.filename in identity_members:
                        if payload.count(current_bytes) != 1:
                            raise ValueError(f"EPUB identifier must occur exactly once in {source_info.filename}")
                        payload = payload.replace(current_bytes, expected_bytes, 1)
                    target_info = zipfile.ZipInfo(source_info.filename, normalized_timestamp)
                    target_info.compress_type = source_info.compress_type
                    target_info.comment = source_info.comment
                    target_info.create_system = source_info.create_system
                    target_info.external_attr = source_info.external_attr
                    target_info.internal_attr = source_info.internal_attr
                    destination.writestr(target_info, payload)
                    # ``ZipFile`` substitutes 0600 when external_attr is zero;
                    # restore the exact source value before it serializes the
                    # central directory at close.
                    target_info.external_attr = source_info.external_attr
        assert temporary_path is not None
        temporary_path.chmod(original_mode)
        os.replace(temporary_path, epub_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return expected_identifier


def render_epub(
    combined_md: Path,
    output_path: Path,
    *,
    bibliography: Path | None = None,
    cover_image: Path | None = None,
    cover_alt: str | None = None,
    title: str | None = None,
    author: str | None = None,
    language: str = "en",
    pandoc_path: str = "pandoc",
    extra_args: list[str] | None = None,
) -> EpubRenderResult:
    """Render *combined_md* to an EPUB at *output_path*.

    The EPUB package identifier is a deterministic UUIDv5 over the effective
    package's canonical member names and uncompressed bytes after Pandoc and
    cover-accessibility processing, with only the OPF/NCX identifier fields
    normalized out. A valid caller ``SOURCE_DATE_EPOCH`` controls Pandoc's OPF
    modification time and therefore participates in package identity; absent
    or invalid values use the fixed ZIP-safe epoch ``1980-01-01T00:00:00Z``.
    The final archive rewrite normalizes ZIP member timestamps without
    consulting ambient Git state. Pandoc writes a fresh sibling temporary file,
    so stale output cannot be accepted and caller output redirects cannot alter
    the requested destination.

    Args:
        combined_md: Combined-manuscript markdown file.
        output_path: Target .epub path; parent created if missing.
        bibliography: Optional `.bib` file. When given, --citeproc is enabled.
        cover_image: Optional cover image path (passed via --epub-cover-image).
        cover_alt: Source-owned alternative text for ``cover_image``. A cover
            image is rejected when this is missing or blank because Pandoc's
            generated SVG cover otherwise has no accessible name.
        title: Book title, passed via ``--metadata title=``. Without this
            (and without a ``title:`` YAML frontmatter field already in
            *combined_md*), pandoc emits an EPUB with no ``dc:title`` at
            all, which retailer converters (e.g. Amazon KDP) can reject
            outright rather than merely warn about.
        author: Author name, passed via ``--metadata author=``. Same
            missing-``dc:creator`` failure mode as *title* when absent.
        language: BCP-47 language tag, passed via ``--metadata lang=``.
            Defaults to "en" — without an explicit value, pandoc falls back
            to the host's locale (e.g. the POSIX "C" locale becomes the
            literal, invalid ``dc:language`` value "C").
        pandoc_path: pandoc binary (default "pandoc").
        extra_args: Extra args appended before the renderer's authoritative
            identifier placeholder. Effective changes made by these arguments
            participate in the finalized package identifier; attempts that
            mutate the placeholder identifier are rejected fail-closed.

    Returns:
        EpubRenderResult with the output path, byte size, and duration.

    Raises:
        RenderingError: pandoc missing, timed out, non-zero exit, or empty output.
        FileNotFoundError: input files do not exist.
    """
    if not combined_md.is_file():
        raise FileNotFoundError(f"Combined markdown not found: {combined_md}")
    if bibliography is not None and not bibliography.is_file():
        raise FileNotFoundError(f"Bibliography not found: {bibliography}")
    if cover_image is not None and not cover_image.is_file():
        raise FileNotFoundError(f"Cover image not found: {cover_image}")
    normalized_cover_alt = " ".join((cover_alt or "").split())
    if cover_image is not None and not normalized_cover_alt:
        raise RenderingError("EPUB cover image requires non-empty cover_alt accessibility text")
    if shutil.which(pandoc_path) is None:
        raise RenderingError(f"pandoc binary not found: {pandoc_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing_output_mode = (
        stat.S_IMODE(output_path.stat().st_mode) if output_path.is_file() and not output_path.is_symlink() else None
    )
    with tempfile.NamedTemporaryFile(
        prefix=f".{output_path.name}.",
        suffix=".rendering",
        dir=output_path.parent,
        delete=False,
    ) as handle:
        rendered_path = Path(handle.name)
    # Let Pandoc create the archive with the caller's ordinary umask. More
    # importantly, success without writing cannot inherit even an empty file.
    rendered_path.unlink()

    source_date_epoch = _epub_source_date_epoch()
    subprocess_env = dict(os.environ)
    subprocess_env["SOURCE_DATE_EPOCH"] = str(source_date_epoch)

    cmd: list[str] = [
        pandoc_path,
        "-f",
        "markdown+yaml_metadata_block",
        "-t",
        "epub",
        str(combined_md),
        "--standalone",
        f"--metadata=lang:{language}",
    ]
    if title is not None:
        cmd.append(f"--metadata=title:{title}")
    if author is not None:
        cmd.append(f"--metadata=author:{author}")
    if bibliography is not None:
        cmd.extend(["--citeproc", f"--bibliography={bibliography}"])
    if cover_image is not None:
        cmd.append(f"--epub-cover-image={cover_image}")
    if extra_args:
        cmd.extend(extra_args)
    # This must remain after arbitrary extras: source YAML and
    # arbitrary extra_args may request an identifier, but the effective-package
    # finalizer requires its stable placeholder and replaces it authoritatively.
    cmd.append(f"--metadata=identifier:{_EPUB_IDENTIFIER_PLACEHOLDER}")
    # Likewise, a caller-supplied -o/--output cannot redirect Pandoc and leave a
    # stale requested destination to be mistaken for this invocation's result.
    cmd.extend(["-o", str(rendered_path)])

    logger.debug("Invoking pandoc for EPUB: %s", " ".join(cmd))
    start = time.monotonic()
    try:
        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_SECONDS,
                env=subprocess_env,
            )
        except subprocess.TimeoutExpired as exc:
            stderr_text = _process_output_text(exc.stderr) or _process_output_text(exc.stdout) or str(exc)
            raise RenderingError(
                f"pandoc EPUB render timed out after 120s: {_truncate_error_context(stderr_text)}"
            ) from exc

        duration = time.monotonic() - start

        if result.returncode != 0:
            stderr_text = result.stderr or result.stdout or ""
            raise RenderingError(
                f"pandoc EPUB render failed (exit {result.returncode}): {_truncate_error_context(stderr_text)}"
            )
        if not rendered_path.exists():
            raise RenderingError(f"pandoc reported success but EPUB was not created: {output_path}")
        if rendered_path.stat().st_size == 0:
            raise RenderingError(f"pandoc reported success but EPUB is empty: {output_path}")

        try:
            # Explicitly enforce metadata-only archive bounds before even the
            # cover accessibility pass may inspect a member payload.
            with zipfile.ZipFile(rendered_path) as archive:
                _preflight_members(archive.infolist())
            if cover_image is not None:
                apply_epub_cover_accessibility(rendered_path, normalized_cover_alt)
            # Re-run the complete package contract after cover processing and
            # before canonicalization reads every effective-package payload.
            with zipfile.ZipFile(rendered_path) as archive:
                validate_epub_package(archive)
            finalized_identifier = _normalize_epub_archive(
                rendered_path,
                source_date_epoch=source_date_epoch,
            )
            with zipfile.ZipFile(rendered_path) as archive:
                validate_epub_package(archive)
                expected_identifier, current_identifier, _, _ = _canonical_epub_identifier(archive)
                if current_identifier != finalized_identifier or current_identifier != expected_identifier:
                    raise ValueError("EPUB finalized identifier does not match effective package content")
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            raise RenderingError(f"pandoc EPUB package failed validation or canonicalization: {exc}") from exc

        if existing_output_mode is not None:
            rendered_path.chmod(existing_output_mode)
        os.replace(rendered_path, output_path)
        size = output_path.stat().st_size
    finally:
        rendered_path.unlink(missing_ok=True)

    logger.info("  Generated EPUB: %s (%.1f KB, %.1fs)", output_path.name, size / 1024, duration)
    return EpubRenderResult(
        output_path=output_path,
        size_bytes=size,
        duration_seconds=duration,
    )


__all__ = ["EpubRenderResult", "render_epub"]
