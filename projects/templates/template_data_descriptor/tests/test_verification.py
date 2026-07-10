"""Tests for byte-level descriptor↔file verification (no mocks; real files)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

from data_descriptor import (
    FileVerification,
    compute_file_digest,
    count_csv_rows,
    verification_summary,
    verify_descriptor_files,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_fixture() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        json.loads((DATA_DIR / "example_descriptor.json").read_text(encoding="utf-8")),
    )


class TestComputeFileDigest:
    """Digest matches an independent hashlib computation."""

    def test_matches_hashlib(self, tmp_path: Path) -> None:
        target = tmp_path / "sample.csv"
        target.write_bytes(b"a,b\n1,2\n")
        expected = "sha256:" + hashlib.sha256(b"a,b\n1,2\n").hexdigest()
        assert compute_file_digest(target) == expected

    def test_shipped_measurements_digest_matches_descriptor(self) -> None:
        descriptor = load_fixture()
        declared = descriptor["files"][0]["checksum"]
        actual = compute_file_digest(DATA_DIR / "fixtures" / "measurements.csv")
        assert actual == declared


class TestCountCsvRows:
    """Row counting excludes the header and blank lines."""

    def test_counts_data_rows(self, tmp_path: Path) -> None:
        target = tmp_path / "d.csv"
        target.write_text("h1,h2\n1,2\n3,4\n5,6\n", encoding="utf-8")
        assert count_csv_rows(target) == 3

    def test_ignores_trailing_blank_lines(self, tmp_path: Path) -> None:
        target = tmp_path / "d.csv"
        target.write_text("h1\n1\n2\n\n\n", encoding="utf-8")
        assert count_csv_rows(target) == 2

    def test_empty_file_is_zero_rows(self, tmp_path: Path) -> None:
        target = tmp_path / "empty.csv"
        target.write_text("", encoding="utf-8")
        assert count_csv_rows(target) == 0


class TestVerifyDescriptorFiles:
    """Verification binds the descriptor to bytes on disk."""

    def test_shipped_fixture_verifies_clean(self) -> None:
        descriptor = load_fixture()
        results = verify_descriptor_files(descriptor, DATA_DIR)
        assert len(results) == 2
        assert all(isinstance(item, FileVerification) for item in results)
        assert all(item.status == "verified" for item in results)
        assert all(item.checksum_ok and item.rows_ok for item in results)

    def test_absent_file_is_reported_not_failed(self, tmp_path: Path) -> None:
        descriptor = {
            "files": [
                {
                    "path": "missing.csv",
                    "media_type": "text/csv",
                    "checksum": "sha256:" + "0" * 64,
                    "rows": 3,
                }
            ]
        }
        results = verify_descriptor_files(descriptor, tmp_path)
        assert results[0].status == "absent"
        assert results[0].actual_rows == -1
        assert results[0].actual_checksum == ""

    def test_checksum_mismatch_detected(self, tmp_path: Path) -> None:
        target = tmp_path / "m.csv"
        target.write_text("h\n1\n2\n", encoding="utf-8")
        descriptor = {
            "files": [{"path": "m.csv", "media_type": "text/csv", "checksum": "sha256:" + "1" * 64, "rows": 2}]
        }
        results = verify_descriptor_files(descriptor, tmp_path)
        assert results[0].status == "checksum_mismatch"
        assert results[0].rows_ok is True
        assert results[0].checksum_ok is False

    def test_row_mismatch_detected(self, tmp_path: Path) -> None:
        target = tmp_path / "m.csv"
        target.write_text("h\n1\n2\n", encoding="utf-8")
        descriptor = {
            "files": [
                {
                    "path": "m.csv",
                    "media_type": "text/csv",
                    "checksum": compute_file_digest(target),
                    "rows": 99,
                }
            ]
        }
        results = verify_descriptor_files(descriptor, tmp_path)
        assert results[0].status == "row_mismatch"
        assert results[0].checksum_ok is True
        assert results[0].rows_ok is False

    def test_non_list_and_non_mapping_entries_are_tolerated(self, tmp_path: Path) -> None:
        assert verify_descriptor_files({"files": "not-a-list"}, tmp_path) == ()
        results = verify_descriptor_files({"files": ["not-a-mapping", {"path": "x.csv"}]}, tmp_path)
        assert len(results) == 1
        assert results[0].status == "absent"


class TestVerificationSummary:
    """Summary aggregates statuses into counts."""

    def test_summary_counts(self) -> None:
        descriptor = load_fixture()
        results = verify_descriptor_files(descriptor, DATA_DIR)
        summary = verification_summary(results)
        assert summary == {"total": 2, "verified": 2, "absent": 0, "mismatch": 0}

    def test_summary_counts_absent_and_mismatch(self, tmp_path: Path) -> None:
        good = tmp_path / "g.csv"
        good.write_text("h\n1\n", encoding="utf-8")
        descriptor = {
            "files": [
                {"path": "g.csv", "media_type": "text/csv", "checksum": compute_file_digest(good), "rows": 1},
                {"path": "gone.csv", "media_type": "text/csv", "checksum": "sha256:" + "0" * 64, "rows": 1},
            ]
        }
        summary = verification_summary(verify_descriptor_files(descriptor, tmp_path))
        assert summary == {"total": 2, "verified": 1, "absent": 1, "mismatch": 0}
