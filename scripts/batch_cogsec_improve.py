#!/usr/bin/env python3
"""
Batch code quality improver for a cognitive_integrity part.
Applies mechanical transformations:
  1. Insert 'from __future__ import annotations' if absent (after module docstring)
  2. Add minimal module docstring if none exists
  3. Replace bare 'except:' with 'except Exception:'
  4. Ensure consistent module docstring style (Google-ish, 1-2 sentences)
"""
import ast
import re
from pathlib import Path

def improve_file(path: Path) -> dict:
    source = path.read_text()
    lines = source.splitlines(keepends=True)
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"file": str(path), "error": str(e), "modified": False}
    changes = {"file": str(path), "future": False, "docstring": False, "except": 0, "modified": False}

    # Check future import
    if "from __future__ import annotations" not in source:
        insert_line = 1
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
            insert_line = 2  # after docstring
        lines.insert(insert_line - 1, "from __future__ import annotations\n\n")
        changes["future"] = True
        changes["modified"] = True

    # Re-parse after potential insert (too complicated; we'll just proceed with line edits)

    # Bare except fix
    new_lines = []
    for line in lines:
        m = re.match(r"^(\s*)except\s*:", line)
        if m:
            new_line = f"{m.group(1)}except Exception:\n"
            new_lines.append(new_line)
            changes["except"] += 1
            if new_line != line:
                changes["modified"] = True
        else:
            new_lines.append(line)

    # Module docstring (only if still none after future insert)
    combined = "".join(new_lines)
    try:
        tree2 = ast.parse(combined)
    except SyntaxError:
        tree2 = None
    if tree2 and not (
        tree2.body
        and isinstance(tree2.body[0], ast.Expr)
        and isinstance(tree2.body[0].value, ast.Constant)
        and isinstance(tree2.body[0].value.value, str)
    ):
        # Insert a short docstring at top
        doc = f'"""{path.stem.replace("_", " ").title()} module.\n\nPart of the Cognitive Integrity Framework.\n"""\n\n'
        new_lines.insert(0, doc)
        changes["docstring"] = True
        changes["modified"] = True

    if changes["modified"]:
        path.write_text("".join(new_lines))
    return changes

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: batch_cogsec_improve.py <src_root_dir>")
        sys.exit(1)
    root = Path(sys.argv[1])
    if not root.exists():
        print(f"Error: {root} not found")
        sys.exit(1)
    total = {"files": 0, "future": 0, "docstring": 0, "except": 0, "modified": 0}
    for pyfile in sorted(root.rglob("*.py")):
        if "tests" in pyfile.parts or ".venv" in pyfile.parts or "__pycache__" in pyfile.parts:
            continue
        result = improve_file(pyfile)
        total["files"] += 1
        for k in ["future", "docstring", "except"]:
            total[k] += result.get(k, 0)
        if result.get("modified"):
            total["modified"] += 1
        if "error" in result:
            print(f"ERROR in {result['file']}: {result['error']}")
    print("=== BATCH IMPROVE SUMMARY ===")
    print(f"Root: {root}")
    print(f"Files scanned: {total['files']}")
    print(f"Files modified: {total['modified']}")
    print(f"  Added __future__: {total['future']}")
    print(f"  Added docstrings: {total['docstring']}")
    print(f"  Fixed bare excepts: {total['except']}")

if __name__ == "__main__":
    main()
