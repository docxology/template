"""Confined local-raster inspection for accessible slide composition."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
from typing import BinaryIO
from urllib.parse import unquote, urlsplit
import warnings

from PIL import Image

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import density_error


MAX_INTRINSIC_IMAGE_BYTES = 128 * 1024 * 1024
MAX_INTRINSIC_IMAGE_PIXELS = 100_000_000
MAX_IMAGE_TARGET_CHARACTERS = 4_096
INSPECTABLE_RASTER_SUFFIXES = frozenset({".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"})

_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_FILE_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)


@dataclass(frozen=True)
class IntrinsicImageGeometry:
    """Validated intrinsic raster dimensions."""

    width: int
    height: int

    @property
    def aspect(self) -> float:
        return self.width / self.height


@dataclass(frozen=True)
class _ResolvedLocalImage:
    """A lexical target confined to one caller-authorized directory."""

    path: Path
    root: Path


def _lexical_absolute(path: Path) -> Path:
    """Return an absolute normalized path without following symlinks."""

    return Path(os.path.abspath(os.fspath(path)))


def _ordered_authorized_roots(declared_roots: tuple[Path, ...]) -> tuple[Path, ...]:
    """Canonicalize only caller-declared resource roots, preserving order."""

    roots: list[Path] = []
    for raw_root in declared_roots:
        # A lifecycle checkout may deliberately expose its manuscript through
        # one declared symlink. Resolve that authority once; symlinks beneath
        # the canonical root remain forbidden during target traversal.
        root = _lexical_absolute(raw_root).resolve(strict=False)
        if root not in roots:
            roots.append(root)
    return tuple(roots)


def _containing_roots(path: Path, roots: tuple[Path, ...]) -> tuple[Path, ...]:
    containing: list[Path] = []
    for root in roots:
        try:
            path.relative_to(root)
        except ValueError:
            continue
        containing.append(root)
    return tuple(sorted(containing, key=lambda item: len(item.parts), reverse=True))


def _first_symlink_component(path: Path, *, root: Path) -> Path | None:
    """Return the first existing symlink beneath a canonical declared root."""

    absolute = _lexical_absolute(path)
    relative = absolute.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return None
        if stat.S_ISLNK(mode):
            return current
    return None


def _unsafe_path_error(
    message: str,
    *,
    source: str,
    heading: str,
    target: str,
    **context: object,
) -> RenderingError:
    return density_error(
        "slides.security.figure-path",
        message,
        source=source,
        heading=heading,
        figure_target=target,
        **context,
    )


def _decoded_target_path(target: str, *, source: str, heading: str) -> str | None:
    if len(target) > MAX_IMAGE_TARGET_CHARACTERS:
        raise _unsafe_path_error(
            "a local figure target exceeds the path-length limit",
            source=source,
            heading=heading,
            target=target[:160] + "...",
            maximum_characters=MAX_IMAGE_TARGET_CHARACTERS,
        )
    try:
        parsed = urlsplit(target)
    except ValueError as exc:
        raise _unsafe_path_error(
            "a local figure target is not a valid path or URL",
            source=source,
            heading=heading,
            target=target,
            error_type=type(exc).__name__,
        ) from exc

    # Parse the scheme before the protocol-relative branch: ``file://host``
    # carries a netloc too, but remains a local-file authority and must never
    # be passed through as a remote resource. Scheme-relative web URLs are
    # remote resources, not absolute local paths. Parsing before decoding also
    # keeps percent-encoded '#' and '?' as filename data rather than URL
    # delimiters.
    if parsed.scheme.casefold() == "file":
        raise _unsafe_path_error(
            "absolute local figure URLs are forbidden",
            source=source,
            heading=heading,
            target=target,
        )
    if parsed.netloc and not parsed.scheme:
        return None
    decoded_target = unquote(target)
    raw_windows = PureWindowsPath(decoded_target)
    if raw_windows.is_absolute() or bool(raw_windows.drive):
        raise _unsafe_path_error(
            "absolute and encoded-absolute local figure targets are forbidden",
            source=source,
            heading=heading,
            target=target,
        )
    if parsed.scheme or parsed.netloc:
        return None
    decoded = unquote(parsed.path)
    if "\x00" in decoded:
        raise _unsafe_path_error(
            "a local figure target contains a null byte",
            source=source,
            heading=heading,
            target=target,
        )
    posix = PurePosixPath(decoded)
    windows = PureWindowsPath(decoded)
    if posix.is_absolute() or windows.is_absolute() or bool(windows.drive):
        raise _unsafe_path_error(
            "absolute and encoded-absolute local figure targets are forbidden",
            source=source,
            heading=heading,
            target=target,
        )
    if "\\" in decoded:
        raise _unsafe_path_error(
            "backslash-separated local figure targets are forbidden",
            source=source,
            heading=heading,
            target=target,
        )
    return decoded or None


def _resource_relative_targets(path_text: str) -> tuple[Path, ...]:
    """Mirror the renderer's declared figure-resource aliases safely."""

    paths = [Path(path_text)]
    for prefix in ("../output/figures/", "output/figures/", "../figures/", "./figures/"):
        if path_text.startswith(prefix):
            alias = Path(path_text[len(prefix) :])
            if alias not in paths:
                paths.append(alias)
            break
    return tuple(paths)


