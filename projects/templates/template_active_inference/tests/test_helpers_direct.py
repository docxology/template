"""Direct (read-only) tests for small pure functions in helpers modules.

These functions read no tracked output/ state and need no project-tree copy.
They are exercised here so the 90% coverage floor does not depend on
whether the heavy sheaf-track writers happen to run during a given CI leg.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast


# ---------------------------------------------------------------------------
# roadmap_tracks.row_aggregates  (row predicates on dict payloads)
# ---------------------------------------------------------------------------


def _rows(payload: dict, key: str = "rows"):
    from roadmap_tracks.row_aggregates import rows

    return rows(payload, key)


def _all_rows(payload: dict, predicate, key: str = "rows") -> bool:
    from roadmap_tracks.row_aggregates import all_rows

    return cast(bool, all_rows(payload, predicate, key))


def _all_field_present(payload: dict, fields, key: str = "rows") -> bool:
    from roadmap_tracks.row_aggregates import all_field_present

    return cast(bool, all_field_present(payload, fields, key))


class TestRowAggregates:
    def test_rows_returns_filtered_list(self) -> None:
        payload = {"rows": [{"a": 1}, {"a": 2}, "not-a-dict"]}
        assert _rows(payload) == [{"a": 1}, {"a": 2}]

    def test_rows_returns_empty_for_missing_key(self) -> None:
        assert _rows({}) == []
        assert _rows({"data": None}) == []

    def test_rows_custom_key(self) -> None:
        payload = {"items": [{"x": 10}]}
        assert _rows(payload, key="items") == [{"x": 10}]

    def test_all_rows_true_when_all_satisfy(self) -> None:
        payload = {"rows": [{"ok": True}, {"ok": True}]}
        assert _all_rows(payload, lambda r: r["ok"]) is True

    def test_all_rows_false_when_one_fails(self) -> None:
        payload = {"rows": [{"ok": True}, {"ok": False}]}
        assert _all_rows(payload, lambda r: r["ok"]) is False

    def test_all_rows_false_for_empty(self) -> None:
        assert _all_rows({}, lambda r: True) is False

    def test_all_field_present_true(self) -> None:
        payload = {"rows": [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]}
        assert _all_field_present(payload, ["a", "b"]) is True

    def test_all_field_present_false_when_field_missing(self) -> None:
        payload = {"rows": [{"a": 1}, {"a": 2, "b": "y"}]}
        assert _all_field_present(payload, ["a", "b"]) is False


# ---------------------------------------------------------------------------
# roadmap_tracks.sheaf_tracks_helpers
# ---------------------------------------------------------------------------


def _entropy(values: list[float]) -> float:
    from roadmap_tracks.sheaf_tracks_helpers import _entropy

    return cast(float, _entropy(values))


def _portable_repo_path(path: Path, project_root: Path) -> str:
    from roadmap_tracks.sheaf_tracks_helpers import _portable_repo_path

    return cast(str, _portable_repo_path(path, project_root))


class TestSheafTracksHelpersEntropy:
    def test_entropy_uniform(self) -> None:
        e = _entropy([0.5, 0.5])
        assert abs(e - 0.693) < 0.01

    def test_entropy_deterministic(self) -> None:
        assert abs(_entropy([1.0, 0.0]) - 0.0) < 1e-9

    def test_entropy_skips_zeros(self) -> None:
        e = _entropy([0.5, 0.5, 0.0, 0.0])
        assert abs(e - 0.693) < 0.01


class TestSheafTracksHelpersPortableRepoPath:
    def test_inside_repo_returns_relative(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir(parents=True)
        (repo_root / "run.sh").touch()
        (repo_root / "projects").mkdir()
        proj = repo_root / "projects" / "my_proj"
        proj.mkdir()
        target = proj / "src" / "mod.py"
        target.parent.mkdir()
        target.touch()
        result = _portable_repo_path(target, proj)
        assert result == "<repo-root>/projects/my_proj/src/mod.py"

    def test_outside_repo_is_redacted(self, tmp_path: Path) -> None:
        isolated = tmp_path / "isolated"
        isolated.mkdir()
        target = isolated / "data.txt"
        target.touch()
        result = _portable_repo_path(target, isolated)
        assert result == "<external-path>"


# ---------------------------------------------------------------------------
# roadmap_tracks.sheaf_tracks_io
# ---------------------------------------------------------------------------


def _bridge(row: dict) -> tuple[bool, bool]:
    from roadmap_tracks.sheaf_tracks_io import _bridge_reference_section_status

    return cast(tuple[bool, bool], _bridge_reference_section_status(row))


def _sha256(path: Path) -> str:
    from roadmap_tracks.sheaf_tracks_io import _sha256

    return cast(str, _sha256(path))


def _deterministic_seed(root: Path) -> int:
    from roadmap_tracks.sheaf_tracks_io import _deterministic_seed

    return cast(int, _deterministic_seed(root))


class TestSheafTracksIOBridgeReference:
    def test_unbound_row_returns_false_false(self) -> None:
        assert _bridge({}) == (False, False)

    def test_no_sections_returns_false_false(self) -> None:
        row = {"reference_track_bindings": {"01_intro": ["visualization"]}}
        assert _bridge(row) == (False, False)

    def test_sheaf_bound_but_not_visualization(self) -> None:
        row = {
            "figure_reference_sections": ["01_intro"],
            "reference_track_bindings": {"01_intro": ["analytical"]},
        }
        sheaf_bound, visualization_bound = _bridge(row)
        assert sheaf_bound is True
        assert visualization_bound is False

    def test_full_bind(self) -> None:
        row = {
            "figure_reference_sections": ["01_intro"],
            "reference_track_bindings": {"01_intro": ["visualization", "analytical"]},
        }
        sheaf_bound, visualization_bound = _bridge(row)
        assert sheaf_bound is True
        assert visualization_bound is True


class TestSheafTracksIOSha256:
    def test_missing_file_returns_empty(self) -> None:
        assert _sha256(Path("/nonexistent/path")) == ""

    def test_file_returns_nonempty_digest(self, tmp_path: Path) -> None:
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        digest = _sha256(f)
        assert len(digest) == 64


class TestSheafTracksIODeterministicSeed:
    def test_missing_pymdp_yaml_returns_zero(self, tmp_path: Path) -> None:
        assert _deterministic_seed(tmp_path) == 0

    def test_missing_seed_keys_returns_zero(self, tmp_path: Path) -> None:
        cfg = tmp_path / "pymdp.yaml"
        cfg.write_text("other_key: 42\n")
        assert _deterministic_seed(tmp_path) == 0


# ---------------------------------------------------------------------------
# roadmap_tracks.sheaf_tracks_io  - _source_commit (injectable subprocess)
# ---------------------------------------------------------------------------


class TestSheafTracksIOSourceCommit:
    def test_returns_stdout_stripped(self, tmp_path: Path) -> None:
        def _fake_runner(*args, **kwargs):
            class Result:
                stdout = " abc123def  \n"
                returncode = 0

            return Result()

        from roadmap_tracks.sheaf_tracks_io import _source_commit

        assert _source_commit(tmp_path, process_runner=_fake_runner) == "abc123def"

    def test_returns_unknown_on_error(self, tmp_path: Path) -> None:
        def _fake_runner(*args, **kwargs):
            raise OSError("not a git repo")

        from roadmap_tracks.sheaf_tracks_io import _source_commit

        assert _source_commit(tmp_path, process_runner=_fake_runner) == "unknown"

    def test_returns_unknown_when_stdout_empty(self, tmp_path: Path) -> None:
        def _fake_runner(*args, **kwargs):
            class Result:
                stdout = ""
                returncode = 0

            return Result()

        from roadmap_tracks.sheaf_tracks_io import _source_commit

        assert _source_commit(tmp_path, process_runner=_fake_runner) == "unknown"


# ---------------------------------------------------------------------------
# roadmap_tracks.sheaf_tracks_io  - _config_digest (tmp_path fixture)
# ---------------------------------------------------------------------------


def _config_digest(root: Path) -> str:
    from roadmap_tracks.sheaf_tracks_io import _config_digest

    return cast(str, _config_digest(root))


class TestSheafTracksIOConfigDigest:
    def test_digest_is_nonempty_even_with_all_missing(self, tmp_path: Path) -> None:
        """Missing files hash to their empty keys, producing a deterministic digest."""
        d = _config_digest(tmp_path)
        assert len(d) == 64
        # Same empty-tree digest every time
        assert _config_digest(tmp_path) == d

    def test_digest_changes_when_file_content_changes(self, tmp_path: Path) -> None:
        cfg_dir = tmp_path / "manuscript"
        cfg_dir.mkdir(parents=True)
        cfg = cfg_dir / "config.yaml"
        cfg.write_text("key: value\n")
        d1 = _config_digest(tmp_path)
        cfg.write_text("key: other\n")
        d2 = _config_digest(tmp_path)
        assert d1 != d2


# ---------------------------------------------------------------------------
# roadmap_tracks.sheaf_tracks_io  - _load_structured
# ---------------------------------------------------------------------------


def _load_structured(path: Path) -> dict[str, Any]:
    from roadmap_tracks.sheaf_tracks_io import _load_structured

    return cast(dict[str, Any], _load_structured(path))


class TestSheafTracksIOLoadStructured:
    def test_missing_yaml_file_returns_empty(self, tmp_path: Path) -> None:
        assert _load_structured(tmp_path / "nonexistent.yaml") == {}

    def test_missing_json_file_returns_empty_via_json_fallback(self, tmp_path: Path) -> None:
        """A .json file that doesn't exist returns {} via the JSON loader fallback."""
        assert _load_structured(tmp_path / "missing.json") == {}


