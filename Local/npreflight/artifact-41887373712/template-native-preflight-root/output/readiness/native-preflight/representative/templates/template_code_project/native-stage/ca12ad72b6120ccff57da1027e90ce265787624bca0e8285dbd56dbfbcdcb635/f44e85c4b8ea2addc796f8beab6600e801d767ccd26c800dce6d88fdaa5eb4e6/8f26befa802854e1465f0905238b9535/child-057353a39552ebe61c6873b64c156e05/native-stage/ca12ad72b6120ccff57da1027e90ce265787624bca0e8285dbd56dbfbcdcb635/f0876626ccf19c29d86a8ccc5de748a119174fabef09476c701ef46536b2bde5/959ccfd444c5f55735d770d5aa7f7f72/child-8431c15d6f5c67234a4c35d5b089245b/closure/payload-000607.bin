"""Resolution of the repo-shipped pandoc Lua filters.

Every writer that numbers cross-references — the combined PDF, the combined
HTML, DOCX, EPUB, and the opt-in ebook stage — has to apply the same filters in
the same order, or the same manuscript acquires different numbers in different
editions. Centralising the lookup here means the filter is named once; a writer
that forgets it fails the wiring test rather than silently shipping unnumbered
prose.

Ordering contract
-----------------
``formalism_filter_args()`` must be added to a pandoc command *before*
``--filter pandoc-crossref`` and before ``--citeproc``. Pandoc applies filters
in command-line order, and the formalism filter has to consume its ``[@def:x]``
citations before the citation machinery sees them (see ``formalism.lua`` for
why that matters).

Missing-filter policy
---------------------
This is deliberately stricter than the surrounding ``pandoc-crossref`` handling.
``pandoc-crossref`` is an optional external binary: a machine legitimately may
not have it, so the writers log a warning, name the install command, and carry
on. ``formalism.lua`` ships inside this package. Its absence is not a missing
optional dependency, it is a broken or partial installation of the rendering
code itself — and the failure it would cause is silent, because unnumbered
output still renders and still exits zero. So it raises instead.
"""

from __future__ import annotations

from pathlib import Path

FORMALISM_FILTER_NAME = "formalism.lua"


class FormalismFilterMissingError(RuntimeError):
    """Raised when the repo-shipped ``formalism.lua`` is not on disk.

    Deliberately a ``RuntimeError`` and not a ``RenderingError``/``OSError``:
    the combined DOCX and EPUB writers catch those two families and downgrade
    them to a logged warning, which is exactly the "degrade quietly while
    reporting success" outcome this condition must never produce.
    """


def formalism_filter_path(package_dir: Path | None = None) -> Path:
    """Return the absolute path to the shipped formalism Lua filter.

    Args:
        package_dir: Directory to search instead of this package. An injection
            seam for the missing-filter test, which points it at a real empty
            directory rather than patching module state — the same
            dependency-injection style ``render_combined_epub`` uses for its
            renderer. Production callers pass nothing.

    Raises:
        FormalismFilterMissingError: If the filter is absent from the package.
    """
    directory = package_dir if package_dir is not None else Path(__file__).parent
    path = directory / FORMALISM_FILTER_NAME
    if not path.is_file():
        raise FormalismFilterMissingError(
            f"{FORMALISM_FILTER_NAME} is missing from {path.parent}. "
            "This file ships with the repository, so its absence means a broken or "
            "partial install of infrastructure/rendering, not a missing optional tool. "
            "Rendering is refused rather than silently producing a manuscript whose "
            "Definitions and Propositions are unnumbered and whose [@def:...] "
            "references are emitted as undefined citations. "
            "Restore it with: git checkout -- "
            "infrastructure/rendering/formalism.lua"
        )
    return path


def formalism_filter_args() -> list[str]:
    """Return the pandoc arguments applying the formalism filter.

    Add these before ``--filter pandoc-crossref`` and before ``--citeproc``.

    Raises:
        FormalismFilterMissingError: If the filter is absent from the package.
    """
    return ["--lua-filter", str(formalism_filter_path())]


__all__ = [
    "FORMALISM_FILTER_NAME",
    "FormalismFilterMissingError",
    "formalism_filter_args",
    "formalism_filter_path",
]
