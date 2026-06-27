"""Package build helpers (uv build / wheel / sdist).

All subprocess calls are isolated here so unit tests can stub at the
``build_dist`` boundary without touching the real filesystem.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def build_dist(
    project_root: Path,
    *,
    dist_dir: Path | None = None,
    clean: bool = True,
) -> Path:
    """Build wheel + sdist using ``uv build``.

    Parameters
    ----------
    project_root:
        Directory that contains ``pyproject.toml``.  Passed as ``cwd`` to
        ``uv build``.
    dist_dir:
        Where build artefacts are written.  Defaults to
        ``project_root / "dist"``.
    clean:
        When True (default) all existing files inside ``dist_dir`` are
        removed before building so stale artefacts cannot be accidentally
        uploaded.

    Returns
    -------
    Path
        ``dist_dir`` after a successful build.

    Raises
    ------
    RuntimeError
        If ``uv build`` exits non-zero, or if the build directory is empty
        (no ``.whl`` or ``.tar.gz`` files) after the run.
    """
    out = dist_dir if dist_dir is not None else (project_root / "dist")

    if clean and out.exists():
        for f in out.iterdir():
            if f.is_file():
                f.unlink()

    out.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["uv", "build", "--out-dir", str(out)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"uv build failed:\n{result.stderr.strip() or result.stdout.strip()}"
        )

    wheels, sdists = list_dist_files(out)
    if not wheels and not sdists:
        raise RuntimeError(
            f"uv build succeeded but produced no distribution files in {out}"
        )

    logger.info(
        "Built %d wheel(s) + %d sdist(s) in %s",
        len(wheels),
        len(sdists),
        out,
    )
    return out


def list_dist_files(dist_dir: Path) -> tuple[list[Path], list[Path]]:
    """Return ``(wheels, sdists)`` found in *dist_dir*.

    Does not raise if the directory is empty — callers decide what to do.

    Parameters
    ----------
    dist_dir:
        Directory to inspect.

    Returns
    -------
    tuple[list[Path], list[Path]]
        A 2-tuple of ``(wheels, sdists)``.  Both lists are sorted for
        deterministic ordering.
    """
    if not dist_dir.exists():
        return [], []
    wheels = sorted(dist_dir.glob("*.whl"))
    sdists = sorted(dist_dir.glob("*.tar.gz"))
    return wheels, sdists
