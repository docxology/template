"""Tests for publication-artifact path portability."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.files.portability import sanitize_machine_local_paths


def test_sanitize_machine_local_paths_preserves_relative_suffix(tmp_path: Path) -> None:
    report = tmp_path / "output" / "reports" / "summary.json"
    report.parent.mkdir(parents=True)
    report.write_text(
        '{"mac": "/Users/alice/work/result.csv", "linux": "/home/bob/work/result.csv"}\n',
        encoding="utf-8",
    )

    changed = sanitize_machine_local_paths(tmp_path / "output")

    assert changed == (report,)
    assert report.read_text(encoding="utf-8") == (
        '{"mac": "<home>/work/result.csv", "linux": "<home>/work/result.csv"}\n'
    )


def test_sanitize_machine_local_paths_skips_binary_and_symlink(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    binary = output / "figure.png"
    binary.write_bytes(b"/Users/alice/private")
    outside = tmp_path / "outside.json"
    outside.write_text('{"path": "/Users/alice/private"}\n', encoding="utf-8")
    link = output / "linked.json"
    link.symlink_to(outside)

    assert sanitize_machine_local_paths(output) == ()
    assert binary.read_bytes() == b"/Users/alice/private"
    assert "/Users/alice/" in outside.read_text(encoding="utf-8")


def test_publication_sanitation_preserves_hidden_runtime_receipts(tmp_path: Path) -> None:
    output = tmp_path / "output"
    receipt = output / ".pipeline" / "analysis" / "original.json"
    receipt.parent.mkdir(parents=True)
    original = b'{"cwd": "/Users/alice/research", "custody": "verified"}\n'
    receipt.write_bytes(original)
    hidden_file = output / ".local.json"
    hidden_file.write_bytes(original)
    public = output / "data" / "analysis.json"
    public.parent.mkdir()
    public.write_bytes(original)

    assert sanitize_machine_local_paths(output) == (public,)
    assert receipt.read_bytes() == original
    assert hidden_file.read_bytes() == original
    assert b"<home>/research" in public.read_bytes()
