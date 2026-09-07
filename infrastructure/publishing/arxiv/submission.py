"""Prepare a deterministic, renderer-aware LaTeX source tarball for arXiv."""

from __future__ import annotations

import gzip
import os
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.determinism import resolve_source_date_epoch
from infrastructure.core.exceptions import PublishingError
from infrastructure.publishing.models import PublicationMetadata

_SUBMISSION_DIRECTORY = "arxiv_submission"
_ARCHIVE_PATTERN = "arxiv_submission_*.tar.gz"
_CANONICAL_RENDERED_TEX = "_combined_manuscript.tex"
_SOURCE_SUFFIXES = frozenset({".bbl", ".bib", ".bst", ".cls", ".gls", ".ind", ".nls", ".sty", ".tex"})
_RENDERED_DEPENDENCY_SUFFIXES = frozenset({".bib", ".bst", ".cls", ".sty"})
_MATCHED_AUXILIARY_SUFFIXES = (".bbl", ".gls", ".ind", ".nls")
_FIGURE_SUFFIXES = frozenset({".eps", ".jpeg", ".jpg", ".pdf", ".png", ".ps"})


def _remove_generated_path(path: Path) -> None:
    """Remove one exact generated path without following a symlink."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif os.path.lexists(path):
        raise PublishingError(f"Cannot safely replace non-file arXiv artifact: {path}")


def _clean_previous_package(output_dir: Path) -> Path:
    """Remove the staging tree and every older date-named package."""
    submission_dir = output_dir / _SUBMISSION_DIRECTORY
    _remove_generated_path(submission_dir)
    for archive in sorted(output_dir.glob(_ARCHIVE_PATTERN)):
        if archive.is_dir() and not archive.is_symlink():
            raise PublishingError(f"Refusing to remove directory matching arXiv archive pattern: {archive}")
        _remove_generated_path(archive)
    return submission_dir


def _require_regular_source(path: Path) -> None:
    """Reject links and special files before they can enter a public package."""
    if path.is_symlink():
        raise PublishingError(f"arXiv source packages may not contain symlinks: {path}")
    if not path.is_file():
        raise PublishingError(f"arXiv package input is not a regular file: {path}")


def _require_nonempty_tex(path: Path) -> None:
    _require_regular_source(path)
    if path.stat().st_size == 0:
        raise PublishingError(f"arXiv TeX root is empty: {path}")


def _copy_file(source: Path, target: Path, *, content: str | None = None) -> None:
    """Copy one source, rejecting conflicting package paths."""
    _require_regular_source(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_file():
            raise PublishingError(f"Unsafe arXiv package target collision: {target}")
        candidate = content.encode("utf-8") if content is not None else source.read_bytes()
        if target.read_bytes() != candidate:
            raise PublishingError(f"Conflicting arXiv package inputs map to {target}")
        return
    if content is None:
        shutil.copy2(source, target)
    else:
        target.write_text(content, encoding="utf-8")


def _visible_tree_files(root: Path) -> tuple[Path, ...]:
    """Return sorted, non-hidden regular files, failing on any symlink."""
    if root.is_symlink():
        raise PublishingError(f"arXiv package source directory may not be a symlink: {root}")
    if not root.is_dir():
        return ()
    files: list[Path] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path.is_symlink():
            raise PublishingError(f"arXiv source packages may not contain symlinks: {path}")
        if path.is_dir():
            continue
        _require_regular_source(path)
        files.append(path)
    return tuple(files)


def _copy_figure_tree(root: Path, target_root: Path) -> None:
    for source in _visible_tree_files(root):
        if source.suffix.lower() in _FIGURE_SUFFIXES:
            _copy_file(source, target_root / source.relative_to(root))


def _rendered_tex(output_dir: Path) -> Path | None:
    """Select one rendered root deterministically, preferring the renderer contract."""
    pdf_dir = output_dir / "pdf"
    if pdf_dir.is_symlink():
        raise PublishingError(f"Rendered PDF directory may not be a symlink: {pdf_dir}")
    if not pdf_dir.is_dir():
        return None
    canonical = pdf_dir / _CANONICAL_RENDERED_TEX
    if canonical.is_symlink():
        raise PublishingError(f"Rendered TeX source may not be a symlink: {canonical}")
    if canonical.is_file():
        _require_nonempty_tex(canonical)
        return canonical
    candidates = []
    for candidate in sorted(pdf_dir.glob("*.tex")):
        _require_nonempty_tex(candidate)
        candidates.append(candidate)
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise PublishingError(
            f"Multiple rendered TeX roots found without {_CANONICAL_RENDERED_TEX}; cannot choose safely: {names}"
        )
    return candidates[0] if candidates else None


def _arxiv_rendered_tex(source: Path) -> str:
    """Adapt renderer-owned figure paths to arXiv's root compilation directory."""
    try:
        text = source.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PublishingError(f"Rendered TeX source is not UTF-8: {source}") from exc
    return text.replace("{../figures/", "{figures/")


