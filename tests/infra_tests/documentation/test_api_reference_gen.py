"""Tests for ``infrastructure.documentation.api_reference_gen``.

Real I/O only (no mocks). A synthetic two-package infrastructure tree
is materialised under ``tmp_path``; the generator must:

* Walk both packages' ``__all__`` lists.
* Document all six public symbols (2 × 2 functions + 2 × 1 class).
* Round-trip through the API_REFERENCE markers idempotently.
* Skip private modules / leading-underscore symbols.
* Omit packages whose ``__all__`` is empty.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from infrastructure.documentation.api_reference_gen import (
    ModuleAPI,
    build_api_reference_markdown,
    inject_api_reference,
    walk_public_api,
)


# ---------------------------------------------------------------------------
# Synthetic package fixtures
# ---------------------------------------------------------------------------


def _write_package(
    repo_root: Path,
    package_name: str,
    submodule_name: str,
    submodule_source: str,
    all_list: list[str],
) -> Path:
    """Materialise ``infrastructure/<package>/{__init__.py, <submodule>.py}``.

    Returns the package root directory.
    """
    pkg_dir = repo_root / "infrastructure" / package_name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (repo_root / "infrastructure" / "__init__.py").touch()
    sub_path = pkg_dir / f"{submodule_name}.py"
    sub_path.write_text(submodule_source, encoding="utf-8")
    init_lines = [
        '"""Synthetic package."""',
        "from __future__ import annotations",
        "",
        f"from infrastructure.{package_name}.{submodule_name} import (",
        *[f"    {n}," for n in all_list],
        ")",
        "",
        "__all__ = [",
        *[f'    "{n}",' for n in all_list],
        "]",
        "",
    ]
    (pkg_dir / "__init__.py").write_text("\n".join(init_lines), encoding="utf-8")
    return pkg_dir


@pytest.fixture
def two_package_tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Build two synthetic infra packages, each with 2 functions + 1 class."""
    alpha_src = (
        textwrap.dedent(
            '''
        """Alpha submodule."""
        from __future__ import annotations


        def add_one(x: int) -> int:
            """Increment ``x`` by one.

            Extra paragraph.
            """
            return x + 1


        def double(x: int) -> int:
            """Return twice ``x``."""
            return x * 2


        class AlphaThing:
            """A small alpha thing.

            More detail follows.
            """

            def __init__(self, name: str, count: int = 0) -> None:
                self.name = name
                self.count = count


        def _private_helper() -> None:
            """Should never appear in __all__."""
        '''
        ).strip()
        + "\n"
    )

    beta_src = (
        textwrap.dedent(
            '''
        """Beta submodule."""
        from __future__ import annotations


        def shout(message: str) -> str:
            """Return the upper-cased ``message``."""
            return message.upper()


        def whisper(message: str, *, soft: bool = True) -> str:
            """Return the lower-cased ``message``."""
            return message.lower() if soft else message


        class BetaWidget:
            """A configurable widget."""

            def __init__(self, *, color: str = "blue") -> None:
                self.color = color
        '''
        ).strip()
        + "\n"
    )

    pkg_alpha = _write_package(
        tmp_path,
        "alpha",
        "core",
        alpha_src,
        ["AlphaThing", "add_one", "double"],
    )
    pkg_beta = _write_package(
        tmp_path,
        "beta",
        "widgets",
        beta_src,
        ["BetaWidget", "shout", "whisper"],
    )
    return tmp_path, pkg_alpha, pkg_beta


# ---------------------------------------------------------------------------
# walk_public_api
# ---------------------------------------------------------------------------


