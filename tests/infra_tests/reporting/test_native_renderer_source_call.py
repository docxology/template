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

from infrastructure.reporting.native_renderer_source_call import authored_counterpart
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
