"""Plugin export drift detection for Hermes template plugins."""

from __future__ import annotations

import filecmp
import subprocess
import sys
import tempfile
from difflib import unified_diff
from pathlib import Path


def compare_directories(
    dir1: Path,
    dir2: Path,
) -> tuple[set[Path], set[Path], set[Path]]:
    """Return (only_in_dir1, only_in_dir2, diff_files)."""
    if not dir1.exists():
        raise FileNotFoundError(f"Directory not found: {dir1}")
    if not dir2.exists():
        only1 = {p.relative_to(dir1) for p in dir1.rglob("*") if p.is_file()}
        return only1, set(), set()

    files1 = {p.relative_to(dir1): p for p in dir1.rglob("*") if p.is_file()}
    files2 = {p.relative_to(dir2): p for p in dir2.rglob("*") if p.is_file()}
    set1 = set(files1)
    set2 = set(files2)
    only1 = set1 - set2
    only2 = set2 - set1
    diff_files: set[Path] = set()
    for rel in set1 & set2:
        try:
            if not filecmp.cmp(files1[rel], files2[rel], shallow=False):
                diff_files.add(rel)
        except OSError as exc:
            print(f"Warning: could not compare {rel}: {exc}", file=sys.stderr)
    return only1, only2, diff_files


def run_plugin_export_check(
    *,
    output_dir: Path | str = ".hermes/plugins/template-plugin",
    template_cmd: str = "template",
) -> int:
    """Execute plugin export drift check. Returns 0 if clean, 1 if drift or error."""
    output = Path(output_dir)
    check_cmd = [template_cmd, "plugin", "export", "--output", str(output), "--check"]
    try:
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        print(
            "ERROR: 'template' command not found. Ensure Hermes is installed and on PATH.",
            file=sys.stderr,
        )
        return 1
    except subprocess.TimeoutExpired:
        print("ERROR: 'template plugin export --check' timed out after 60 seconds.", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: Failed to run template command: {exc}", file=sys.stderr)
        return 1

    if result.returncode == 0:
        print("✅ Plugin export check passed: no drift detected.")
        return 0

    print("❌ Plugin export check FAILED: drift detected.", file=sys.stderr)
    if result.stdout:
        print(" template output:\n", result.stdout, file=sys.stderr)
    if result.stderr:
        print(" template errors:\n", result.stderr, file=sys.stderr)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            export_tmp = Path(tmpdir) / "exported_plugin"
            export_cmd = [template_cmd, "plugin", "export", "--output", str(export_tmp)]
            subprocess.run(export_cmd, check=True, capture_output=True, text=True, timeout=60)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: Plugin export failed (exit {exc.returncode}).", file=sys.stderr)
        print(exc.stdout, file=sys.stderr)
        print(exc.stderr, file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: Could not generate export for diff: {exc}", file=sys.stderr)
        return 1

    if not output.exists():
        print(f"ERROR: Expected plugin directory '{output}' does not exist.", file=sys.stderr)
        return 1

    try:
        only_export, only_expected, diff_files = compare_directories(export_tmp, output)
    except OSError as exc:
        print(f"ERROR: Directory comparison failed: {exc}", file=sys.stderr)
        return 1

    if only_export:
        print(f"\n  New files in export (not in committed): {sorted(str(p) for p in only_export)}")
    if only_expected:
        print(f"\n  Files missing from export (deleted in source): {sorted(str(p) for p in only_expected)}")
    if diff_files:
        print("\n  Modified files (content differs):")
        for rel in sorted(diff_files):
            print(f"    - {rel}")
            left = export_tmp / rel
            right = output / rel
            try:
                left_lines = left.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
                right_lines = right.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
                for line in unified_diff(
                    left_lines,
                    right_lines,
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                    lineterm="",
                ):
                    print(f"      {line}")
            except OSError as exc:
                print(f"      Could not generate diff for {rel}: {exc}")

    if not (only_export or only_expected or diff_files):
        print(
            "WARNING: template reported drift but no file differences were found.",
            file=sys.stderr,
        )
    return 1