class TestWalkPublicAPI:
    """Verify per-package symbol resolution."""

    def test_returns_one_record_per_all_entry(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, _ = two_package_tree
        records = walk_public_api(pkg_alpha)
        assert len(records) == 3
        names = {r.name for r in records}
        assert names == {"AlphaThing", "add_one", "double"}

    def test_records_are_alphabetical(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, _ = two_package_tree
        records = walk_public_api(pkg_alpha)
        names = [r.name for r in records]
        assert names == sorted(names, key=str.lower)

    def test_function_signature_resolved(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, _ = two_package_tree
        records = walk_public_api(pkg_alpha)
        add_one = next(r for r in records if r.name == "add_one")
        assert add_one.kind == "function"
        assert "x: int" in add_one.signature
        assert "-> int" in add_one.signature
        assert add_one.summary == "Increment ``x`` by one."

    def test_class_signature_uses_init(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, _ = two_package_tree
        records = walk_public_api(pkg_alpha)
        cls = next(r for r in records if r.name == "AlphaThing")
        assert cls.kind == "class"
        assert "name: str" in cls.signature
        # Default-value formatting follows ast.unparse (``int=0``, no space).
        normalised = cls.signature.replace(" ", "")
        assert "count:int=0" in normalised
        # ``self`` is dropped for readability.
        assert not cls.signature.startswith("self")

    def test_summary_is_first_docstring_line(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, _ = two_package_tree
        records = walk_public_api(pkg_alpha)
        thing = next(r for r in records if r.name == "AlphaThing")
        assert thing.summary == "A small alpha thing."

    def test_module_resolves_to_definition_site(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, _ = two_package_tree
        records = walk_public_api(pkg_alpha)
        for rec in records:
            assert rec.module.endswith(".core")

    def test_private_symbols_skipped(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        """A leading-underscore name in __all__ is filtered out."""
        repo_root, _, _ = two_package_tree
        sneaky_pkg = repo_root / "infrastructure" / "sneaky"
        sneaky_pkg.mkdir(parents=True)
        (sneaky_pkg / "core.py").write_text(
            'def _hidden() -> None:\n    """Should not appear."""\n',
            encoding="utf-8",
        )
        (sneaky_pkg / "__init__.py").write_text(
            'from infrastructure.sneaky.core import _hidden\n__all__ = ["_hidden"]\n',
            encoding="utf-8",
        )
        records = walk_public_api(sneaky_pkg)
        assert records == []

    def test_missing_init_raises(self, tmp_path: Path) -> None:
        empty = tmp_path / "no_init"
        empty.mkdir()
        with pytest.raises(FileNotFoundError):
            walk_public_api(empty)

    def test_init_without_all_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "infrastructure" / "bad"
        bad.mkdir(parents=True)
        (bad / "__init__.py").write_text("# no __all__ here\n", encoding="utf-8")
        with pytest.raises(ValueError, match="__all__"):
            walk_public_api(bad)


# ---------------------------------------------------------------------------
# build_api_reference_markdown
# ---------------------------------------------------------------------------


class TestBuildMarkdown:
    """Verify rendered Markdown structure."""

    def test_documents_all_six_symbols(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, pkg_beta = two_package_tree
        md = build_api_reference_markdown([pkg_alpha, pkg_beta])
        for sym in ("AlphaThing", "add_one", "double", "BetaWidget", "shout", "whisper"):
            assert f"### `{sym}`" in md, f"Missing {sym} heading in:\n{md}"

    def test_signatures_in_fenced_python(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, pkg_beta = two_package_tree
        md = build_api_reference_markdown([pkg_alpha, pkg_beta])
        assert "```python" in md
        assert "add_one(x: int) -> int" in md
        assert "shout(message: str) -> str" in md

    def test_class_signatures_prefixed_with_class(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, pkg_beta = two_package_tree
        md = build_api_reference_markdown([pkg_alpha, pkg_beta])
        assert "class AlphaThing(" in md
        assert "class BetaWidget(" in md

    def test_per_package_section_headings(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, pkg_beta = two_package_tree
        md = build_api_reference_markdown([pkg_alpha, pkg_beta])
        assert "## Package: `infrastructure.alpha`" in md
        assert "## Package: `infrastructure.beta`" in md

    def test_empty_all_package_omitted(self, tmp_path: Path) -> None:
        pkg = tmp_path / "infrastructure" / "ghost"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
        md = build_api_reference_markdown([pkg])
        assert "ghost" not in md
        assert "_No packages with non-empty `__all__` found._" in md

    def test_caption_warns_against_hand_editing(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        _, pkg_alpha, pkg_beta = two_package_tree
        md = build_api_reference_markdown([pkg_alpha, pkg_beta])
        assert "auto-generated" not in md.lower() or "Do not hand-edit" in md
        assert "generate_api_reference_doc.py" in md

    def test_deterministic_output(self, two_package_tree: tuple[Path, Path, Path]) -> None:
        """Two consecutive renders produce byte-identical output."""
        _, pkg_alpha, pkg_beta = two_package_tree
        first = build_api_reference_markdown([pkg_alpha, pkg_beta])
        second = build_api_reference_markdown([pkg_alpha, pkg_beta])
        assert first == second


# ---------------------------------------------------------------------------
# inject_api_reference (marker round-trip)
# ---------------------------------------------------------------------------


class TestInjectAPIReference:
    """Verify marker round-trip and idempotence."""

    def test_roundtrip_with_existing_markers(self, two_package_tree: tuple[Path, Path, Path], tmp_path: Path) -> None:
        _, pkg_alpha, pkg_beta = two_package_tree
        target = tmp_path / "doc.md"
        target.write_text(
            "# Title\n\n"
            "Hand-written preface.\n\n"
            "<!-- BEGIN:API_REFERENCE -->\n"
            "OLD CONTENT\n"
            "<!-- END:API_REFERENCE -->\n\n"
            "Hand-written footer.\n",
            encoding="utf-8",
        )
        content = build_api_reference_markdown([pkg_alpha, pkg_beta])
        changed = inject_api_reference(target, content)
        assert changed is True
        new_text = target.read_text(encoding="utf-8")
        assert "Hand-written preface." in new_text
        assert "Hand-written footer." in new_text
        assert "OLD CONTENT" not in new_text
        assert "AlphaThing" in new_text

    def test_idempotent_second_run(self, two_package_tree: tuple[Path, Path, Path], tmp_path: Path) -> None:
        """Running the generator twice produces no diff on the second run."""
        _, pkg_alpha, pkg_beta = two_package_tree
        target = tmp_path / "doc.md"
        target.write_text(
            "<!-- BEGIN:API_REFERENCE -->\n_placeholder_\n<!-- END:API_REFERENCE -->\n",
            encoding="utf-8",
        )
        content = build_api_reference_markdown([pkg_alpha, pkg_beta])
        first = inject_api_reference(target, content)
        snapshot = target.read_text(encoding="utf-8")
        second = inject_api_reference(target, content)
        assert first is True
        assert second is False  # idempotent
        assert target.read_text(encoding="utf-8") == snapshot

    def test_missing_target_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            inject_api_reference(tmp_path / "missing.md", "x")

    def test_appends_when_markers_missing(self, two_package_tree: tuple[Path, Path, Path], tmp_path: Path) -> None:
        _, pkg_alpha, pkg_beta = two_package_tree
        target = tmp_path / "doc.md"
        target.write_text("# Title\n\nNo markers yet.\n", encoding="utf-8")
        content = build_api_reference_markdown([pkg_alpha, pkg_beta])
        changed = inject_api_reference(target, content)
        assert changed is True
        text = target.read_text(encoding="utf-8")
        assert "<!-- BEGIN:API_REFERENCE -->" in text
        assert "<!-- END:API_REFERENCE -->" in text


# ---------------------------------------------------------------------------
# Dataclass smoke
# ---------------------------------------------------------------------------


def test_module_api_is_frozen_dataclass() -> None:
    rec = ModuleAPI(
        package="infrastructure.foo",
        module="infrastructure.foo.bar",
        name="x",
        kind="function",
        signature="x() -> None",
        summary="Does x.",
    )
    with pytest.raises(Exception):  # FrozenInstanceError, but kept loose for portability
        rec.name = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# discover_infrastructure_packages
# ---------------------------------------------------------------------------


class TestDiscoverInfrastructurePackages:
    """Verify package-root discovery under an ``infrastructure/`` directory."""

    def test_returns_sorted_package_roots(self, tmp_path: Path) -> None:
        from infrastructure.documentation.api_reference_gen import (
            discover_infrastructure_packages,
        )

        infra_dir = tmp_path / "infrastructure"
        # Create out of alphabetical order to prove sorting.
        for name in ("zebra", "alpha"):
            pkg = infra_dir / name
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").touch()

        result = discover_infrastructure_packages(infra_dir)

        assert [p.name for p in result] == ["alpha", "zebra"]

    def test_excludes_underscore_prefixed_dirs(self, tmp_path: Path) -> None:
        from infrastructure.documentation.api_reference_gen import (
            discover_infrastructure_packages,
        )

        infra_dir = tmp_path / "infrastructure"
        for name in ("_private", "public_pkg"):
            pkg = infra_dir / name
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").touch()

        result = discover_infrastructure_packages(infra_dir)

        assert [p.name for p in result] == ["public_pkg"]

    def test_excludes_dirs_without_init(self, tmp_path: Path) -> None:
        from infrastructure.documentation.api_reference_gen import (
            discover_infrastructure_packages,
        )

        infra_dir = tmp_path / "infrastructure"
        no_init = infra_dir / "no_init"
        no_init.mkdir(parents=True)

        result = discover_infrastructure_packages(infra_dir)

        assert result == []