def _figure_alias_target(path_text: str) -> Path | None:
    """Return the payload of an explicit figure-resource alias."""

    for prefix in ("../output/figures/", "output/figures/", "../figures/", "./figures/"):
        if path_text.startswith(prefix):
            return Path(path_text[len(prefix) :])
    return None


def _resolve_local_image(
    target: str,
    *,
    source: str,
    heading: str,
    authorized_roots: tuple[Path, ...],
    figure_root: Path | None = None,
) -> _ResolvedLocalImage | None:
    path_text = _decoded_target_path(target, source=source, heading=heading)
    if path_text is None:
        return None
    roots = _ordered_authorized_roots(authorized_roots)
    if not roots:
        return None
    alias = _figure_alias_target(path_text)
    if alias is not None and figure_root is not None:
        canonical_figure_root = _ordered_authorized_roots((figure_root,))[0]
        if canonical_figure_root not in roots:
            raise _unsafe_path_error(
                "the declared figure root is outside the authorized image roots",
                source=source,
                heading=heading,
                target=target,
            )
        candidate = _lexical_absolute(canonical_figure_root / alias)
        if not _containing_roots(candidate, (canonical_figure_root,)):
            raise _unsafe_path_error(
                "a figure-resource alias escapes the declared figure root",
                source=source,
                heading=heading,
                target=target,
            )
        if symlink := _first_symlink_component(candidate, root=canonical_figure_root):
            raise _unsafe_path_error(
                "a local figure target contains a symlink component",
                source=source,
                heading=heading,
                target=target,
                symlink_component=str(symlink),
            )
        return _ResolvedLocalImage(path=candidate, root=canonical_figure_root) if candidate.exists() else None
    admitted_candidate = False
    for search_root in roots:
        for relative_target in _resource_relative_targets(path_text):
            candidate = _lexical_absolute(search_root / relative_target)
            containing = _containing_roots(candidate, roots)
            if not containing:
                continue
            admitted_candidate = True
            selected_root = containing[0]
            if symlink := _first_symlink_component(candidate, root=selected_root):
                raise _unsafe_path_error(
                    "a local figure target contains a symlink component",
                    source=source,
                    heading=heading,
                    target=target,
                    symlink_component=str(symlink),
                )
            if candidate.exists():
                return _ResolvedLocalImage(path=candidate, root=selected_root)
    if admitted_candidate:
        return None
    raise _unsafe_path_error(
        "a local figure target escapes every authorized image root",
        source=source,
        heading=heading,
        target=target,
        authorized_roots=[str(root) for root in roots],
    )


def _open_confined_posix(image: _ResolvedLocalImage) -> BinaryIO:
    relative = image.path.relative_to(image.root)
    if not relative.parts:
        raise OSError("local image target does not name a file")
    opened: list[int] = []
    try:
        current = os.open(image.root, _DIRECTORY_FLAGS)
        opened.append(current)
        for part in relative.parts[:-1]:
            current = os.open(part, _DIRECTORY_FLAGS, dir_fd=current)
            opened.append(current)
        file_descriptor = os.open(relative.parts[-1], _FILE_FLAGS, dir_fd=current)
    except BaseException:
        for descriptor in reversed(opened):
            with suppress(OSError):
                os.close(descriptor)
        raise
    for descriptor in reversed(opened):
        with suppress(OSError):
            os.close(descriptor)
    return os.fdopen(file_descriptor, "rb")


