"""Direct leg-deterministic tests for the shared support primitives.

Covers the previously-untested branches of two tiny helper modules whose
failure paths only ran when a gate happened to rebuild the tracked snapshot:

* ``json_io.load_json_strict`` -- the missing-file short circuit and the
  fail-loud ``ValueError`` raised on a present-but-malformed artifact
  (``src/json_io.py`` lines 31, 34-35), plus the non-dict fallthrough.
* ``roadmap_tracks.row_aggregates.all_field_present`` -- the whole helper
  (``src/roadmap_tracks/row_aggregates.py`` lines 26-27), including the
  negative control that forces the every-row-has-every-field claim False.

All inputs are constructed data / real temp files (no mocks); nothing touches
the git-tracked project tree.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from json_io import load_json, load_json_strict, read_json, write_json
from roadmap_tracks.row_aggregates import all_field_present, all_rows, rows


# ---------------------------------------------------------------------------
# json_io.load_json_strict -- lines 31, 34-35 and the non-dict fallthrough
# ---------------------------------------------------------------------------


def test_load_json_strict_missing_file_returns_empty(tmp_path: Path) -> None:
    """A missing artifact returns {} (line 31), mirroring load_json."""
    assert load_json_strict(tmp_path / "absent.json") == {}


def test_load_json_strict_raises_valueerror_on_malformed(tmp_path: Path) -> None:
    """A present-but-malformed artifact fails loudly (lines 34-35)."""
    bad = tmp_path / "malformed.json"
    bad.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed JSON artifact"):
        load_json_strict(bad)


def test_load_json_strict_non_dict_payload_returns_empty(tmp_path: Path) -> None:
    """A well-formed but non-object payload collapses to {} (line 36)."""
    arr = tmp_path / "list.json"
    arr.write_text("[1, 2, 3]", encoding="utf-8")
    assert load_json_strict(arr) == {}


def test_load_json_strict_returns_object(tmp_path: Path) -> None:
    """Positive control: a valid JSON object round-trips unchanged."""
    obj = tmp_path / "obj.json"
    obj.write_text('{"a": 1, "b": [2, 3]}', encoding="utf-8")
    assert load_json_strict(obj) == {"a": 1, "b": [2, 3]}


def test_load_json_swallows_malformed_where_strict_raises(tmp_path: Path) -> None:
    """Contrast: the lenient loader treats a malformed artifact as absent."""
    bad = tmp_path / "malformed.json"
    bad.write_text("{oops", encoding="utf-8")
    assert load_json(bad) == {}
    # ...while the strict variant refuses to launder it as empty.
    with pytest.raises(ValueError):
        load_json_strict(bad)


def test_write_read_json_roundtrip(tmp_path: Path) -> None:
    """write_json + read_json alias preserve payload content."""
    target = tmp_path / "nested" / "out.json"
    payload = {"z": 1, "a": {"b": 2}}
    written = write_json(target, payload)
    assert written == target and target.is_file()
    assert read_json(target) == payload


# ---------------------------------------------------------------------------
# row_aggregates.all_field_present -- lines 26-27 (whole helper)
# ---------------------------------------------------------------------------


def test_all_field_present_true_when_every_row_has_every_field() -> None:
    """Positive control: all rows carry truthy values for all fields."""
    payload = {"rows": [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]}
    assert all_field_present(payload, ("a", "b")) is True


def test_all_field_present_false_when_a_row_misses_a_field() -> None:
    """Negative control: one row missing a required field forces False."""
    payload = {"rows": [{"a": 1, "b": "x"}, {"a": 2}]}
    assert all_field_present(payload, ("a", "b")) is False


def test_all_field_present_false_when_a_field_is_falsy() -> None:
    """Negative control: a falsy value (0/"") is not "present"."""
    payload = {"rows": [{"a": 1, "b": ""}]}
    assert all_field_present(payload, ("a", "b")) is False


def test_all_field_present_false_on_empty_rows() -> None:
    """Negative control: a vacuous row set never satisfies the claim."""
    assert all_field_present({"rows": []}, ("a",)) is False
    assert all_field_present({}, ("a",)) is False


def test_all_field_present_honours_alternate_key() -> None:
    """The key override selects a different row list."""
    payload = {"edges": [{"src": 1, "dst": 2}]}
    assert all_field_present(payload, ("src", "dst"), key="edges") is True
    assert all_field_present(payload, ("src", "missing"), key="edges") is False


def test_rows_and_all_rows_ignore_non_dict_entries() -> None:
    """rows() drops non-dict entries; all_rows() needs a non-empty set."""
    payload = {"rows": [{"ok": True}, "garbage", 5, {"ok": True}]}
    assert rows(payload) == [{"ok": True}, {"ok": True}]
    assert all_rows(payload, lambda row: bool(row.get("ok"))) is True
    assert all_rows({"rows": []}, lambda row: True) is False
