"""AST helpers for merging pytest supplement files."""

from __future__ import annotations

import ast
from pathlib import Path


def merge_supplements(canonical: Path, supplements: list[Path], dry_run: bool = False) -> int:
    """Merge supplement test blocks into a canonical test module."""
    canonical_source = canonical.read_text(encoding="utf-8")
    canon_tree = ast.parse(canonical_source, filename=str(canonical))
    keys = _collect_keys(canon_tree)
    class_names = _class_names(canon_tree)
    append_chunks: list[str] = []

    for supplement in supplements:
        if not supplement.exists():
            print(f"skip missing {supplement}")
            continue
        added = _append_unique_blocks(supplement, keys, class_names, append_chunks)
        print(f"{supplement.name}: appended {added} blocks")

    if not append_chunks:
        return 0
    if dry_run:
        print(f"would append {len(append_chunks)} blocks to {canonical}")
        return len(append_chunks)

    canonical.write_text(canonical_source.rstrip() + "\n" + "".join(append_chunks), encoding="utf-8")
    print(f"merged {len(append_chunks)} total blocks into {canonical.name}")
    return len(append_chunks)


def _append_unique_blocks(
    supplement: Path,
    keys: set[str],
    class_names: set[str],
    append_chunks: list[str],
) -> int:
    source = supplement.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(supplement))
    lines = source.splitlines(keepends=True)
    stem = supplement.stem.replace("test_", "").replace("_coverage", "").replace("_full", "")
    added = 0
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.ClassDef):
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
    return added


def _collect_keys(tree: ast.Module) -> set[str]:
    keys: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            keys.add(node.name)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test"):
                    keys.add(f"{node.name}.{item.name}")
    return keys


def _class_names(tree: ast.Module) -> set[str]:
    return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}


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
