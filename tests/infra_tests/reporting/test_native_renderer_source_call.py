"""The native renderer maps each consumed input onto its authored source.

The combined renderer reads the injected ``output/manuscript`` tree while the
authored sources live under ``manuscript/``. A generated transmission bookend
exists only in the injected tree, so it has no authored counterpart to compare
against; every other member must exist under the authored root, and a missing
one is refused by name rather than surfacing as a later ``FileNotFoundError``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.reporting.native_renderer_source_call import _is_sdk_lua_asset, authored_counterpart
from infrastructure.transmission.transmission_bookends import BEGIN_FILENAME


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    authored = tmp_path / "projects" / "templates" / "template_code_project" / "manuscript"
    consumed = tmp_path / "projects" / "templates" / "template_code_project" / "output" / "manuscript"
    authored.mkdir(parents=True)
    consumed.mkdir(parents=True)
    return authored, consumed


def test_a_generated_bookend_without_an_authored_counterpart_is_render_only(tmp_path: Path) -> None:
    """A bookend present only in the injected tree is a render input, not a source."""
    authored, consumed = _roots(tmp_path)
    bookend = consumed / BEGIN_FILENAME
    bookend.write_text("# Transmission\n", encoding="utf-8")

    assert authored_counterpart(bookend, authored_root=authored, consumed_root=consumed) is None


def test_a_generated_bookend_with_an_authored_counterpart_is_still_compared(tmp_path: Path) -> None:
    """An authored copy of a bookend name is compared, never exempted."""
    authored, consumed = _roots(tmp_path)
    bookend = consumed / BEGIN_FILENAME
    bookend.write_text("# Generated\n", encoding="utf-8")
    authored_bookend = authored / BEGIN_FILENAME
    authored_bookend.write_text("# Authored\n", encoding="utf-8")

    assert authored_counterpart(bookend, authored_root=authored, consumed_root=consumed) == authored_bookend


def test_a_missing_authored_member_is_refused_by_name(tmp_path: Path) -> None:
    """A non-generated member absent from the authored root names both roots."""
    authored, consumed = _roots(tmp_path)
    member = consumed / "10_body.md"
    member.write_text("# Body\n", encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        authored_counterpart(member, authored_root=authored, consumed_root=consumed)

    message = str(excinfo.value)
    assert "10_body.md" in message
    assert str(authored) in message
    assert str(consumed) in message


def test_a_generated_bookend_absent_from_its_consumed_root_is_refused(tmp_path: Path) -> None:
    """A bookend that exists nowhere is a named refusal, not a custody read."""
    authored, consumed = _roots(tmp_path)
    absent = consumed / BEGIN_FILENAME

    with pytest.raises(ValueError) as excinfo:
        authored_counterpart(absent, authored_root=authored, consumed_root=consumed)

    assert BEGIN_FILENAME in str(excinfo.value)


RENDERING_DIRECTORY = Path(__file__).resolve().parents[3] / "infrastructure" / "rendering"


def test_every_shipped_rendering_lua_asset_is_accepted() -> None:
    """The custody verifier and the shipped assets must agree.

    This is the invariant behind hosted run 41940842593. The previous check named
    two files while six ship, and four call sites pass a filter the check refused:

      _slides_beamer.py:195          _beamer_allowframebreaks.lua
      _slides_beamer.py:200          _table_header_breaks.lua
      _slides_beamer.py:220          _archive_figure_frames.lua
      combined_native_commands.py:92 _table_header_breaks.lua
      office_native_projection.py:21 office_semantics.lua

    So `template_newspaper` and `template_data_descriptor` failed a combined-PDF
    render with "native renderer external operand is not a fixed Source Lua asset"
    for a filter the repository itself ships.

    Asserting over the directory means the next filter added to
    `infrastructure/rendering/` fails CI here rather than in an acceptance run.
    """
    shipped = sorted(RENDERING_DIRECTORY.glob("*.lua"))
    assert shipped, "infrastructure/rendering ships no Lua assets; this test would be vacuous"
    refused = [path.name for path in shipped if not _is_sdk_lua_asset(f"rendering/{path.name}")]
    assert refused == [], (
        "the renderer custody check refuses Lua assets this repository ships: "
        f"{refused}. The predicate is structural (`rendering/<name>.lua`), so a "
        "refusal here means the file is outside that directory or not a `.lua`."
    )


@pytest.mark.parametrize(
    "member",
    [
        "rendering/nested/formalism.lua",
        "rendering/../secret.lua",
        "rendering/formalism.txt",
        "reporting/formalism.lua",
        "rendering/formalism.lua.py",
        "/rendering/formalism.lua",
        "rendering",
        "formalism.lua",
        "./rendering/formalism.lua",
        "rendering//formalism.lua",
        "rendering/FORMALISM.LUA",
    ],
)
def test_a_member_that_is_not_a_shipped_rendering_lua_asset_is_refused(member: str) -> None:
    """The structural rule narrows to exactly `rendering/<name>.lua` and nothing else.

    A derivation that accepted any path would be weaker than the enumeration it
    replaced, so these are the controls that keep it a narrowing: nested paths,
    traversal, a wrong extension, another directory, an absolute path, the
    directory itself, a bare name, a non-canonical form and a case variant.
    """
    assert not _is_sdk_lua_asset(member)


def test_the_renderer_custody_check_consults_the_structural_predicate() -> None:
    """The shipped-asset invariant is worthless if the enforcement site ignores it.

    An earlier version of the test above asserted only that `_is_sdk_lua_asset`
    accepts every shipped filter. Restoring the old two-name enumeration at the
    enforcement site left that test passing, because the predicate still existed
    and merely stopped being consulted. This pins the wiring: the external-operand
    branch must call the predicate, and no literal member enumeration may serve as
    the check.

    Negative control: reinstate
    `if sdk_member not in {"rendering/formalism.lua", ...}:` at the call site and
    this test fails while the module still imports cleanly.
    """
    import inspect

    from infrastructure.reporting import native_renderer_source_call

    source = inspect.getsource(native_renderer_source_call)
    assert "_is_sdk_lua_asset(sdk_member)" in source, (
        "the renderer custody check no longer consults the structural predicate; "
        "a literal allowlist will refuse Lua assets the repository ships"
    )
    assert 'sdk_member not in {"' not in source, (
        "the renderer custody check is back to a literal member enumeration; "
        "every new filter in infrastructure/rendering/ would be refused"
    )