def _copy_rendered_package(
    output_dir: Path,
    manuscript_dir: Path,
    submission_dir: Path,
    rendered_tex: Path,
) -> None:
    """Stage the canonical rendered source and only its relevant companions."""
    pdf_dir = rendered_tex.parent
    _copy_file(rendered_tex, submission_dir / rendered_tex.name, content=_arxiv_rendered_tex(rendered_tex))

    rendered_bibliographies = 0
    for source in sorted(pdf_dir.iterdir(), key=lambda item: item.name):
        if source.name.startswith(".") or source.suffix.lower() not in _RENDERED_DEPENDENCY_SUFFIXES:
            continue
        _copy_file(source, submission_dir / source.name)
        if source.suffix.lower() == ".bib":
            rendered_bibliographies += 1
    for suffix in _MATCHED_AUXILIARY_SUFFIXES:
        companion = rendered_tex.with_suffix(suffix)
        if companion.is_symlink():
            raise PublishingError(f"Rendered TeX companion may not be a symlink: {companion}")
        if companion.is_file():
            _copy_file(companion, submission_dir / companion.name)

    if manuscript_dir.is_dir():
        for source in _visible_tree_files(manuscript_dir):
            suffix = source.suffix.lower()
            if suffix in {".bst", ".cls", ".sty"} or (suffix == ".bib" and rendered_bibliographies == 0):
                _copy_file(source, submission_dir / source.relative_to(manuscript_dir))

    rendered_figures = output_dir / "figures"
    manuscript_figures = manuscript_dir / "figures"
    if rendered_figures.is_dir() or rendered_figures.is_symlink():
        _copy_figure_tree(rendered_figures, submission_dir / "figures")
    elif manuscript_figures.is_dir() or manuscript_figures.is_symlink():
        _copy_figure_tree(manuscript_figures, submission_dir / "figures")


def _copy_manuscript_package(manuscript_dir: Path, submission_dir: Path) -> int:
    """Stage a conventional manuscript source tree, preserving relative paths."""
    tex_count = 0
    for source in _visible_tree_files(manuscript_dir):
        relative = source.relative_to(manuscript_dir)
        if relative.parts and relative.parts[0] == "figures":
            continue
        if source.suffix.lower() not in _SOURCE_SUFFIXES:
            continue
        _copy_file(source, submission_dir / relative)
        tex_count += source.suffix.lower() == ".tex" and source.stat().st_size > 0
    figures = manuscript_dir / "figures"
    if figures.is_dir() or figures.is_symlink():
        _copy_figure_tree(figures, submission_dir / "figures")
    return tex_count


def _archive_epoch(output_dir: Path) -> int:
    configured_raw = os.environ.get("SOURCE_DATE_EPOCH")
    if configured_raw is not None:
        configured = configured_raw.strip()
        try:
            explicit_epoch = int(configured)
        except ValueError as exc:
            raise PublishingError("SOURCE_DATE_EPOCH must be a non-negative integer for arXiv packaging") from exc
        if explicit_epoch < 0:
            raise PublishingError("SOURCE_DATE_EPOCH must be a non-negative integer for arXiv packaging")
        return explicit_epoch
    epoch = resolve_source_date_epoch(deterministic=True, repo_root=output_dir.parent)
    resolved = epoch if epoch is not None else int(datetime.now(timezone.utc).timestamp())
    if resolved < 0:
        raise PublishingError("SOURCE_DATE_EPOCH must be a non-negative integer for arXiv packaging")
    return resolved