def _open_confined_fallback(image: _ResolvedLocalImage) -> BinaryIO:
    """Open with pre/post identity checks where descriptor walking is absent."""

    if symlink := _first_symlink_component(image.path, root=image.root):
        raise OSError(f"symlink component is forbidden: {symlink}")
    before = image.path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise OSError("local image target is not a regular file")
    handle = image.path.open("rb")
    try:
        opened = os.fstat(handle.fileno())
        after = image.path.lstat()
        identity = (opened.st_dev, opened.st_ino)
        if (
            stat.S_ISLNK(after.st_mode)
            or identity != (before.st_dev, before.st_ino)
            or identity
            != (
                after.st_dev,
                after.st_ino,
            )
        ):
            raise OSError("local image path changed during confined open")
        resolved = image.path.resolve(strict=True)
        resolved.relative_to(image.root.resolve(strict=True))
    except BaseException:
        handle.close()
        raise
    return handle


def _open_confined_image(image: _ResolvedLocalImage) -> BinaryIO:
    if (
        os.name == "posix"
        and os.open in os.supports_dir_fd
        and bool(getattr(os, "O_DIRECTORY", 0))
        and bool(getattr(os, "O_NOFOLLOW", 0))
    ):
        return _open_confined_posix(image)
    return _open_confined_fallback(image)  # pragma: no cover - platform fallback


def inspect_intrinsic_image_geometry(
    target: str,
    *,
    source: str,
    heading: str,
    authorized_roots: tuple[Path, ...],
    figure_root: Path | None = None,
) -> IntrinsicImageGeometry | None:
    """Return bounded raster geometry only from a confined regular file."""

    resolved = _resolve_local_image(
        target,
        source=source,
        heading=heading,
        authorized_roots=authorized_roots,
        figure_root=figure_root,
    )
    if resolved is None or resolved.path.suffix.casefold() not in INSPECTABLE_RASTER_SUFFIXES:
        return None
    try:
        with _open_confined_image(resolved) as handle:
            metadata = os.fstat(handle.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError("not a regular file")
            if metadata.st_size > MAX_INTRINSIC_IMAGE_BYTES:
                raise density_error(
                    "slides.security.figure-resource",
                    "a local figure exceeds the intrinsic-metadata byte limit",
                    source=source,
                    heading=heading,
                    figure_target=target,
                    observed_bytes=metadata.st_size,
                    maximum_bytes=MAX_INTRINSIC_IMAGE_BYTES,
                )
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(
                    handle,
                    formats=("AVIF", "BMP", "GIF", "JPEG", "PNG", "TIFF", "WEBP"),
                ) as raster:
                    width, height = raster.size
    except RenderingError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise density_error(
            "slides.security.figure-resource",
            "a local figure exceeds Pillow's safe intrinsic pixel-area limit",
            source=source,
            heading=heading,
            figure_target=target,
            maximum_pixels=MAX_INTRINSIC_IMAGE_PIXELS,
            error_type=type(exc).__name__,
        ) from exc
    except (OSError, ValueError) as exc:
        raise density_error(
            "slides.density.figure-area",
            "a locally resolvable figure has unreadable intrinsic geometry",
            source=source,
            heading=heading,
            figure_target=target,
            error_type=type(exc).__name__,
        ) from exc
    if width <= 0 or height <= 0 or width * height > MAX_INTRINSIC_IMAGE_PIXELS:
        raise density_error(
            "slides.security.figure-resource",
            "a local figure exceeds the intrinsic pixel-area limit",
            source=source,
            heading=heading,
            figure_target=target,
            intrinsic_width=width,
            intrinsic_height=height,
            maximum_pixels=MAX_INTRINSIC_IMAGE_PIXELS,
        )
    return IntrinsicImageGeometry(width=width, height=height)


def validate_local_image_target(
    target: str,
    *,
    source: str,
    heading: str,
    authorized_roots: tuple[Path, ...],
    figure_root: Path | None = None,
) -> None:
    """Validate one writer-bound image target without opening its resource.

    Intrinsic inspection is a figure-layout concern, but Pandoc may also carry
    images in headings or metadata. Those targets still cross the same writer
    boundary and therefore receive identical absolute-path, containment, and
    symlink checks even when no projected figure needs Pillow geometry.
    """

    _resolve_local_image(
        target,
        source=source,
        heading=heading,
        authorized_roots=authorized_roots,
        figure_root=figure_root,
    )


__all__ = [
    "IntrinsicImageGeometry",
    "inspect_intrinsic_image_geometry",
    "validate_local_image_target",
]
