#!/usr/bin/env python3
"""Tests for infrastructure.validation.plugin_export."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.plugin_export import compare_directories, run_plugin_export_check


def test_compare_directories_finds_only_in_first(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "only_left.txt").write_text("a\n")
    (left / "both.txt").write_text("same\n")
    (right / "both.txt").write_text("same\n")

    only1, only2, diff = compare_directories(left, right)
    assert only1 == {Path("only_left.txt")}
    assert only2 == set()
    assert diff == set()


def test_compare_directories_finds_content_diff(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "file.txt").write_text("one\n")
    (right / "file.txt").write_text("two\n")

    only1, only2, diff = compare_directories(left, right)
    assert only1 == set()
    assert only2 == set()
    assert diff == {Path("file.txt")}


def test_compare_directories_when_right_missing(tmp_path: Path) -> None:
    left = tmp_path / "left"
    left.mkdir()
    (left / "a.txt").write_text("x\n")
    right = tmp_path / "missing"

    only1, only2, diff = compare_directories(left, right)
    assert only1 == {Path("a.txt")}
    assert only2 == set()
    assert diff == set()


def _write_template_exporter(tmp_path: Path, *, check_exit: int, export_text: str = "exported\n") -> Path:
    script = tmp_path / "template-exporter.py"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "from pathlib import Path",
                "import sys",
                "args = sys.argv[1:]",
                "if '--check' in args:",
                f"    raise SystemExit({check_exit})",
                "out = Path(args[args.index('--output') + 1])",
                "out.mkdir(parents=True, exist_ok=True)",
                f"(out / 'plugin.txt').write_text({export_text!r}, encoding='utf-8')",
                "raise SystemExit(0)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def test_run_plugin_export_check_passes_when_template_check_passes(tmp_path: Path) -> None:
    template_cmd = _write_template_exporter(tmp_path, check_exit=0)

    assert run_plugin_export_check(output_dir=tmp_path / "expected", template_cmd=str(template_cmd)) == 0


def test_run_plugin_export_check_reports_drift_with_real_export_diff(tmp_path: Path, capsys) -> None:
    expected = tmp_path / "expected"
    expected.mkdir()
    (expected / "plugin.txt").write_text("committed\n", encoding="utf-8")
    template_cmd = _write_template_exporter(tmp_path, check_exit=1, export_text="exported\n")

    assert run_plugin_export_check(output_dir=expected, template_cmd=str(template_cmd)) == 1
    captured = capsys.readouterr()
    assert "Modified files" in captured.out
    assert "plugin.txt" in captured.out


def test_run_plugin_export_check_missing_command_fails(tmp_path: Path) -> None:
    assert run_plugin_export_check(output_dir=tmp_path / "expected", template_cmd=str(tmp_path / "missing")) == 1
