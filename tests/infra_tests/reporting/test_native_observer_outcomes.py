"""Release admission preserves every nested actual native failure and blocker."""

from pathlib import Path

import pytest

from infrastructure.reporting.native_format_observer_outcome import native_observer_outcome
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@pytest.mark.parametrize("kind", ["docx", "pptx"])
def test_office_nested_unsupported_source_is_preserved(kind: str) -> None:
    result = {"status": "blocked", "findings": [], "blockers": ["scientific source is unsupported"]}
    observed = {
        "format": kind,
        "observation": {"conversion": {}, "raster": {}, "observation": result, "status": "blocked"},
    }
    assert native_observer_outcome(observed) == result
    observed["observation"]["status"] = "pass"
    with pytest.raises(ValueError, match="wrapper status"):
        native_observer_outcome(observed)


def test_epub_spine_failure_cannot_be_hidden_by_successful_reader_layout() -> None:
    finding = {"code": "epub.spine.content", "ordinal": 1}
    observed = {
        "format": "epub",
        "observation": {"status": "pass", "findings": [], "blockers": []},
        "spine": {"status": "fail", "findings": [finding], "blockers": ["source figure is unsupported"]},
    }
    assert native_observer_outcome(observed) == {
        "status": "fail",
        "findings": [finding],
        "blockers": ["source figure is unsupported"],
    }
    del observed["spine"]
    with pytest.raises(ValueError, match="must be an object"):
        native_observer_outcome(observed)


@pytest.mark.parametrize("content", [b'{"status":"fail","status":"pass"}', b'{"record":{"exit_code":1,"exit_code":0}}'])
def test_receipt_duplicate_fields_are_refused_from_actual_file_bytes(tmp_path: Path, content: bytes) -> None:
    leaf = tmp_path / "output/readiness/control.json"
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(content)
    reader = SnapshotReader(tmp_path)
    with pytest.raises(ValueError, match="repeats JSON field"):
        reader.read("output/readiness/control.json").json_object()