def _normalized_tar_info(tar: tarfile.TarFile, source: Path, arcname: str, epoch: int) -> tarfile.TarInfo:
    info = tar.gettarinfo(str(source), arcname=arcname)
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = epoch
    info.mode = 0o644
    return info


def _write_deterministic_archive(submission_dir: Path, tar_path: Path, epoch: int) -> None:
    """Write stable gzip and tar headers in lexical member order."""
    temporary = tar_path.with_name(f".{tar_path.name}.tmp")
    _remove_generated_path(temporary)
    try:
        with temporary.open("wb") as raw_file:
            gzip_mtime = epoch if epoch <= 0xFFFFFFFF else 0
            with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=raw_file, mtime=gzip_mtime) as zipped:
                with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
                    for source in _visible_tree_files(submission_dir):
                        arcname = source.relative_to(submission_dir).as_posix()
                        relative = Path(arcname)
                        if relative.is_absolute() or ".." in relative.parts:
                            raise PublishingError(f"Unsafe path in arXiv package: {arcname}")
                        info = _normalized_tar_info(archive, source, arcname, epoch)
                        with source.open("rb") as payload:
                            archive.addfile(info, payload)
        os.replace(temporary, tar_path)
    except Exception:
        _remove_generated_path(temporary)
        raise


def prepare_arxiv_submission(output_dir: Path, metadata: PublicationMetadata) -> Path:
    """Build a deterministic, non-partial LaTeX-source package for manual upload.

    The renderer-owned ``output/pdf/_combined_manuscript.tex`` is preferred. Its
    matching ``.bbl`` (rather than a title-derived filename), rendered
    bibliography dependencies, and ``output/figures/`` are staged with a flat
    top-level TeX root suitable for arXiv's root-directory compilation. If no
    rendered source exists, a conventional sibling ``manuscript/`` TeX tree is
    preserved instead.

    The function fails closed when no TeX root exists, when a rendered root is
    ambiguous, or when a source is a symlink/special file. It removes the prior
    staging directory and all older ``arxiv_submission_*.tar.gz`` files before
    building, so a failed refresh cannot leave a stale package looking current.

    Archive member order and metadata are normalized. ``SOURCE_DATE_EPOCH``
    controls both the UTC ``YYYYMMDD`` filename and tar/gzip timestamps; when it
    is unset, the repository ``HEAD`` epoch is used in deterministic mode.

    ``metadata`` remains part of the public API for compatibility and future
    upload-manifest use; package filenames are deliberately derived from the
    selected TeX root, not from the publication title.

    Raises:
        PublishingError: If a safe LaTeX source package candidate cannot be built.
    """
    del metadata
    output_dir = Path(output_dir)
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise PublishingError(f"arXiv output directory must be a real directory: {output_dir}")

    submission_dir = _clean_previous_package(output_dir)
    manuscript_dir = output_dir.parent / "manuscript"
    rendered_tex = _rendered_tex(output_dir)
    try:
        submission_dir.mkdir()
        if rendered_tex is not None:
            _copy_rendered_package(output_dir, manuscript_dir, submission_dir, rendered_tex)
        elif _copy_manuscript_package(manuscript_dir, submission_dir) == 0:
            raise PublishingError(
                "No LaTeX root found: render the manuscript so output/pdf/"
                f"{_CANONICAL_RENDERED_TEX} exists, or add a .tex source under {manuscript_dir}"
            )

        epoch = _archive_epoch(output_dir)
        date_stamp = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y%m%d")
        tar_path = output_dir / f"arxiv_submission_{date_stamp}.tar.gz"
        _write_deterministic_archive(submission_dir, tar_path, epoch)
        return tar_path
    except Exception:
        _remove_generated_path(submission_dir)
        raise
