#!/usr/bin/env python3
"""Merge pytest supplement files into a canonical test module.

Dedupes by test function name and ClassName.test_method. Renames duplicate
classes to ``{ClassName}From{stem}``. Merges missing top-level imports.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


def _collect_keys(tree: ast.Module) -> set[str]:
    keys: set[str] = set()
    class_names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            keys.add(node.name)
        elif isinstance(node, ast.ClassDef):
            class_names.add(node.name)
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test"):
                    keys.add(f"{node.name}.{item.name}")
    return keys


def _class_names(tree: ast.Module) -> set[str]:
    return {n.name for n in tree.body if isinstance(n, ast.ClassDef)}


def _node_has_unique_tests(node: ast.AST, keys: set[str], class_name: str | None = None) -> bool:
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
        return node.name not in keys
    if isinstance(node, ast.ClassDef):
        cname = class_name or node.name
        return any(
            f"{cname}.{item.name}" not in keys
            for item in node.body
            if isinstance(item, ast.FunctionDef) and item.name.startswith("test")
        )
    return False


def _register_node_keys(node: ast.AST, keys: set[str], class_name: str | None = None) -> None:
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
        keys.add(node.name)
    elif isinstance(node, ast.ClassDef):
        cname = class_name or node.name
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name.startswith("test"):
                keys.add(f"{cname}.{item.name}")


def _rename_class_source(source: str, old: str, new: str) -> str:
    return source.replace(f"class {old}", f"class {new}", 1)


def _merge_imports(canonical_source: str, supplement_sources: list[str]) -> str:
    """Append only standalone import lines missing from canonical (no AST splice)."""
    canon_lines = set(canonical_source.splitlines())
    extra: list[str] = []
    for sup in supplement_sources:
        for line in sup.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                if stripped not in {ln.strip() for ln in canon_lines} and stripped not in extra:
                    # skip if module already imported via different line
                    extra.append(stripped)
    if not extra:
        return canonical_source
    lines = canonical_source.splitlines(keepends=True)
    # insert after module docstring, before first non-import/def/class
    insert_idx = 0
    if lines and lines[0].startswith('"""'):
        for i, line in enumerate(lines[1:], 1):
            if line.strip().endswith('"""'):
                insert_idx = i + 1
                break
    while insert_idx < len(lines) and (
        not lines[insert_idx].strip()
        or lines[insert_idx].strip().startswith("#")
        or lines[insert_idx].strip().startswith("import ")
        or lines[insert_idx].strip().startswith("from ")
    ):
        insert_idx += 1
    block = "".join(f"{line}\n" for line in extra) + "\n"
    return "".join(lines[:insert_idx]) + block + "".join(lines[insert_idx:])


def merge_supplements(canonical: Path, supplements: list[Path], dry_run: bool = False) -> int:
    canonical_source = canonical.read_text(encoding="utf-8")
    canon_tree = ast.parse(canonical_source, filename=str(canonical))
    keys = _collect_keys(canon_tree)
    class_names = _class_names(canon_tree)
    sup_texts: list[str] = []
    append_chunks: list[str] = []

    for sup in supplements:
        if not sup.exists():
            print(f"skip missing {sup}")
            continue
        sup_source = sup.read_text(encoding="utf-8")
        sup_texts.append(sup_source)
        sup_tree = ast.parse(sup_source, filename=str(sup))
        lines = sup_source.splitlines(keepends=True)
        stem = sup.stem.replace("test_", "").replace("_coverage", "").replace("_full", "")
        added = 0
        for node in sup_tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                continue
            rename: str | None = None
            if isinstance(node, ast.ClassDef) and node.name in class_names:
                rename = f"{node.name}From{stem.title().replace('_', '')}"
                if not _node_has_unique_tests(node, keys, rename):
                    continue
            elif not _node_has_unique_tests(node, keys):
                continue

            segment = "".join(lines[node.lineno - 1 : node.end_lineno])
            if rename:
                segment = _rename_class_source(segment, node.name, rename)
                class_names.add(rename)
                _register_node_keys(node, keys, rename)
            else:
                if isinstance(node, ast.ClassDef):
                    class_names.add(node.name)
                _register_node_keys(node, keys)
            append_chunks.append("\n\n" + segment.rstrip() + "\n")
            added += 1
        print(f"{sup.name}: appended {added} blocks")

    if not append_chunks:
        return 0

    merged = canonical_source.rstrip() + "\n" + "".join(append_chunks)
    if dry_run:
        print(f"would append {len(append_chunks)} blocks to {canonical}")
        return len(append_chunks)

    canonical.write_text(merged, encoding="utf-8")
    print(f"merged {len(append_chunks)} total blocks into {canonical.name}")
    return len(append_chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("canonical", type=Path)
    parser.add_argument("supplements", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    merge_supplements(args.canonical, args.supplements, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
