"""Tests for infrastructure/validation/test_supplements.py.

Exercises merge_supplements over real files with tmp_path: missing supplement,
dry-run (no write), dedupe of already-present tests, and the class-rename path
where a supplement reuses a class name already in the canonical module but adds
a genuinely new test method.

Follows No Mocks Policy — real files, real AST parsing, tmp_path only.
"""

from __future__ import annotations

import ast

from infrastructure.validation.test_supplements import merge_supplements

CANONICAL = '''\
"""Canonical test module."""


def test_alpha():
    assert True


class TestThings:
    def test_one(self):
        assert True
'''


def _write(tmp_path, name, body):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_missing_supplement_is_skipped(tmp_path):
    canonical = _write(tmp_path, "test_canon.py", CANONICAL)
    missing = tmp_path / "test_does_not_exist.py"
    added = merge_supplements(canonical, [missing])
    assert added == 0
    # Canonical untouched.
    assert canonical.read_text(encoding="utf-8") == CANONICAL


def test_dry_run_does_not_write(tmp_path):
    canonical = _write(tmp_path, "test_canon.py", CANONICAL)
    supplement = _write(
        tmp_path,
        "test_extra.py",
        "def test_brand_new():\n    assert 1 == 1\n",
    )
    before = canonical.read_text(encoding="utf-8")
    count = merge_supplements(canonical, [supplement], dry_run=True)
    assert count == 1
    # Dry-run must not modify the canonical file.
    assert canonical.read_text(encoding="utf-8") == before


def test_appends_unique_function(tmp_path):
    canonical = _write(tmp_path, "test_canon.py", CANONICAL)
    supplement = _write(
        tmp_path,
        "test_extra.py",
        "def test_brand_new():\n    assert 1 == 1\n",
    )
    count = merge_supplements(canonical, [supplement])
    assert count == 1
    merged = canonical.read_text(encoding="utf-8")
    assert "def test_brand_new" in merged
    # Still valid Python.
    ast.parse(merged)


def test_dedupe_skips_existing_tests(tmp_path):
    canonical = _write(tmp_path, "test_canon.py", CANONICAL)
    # Supplement re-defines test_alpha (already present) -> deduped.
    supplement = _write(
        tmp_path,
        "test_dupe.py",
        "def test_alpha():\n    assert True\n",
    )
    count = merge_supplements(canonical, [supplement])
    assert count == 0
    assert canonical.read_text(encoding="utf-8") == CANONICAL


def test_class_rename_on_collision(tmp_path):
    canonical = _write(tmp_path, "test_canon.py", CANONICAL)
    # Supplement reuses TestThings but adds a NEW method test_two ->
    # the class is appended under a renamed name to avoid collision.
    supplement = _write(
        tmp_path,
        "test_supp.py",
        "class TestThings:\n    def test_two(self):\n        assert True\n",
    )
    count = merge_supplements(canonical, [supplement])
    assert count == 1
    merged = canonical.read_text(encoding="utf-8")
    # Renamed class: stem of "test_supp" -> "supp" -> "Supp".
    assert "class TestThingsFromSupp" in merged
    assert "def test_two" in merged
    # Original class kept intact, no duplicate class TestThings.
    tree = ast.parse(merged)
    class_names = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    assert class_names.count("TestThings") == 1
    assert "TestThingsFromSupp" in class_names


def test_colliding_class_is_renamed_even_when_methods_match(tmp_path):
    # A class-name collision is keyed by the RENAMED class, so methods that
    # share names with the original class are still treated as unique under
    # the new name and the renamed class is appended (documents the dedupe
    # boundary: collision-rename happens at class granularity, not method).
    canonical = _write(tmp_path, "test_canon.py", CANONICAL)
    supplement = _write(
        tmp_path,
        "test_supp.py",
        "class TestThings:\n    def test_one(self):\n        assert True\n",
    )
    count = merge_supplements(canonical, [supplement])
    assert count == 1
    merged = canonical.read_text(encoding="utf-8")
    assert "class TestThingsFromSupp" in merged
    ast.parse(merged)


def test_top_level_function_deduped_against_canonical(tmp_path):
    # A top-level function that duplicates a canonical test name is skipped.
    canonical = _write(tmp_path, "test_canon.py", CANONICAL)
    supplement = _write(
        tmp_path,
        "test_dupe2.py",
        "def test_alpha():\n    assert False\n\n\ndef test_gamma():\n    assert True\n",
    )
    count = merge_supplements(canonical, [supplement])
    # Only the new test_gamma is appended; test_alpha is deduped.
    assert count == 1
    merged = canonical.read_text(encoding="utf-8")
    assert "def test_gamma" in merged
    # The duplicate definition body (assert False) was NOT appended.
    assert merged.count("def test_alpha") == 1
