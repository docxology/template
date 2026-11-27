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

Cross-reference prefix registry
-------------------------------
A citation key such as ``@rem:central`` names either a bibliography entry or a
numbered block elsewhere in the manuscript. The pre-render citation validator,
the prose citation extractor and the publication audit's placeholder scan each
have to make that call, and each used to keep its own hand-written prefix list.
The lists drifted: ``formalism.lua`` numbered remarks, lemmas, corollaries,
axioms, claims and examples while the validator accepted only ``def``, ``prop``
and ``thm``, so a manuscript citing ``[@rem:x]`` was blocked before Pandoc ran
with "Undefined citation key".

``FORMALISM_KINDS`` and the ``*_PREFIXES`` tuples below are now the one list
every Python consumer reads. ``formalism.lua`` cannot import Python, and is
copied and hash-bound as a single file by the native replay lanes, so it keeps
its own ``DEFAULT_KINDS`` table;
``tests/infra_tests/rendering/test_formalism_kinds.py`` pins that table to
``FORMALISM_KINDS`` and runs real pandoc over one block of every registered
kind. Add a kind here and to the filter together, or that test fails.

Prefixes are grouped by the resolver that owns them, and the groups are
disjoint. This module imports only the standard library, so validation and
prose code can read the registry without pulling in the rendering package.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

FORMALISM_FILTER_NAME = "formalism.lua"


@dataclass(frozen=True)
class FormalismKind:
    """One block kind that ``formalism.lua`` numbers.

    Attributes:
        css_class: Fenced-Div class that marks the block, as in
            ``::: {.remark #rem:x}``.
        title: Displayed name the filter prints before the number.
        label_prefix: Conventional label prefix for the kind. The filter claims
            whatever prefix a declared label carries; this is the prefix the
            validators treat as a cross-reference rather than a bibliography key.
            Letters only, because the filter recognises a prefix with
            ``^([%a]+):``.
    """

    css_class: str
    title: str
    label_prefix: str


#: Block kinds ``formalism.lua`` numbers, in its ``DEFAULT_KINDS`` order.
FORMALISM_KINDS: tuple[FormalismKind, ...] = (
    FormalismKind("definition", "Definition", "def"),
    FormalismKind("proposition", "Proposition", "prop"),
    FormalismKind("theorem", "Theorem", "thm"),
    FormalismKind("lemma", "Lemma", "lem"),
    FormalismKind("corollary", "Corollary", "cor"),
    FormalismKind("remark", "Remark", "rem"),
    FormalismKind("axiom", "Axiom", "ax"),
    FormalismKind("claim", "Claim", "claim"),
    FormalismKind("example", "Example", "ex"),
)

#: Sections, figures, tables, equations and listings, resolved by pandoc-crossref.
PANDOC_CROSSREF_PREFIXES: tuple[str, ...] = ("sec", "fig", "tbl", "eq", "lst")

#: Label prefixes of the ``formalism.lua`` kinds.
FORMALISM_LABEL_PREFIXES: tuple[str, ...] = tuple(kind.label_prefix for kind in FORMALISM_KINDS)

#: Invariants, conjectures and algorithms. Neither pandoc-crossref nor
#: ``formalism.lua`` numbers these; manuscripts resolve them through their own
#: environments or generated registries. The citation validator accepted them
#: before this registry existed, and they stay accepted so those manuscripts keep
#: validating.
EXTERNAL_RESOLVER_PREFIXES: tuple[str, ...] = ("inv", "conj", "alg")

#: Every prefix that names a cross-reference rather than a bibliography key.
CROSS_REFERENCE_PREFIXES: tuple[str, ...] = (
    PANDOC_CROSSREF_PREFIXES + FORMALISM_LABEL_PREFIXES + EXTERNAL_RESOLVER_PREFIXES
)

#: ``CROSS_REFERENCE_PREFIXES`` with the separating colon, ready for
#: ``str.startswith``. The colon is load-bearing: ``@remington1990`` is a
#: citation, ``@rem:central`` is a cross-reference.
CROSS_REFERENCE_KEY_PREFIXES: tuple[str, ...] = tuple(f"{prefix}:" for prefix in CROSS_REFERENCE_PREFIXES)


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
    "CROSS_REFERENCE_KEY_PREFIXES",
    "CROSS_REFERENCE_PREFIXES",
    "EXTERNAL_RESOLVER_PREFIXES",
    "FORMALISM_FILTER_NAME",
    "FORMALISM_KINDS",
    "FORMALISM_LABEL_PREFIXES",
    "PANDOC_CROSSREF_PREFIXES",
    "FormalismFilterMissingError",
    "FormalismKind",
    "formalism_filter_args",
    "formalism_filter_path",
]

def combined_html_lua_filters(rendering: Path, *, has_crossref: bool) -> list[Path]:
    """Select the exact ordered Lua files for combined HTML and its replays."""
    filters = [rendering / "normalize_latex_crossrefs.lua"] if has_crossref else []
    return [*filters, rendering / "convert_latex_images.lua", rendering / FORMALISM_FILTER_NAME]
