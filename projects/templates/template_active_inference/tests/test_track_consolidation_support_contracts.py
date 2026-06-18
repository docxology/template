"""Contract checks for shared consolidation helper utilities."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from track_consolidation_support import (
    JsonMutation,
    VERSIONED_TRACK_RE,
    _combine_mutations,
    _drop_last_row,
    _load,
    _relative_posix,
    _set_value,
    _write,
    temporary_json_mutation,
    temporary_text_mutation,
    temporary_yaml_mutation,
)


def test_relative_posix_is_stable_for_nested_files(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    assert _relative_posix(root / "output" / "data" / "a.json", root) == "output/data/a.json"


def test_set_value_rewrites_nested_payload() -> None:
    target = {
        "outer": {
            "inner": {
                "value": 1,
            },
        },
    }
    _set_value(("outer", "inner", "value"), 2)(target)
    assert target == {"outer": {"inner": {"value": 2}}}


def test_drop_last_row_updates_count_when_requested() -> None:
    payload = {"rows": [{"ok": True}, {"ok": False}], "row_count": 2}
    _drop_last_row(update_row_count=True)(payload)
    assert payload["rows"] == [{"ok": True}]
    assert payload["row_count"] == 1


def test_combine_mutations_applies_in_order() -> None:
    payload = {"rows": [{"ok": True}], "row_count": 1}

    def clear_rows(data: dict) -> None:
        data["rows"] = []

    _combine_mutations(_set_value(("rows", 0, "ok"), False), clear_rows)(payload)
    assert payload == {"rows": [], "row_count": 1}


def test_temporary_json_mutation_restores_original_after_exception(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    original = {"rows": [{"ok": True}]}
    _write(artifact, original)

    with pytest.raises(RuntimeError, match="json restore"):
        with temporary_json_mutation(artifact, _set_value(("rows", 0, "ok"), False)):
            assert _load(artifact)["rows"][0]["ok"] is False
            raise RuntimeError("json restore")

    assert _load(artifact) == original


def test_temporary_text_and_yaml_mutation_restore_after_exception(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("alpha: keep\n", encoding="utf-8")
    yaml_path = tmp_path / "claim.yaml"
    yaml_original = "tracks:\n  prose:\n    renderer: markdown\n"
    yaml_path.write_text(yaml_original, encoding="utf-8")

    with pytest.raises(RuntimeError, match="text restore"):
        with temporary_text_mutation(note, lambda text: text.replace("keep", "break")):
            assert note.read_text(encoding="utf-8") == "alpha: break\n"
            raise RuntimeError("text restore")

    with pytest.raises(RuntimeError, match="yaml restore"):
        with temporary_yaml_mutation(yaml_path, lambda payload: payload["tracks"]["prose"].update({"renderer": "broken"})):
            assert yaml.safe_load(yaml_path.read_text(encoding="utf-8"))["tracks"]["prose"]["renderer"] == "broken"
            raise RuntimeError("yaml restore")

    assert note.read_text(encoding="utf-8") == "alpha: keep\n"
    assert yaml_path.read_text(encoding="utf-8") == yaml_original


def test_versioned_track_pattern_does_not_match_unversioned_track() -> None:
    assert not VERSIONED_TRACK_RE.search("prose")
    assert not VERSIONED_TRACK_RE.search("track_v1")
    assert VERSIONED_TRACK_RE.search("track_v2")
    assert VERSIONED_TRACK_RE.search("track_v9")
