"""Gate: Check for drift in Hermes plugin export.

Runs `template plugin export --output .hermes/plugins/template-plugin --check` to detect
drift between source and exported plugin definitions. If drift is detected,
prints a clear diff summary and exits with code 1. Exits 0 if clean.
"""

import filecmp
import subprocess
import sys
import tempfile
from difflib import unified_diff
from pathlib import Path


def _compare_directories(dir1: Path, dir2: Path) -> tuple[set[Path], set[Path], set[Path]]:
    """Recursively compare two directories.

    Args:
        dir1: First directory (e.g., fresh export).
        dir2: Second directory (e.g., committed export).

    Returns:
        (only_in_dir1, only_in_dir2, diff_files) where diff_files are files
        present in both but with different content.
    """
    if not dir1.exists():
        raise FileNotFoundError(f"Directory not found: {dir1}")
    if not dir2.exists():
        # If expected dir doesn't exist, all files in dir1 are "only in dir1"
        only1 = {p.relative_to(dir1) for p in dir1.rglob("*") if p.is_file()}
        return only1, set(), set()

    files1 = {}
    for p in dir1.rglob("*"):
        if p.is_file():
            rel = p.relative_to(dir1)
            files1[rel] = p
    files2 = {}
    for p in dir2.rglob("*"):
        if p.is_file():
            rel = p.relative_to(dir2)
            files2[rel] = p

    set1 = set(files1)
    set2 = set(files2)

    only1 = set1 - set2
    only2 = set2 - set1
    common = set1 & set2

    diff_files = set()
    for rel in common:
        f1 = files1[rel]
        f2 = files2[rel]
        try:
            if not filecmp.cmp(f1, f2, shallow=False):
                diff_files.add(rel)
        except Exception as e:
            print(f"Warning: could not compare {rel}: {e}", file=sys.stderr)

    return only1, only2, diff_files


def run_gate() -> int:
    """Execute the plugin export check gate.

    Returns:
        0 if no drift, 1 if drift detected or error.
    """
    # Step 1: Run template plugin export with --check to detect drift quickly.
    check_cmd = [
        "template", "plugin", "export",
        "--output", ".hermes/plugins/template-plugin",
        "--check"
    ]
    try:
        result = subprocess.run(
            check_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
    except FileNotFoundError:
        print("ERROR: 'template' command not found. Ensure Hermes is installed and on PATH.", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("ERROR: 'template plugin export --check' timed out after 60 seconds.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Failed to run template command: {e}", file=sys.stderr)
        return 1

    if result.returncode == 0:
        print("✅ Plugin export check passed: no drift detected.")
        return 0

    # Drift detected
    print("❌ Plugin export check FAILED: drift detected.", file=sys.stderr)
    if result.stdout:
        print(" template output:\n", result.stdout, file=sys.stderr)
    if result.stderr:
        print(" template errors:\n", result.stderr, file=sys.stderr)

    # Step 2: Generate a detailed diff summary by performing a full export
    # to a temporary directory and comparing with the committed export.
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            export_tmp = Path(tmpdir) / "exported_plugin"
            export_cmd = [
                "template", "plugin", "export",
                "--output", str(export_tmp)
            ]
            subprocess.run(export_cmd, check=True, capture_output=True, text=True, timeout=60)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Plugin export failed (exit {e.returncode}).", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Could not generate export for diff: {e}", file=sys.stderr)
        return 1

    expected_dir = Path(".hermes/plugins/template-plugin")

    if not expected_dir.exists():
        print(f"ERROR: Expected plugin directory '{expected_dir}' does not exist.", file=sys.stderr)
        print("Cannot compute diff; committed plugin files missing.", file=sys.stderr)
        return 1

    try:
        only_export, only_expected, diff_files = _compare_directories(export_tmp, expected_dir)
    except Exception as e:
        print(f"ERROR: Directory comparison failed: {e}", file=sys.stderr)
        return 1

    # Print summary
    if only_export:
        print(f"\n  New files in export (not in committed): {sorted(str(p) for p in only_export)}")
    if only_expected:
        print(f"\n  Files missing from export (deleted in source): {sorted(str(p) for p in only_expected)}")
    if diff_files:
        print("\n  Modified files (content differs):")
        for rel in sorted(diff_files):
            print(f"    - {rel}")
            left = export_tmp / rel
            right = expected_dir / rel
            try:
                with open(left, "r", encoding="utf-8", errors="replace") as f1, \
                     open(right, "r", encoding="utf-8", errors="replace") as f2:
                    left_lines = f1.readlines()
                    right_lines = f2.readlines()
                diff = list(unified_diff(
                    left_lines, right_lines,
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                    lineterm=""
                ))
                if diff:
                    print("      --- unified diff ---")
                    for line in diff:
                        print(f"      {line}")
            except Exception as e:
                print(f"      Could not generate diff for {rel}: {e}")

    if not (only_export or only_expected or diff_files):
        # This shouldn't happen if template --check returned non-zero, but we report uncertainty.
        print("WARNING: template reported drift but no file differences were found.", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(run_gate())