# ---------------------------------------------------------------------------
# roadmap_tracks.sheaf_tracks_io  - _pipeline_tracks and _claim_ids_by_track
# ---------------------------------------------------------------------------


class TestSheafTracksIOPipelineTracks:
    def test_missing_tracks_yaml_returns_empty(self, tmp_path: Path) -> None:
        from roadmap_tracks.sheaf_tracks_io import _pipeline_tracks

        assert _pipeline_tracks(tmp_path) == []

    def test_malformed_tracks_yaml_returns_empty(self, tmp_path: Path) -> None:
        cfg = tmp_path / "tracks.yaml"
        cfg.write_text("tracks: invalid\n")
        from roadmap_tracks.sheaf_tracks_io import _pipeline_tracks

        assert _pipeline_tracks(tmp_path) == []


class TestSheafTracksIOClaimIdsByTrack:
    def test_missing_ledger_returns_empty(self, tmp_path: Path) -> None:
        from roadmap_tracks.sheaf_tracks_io import _claim_ids_by_track

        assert _claim_ids_by_track(tmp_path) == {}

    def test_present_claims_by_track(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        ledger = data_dir / "claim_ledger.yaml"
        ledger.write_text(
            "claims:\n  - id: c1\n    tracks: [t1, t2]\n  - id: c2\n    tracks: [t2]\n  - id: c3\n    tracks: []\n"
        )
        from roadmap_tracks.sheaf_tracks_io import _claim_ids_by_track

        result = _claim_ids_by_track(tmp_path)
        assert result == {"t1": ["c1"], "t2": ["c1", "c2"]}
