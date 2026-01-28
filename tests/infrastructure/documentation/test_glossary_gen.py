from __future__ import annotations

import os
from textwrap import dedent

import pytest

from infrastructure.documentation.glossary_gen import \
    _first_sentence  # type: ignore
from infrastructure.documentation.glossary_gen import (build_api_index,
                                                       generate_markdown_table,
                                                       inject_between_markers)


def write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_build_api_index_discovers_public_functions_and_classes(tmp_path):
    src_dir = tmp_path / "src"
    # visible module with public and private items
    write(
        src_dir.as_posix() + "/mod.py",
        dedent(
            '''
            """Module docstring"""
            def _hidden():
                """hidden"""
                return 1
            
            def public_func(a: int, b: int) -> int:
                """Add two ints."""
                return a + b
            
            class PublicClass:
                """A sample class with a summary sentence. The rest is ignored."""
                def method(self):
                    return 42
            '''
        ),
    )
    # a package __init__.py should resolve to module name 'pkg'
    write(
        src_dir.as_posix() + "/pkg/__init__.py",
        dedent(
            '''
            def pkg_func():
                """Package function."""
                return 'ok'
            '''
        ),
    )
    # file starting with underscore should be skipped entirely
    write(
        src_dir.as_posix() + "/_ignore.py",
        "def visible():\n    return True\n",
    )
    # invalid syntax file should be ignored gracefully
    write(
        src_dir.as_posix() + "/bad.py",
        "def oops(:\n    pass\n",
    )

    entries = build_api_index(src_dir.as_posix())
    names = {(e.module, e.name, e.kind) for e in entries}

    assert ("mod", "public_func", "function") in names
    assert ("mod", "PublicClass", "class") in names
    # private function hidden
    assert ("mod", "_hidden", "function") not in names
    # underscore file skipped
    assert not any(e.module.startswith("_ignore") for e in entries)
    # package module name collapsed to 'pkg'
    assert ("pkg", "pkg_func", "function") in names

    # summaries are first sentence only
    mod_class = next(e for e in entries if e.name == "PublicClass")
    assert "sample class" in mod_class.summary
    assert "." in mod_class.summary or mod_class.summary.endswith("...")


def test_generate_markdown_table_includes_all_entries(tmp_path):
    # minimal entries via real scan
    src_dir = tmp_path / "src"
    write(
        src_dir.as_posix() + "/m.py",
        'def f():\n    """do x"""\n    return 0\n',
    )
    entries = build_api_index(src_dir.as_posix())
    table = generate_markdown_table(entries)

    assert table.startswith("| Module | Name | Kind | Summary |\n|---|---|---|---|\n")
    assert "`m`" in table and "`f`" in table and "function" in table


def test_generate_markdown_table_empty():
    assert generate_markdown_table([]).strip() == "No public APIs detected in `src/`."


def test_inject_between_markers_replaces_when_present():
    begin = "<!-- BEGIN -->"
    end = "<!-- END -->"
    base = dedent(
        f"""
        before text
        {begin}
        OLD CONTENT
        {end}
        after text
        """
    ).strip()
    new = inject_between_markers(base, begin, end, "NEW CONTENT")
    assert begin in new and end in new
    assert "NEW CONTENT" in new and "OLD CONTENT" not in new


def test_inject_between_markers_appends_when_missing():
    begin = "<!-- BEGIN -->"
    end = "<!-- END -->"
    base = "no markers here"
    new = inject_between_markers(base, begin, end, "X")
    assert base in new
    assert begin in new and end in new
    assert "X" in new


def test_first_sentence_handles_none_and_truncation():
    assert _first_sentence(None) == ""
    assert _first_sentence("") == ""
    long = "A" * 500
    out = _first_sentence(long)
    assert out.endswith("...") and len(out) <= 200


def test_inject_between_markers_when_only_begin_present():
    begin = "<!-- BEGIN -->"
    end = "<!-- END -->"
    text = "prefix\n" + begin + "\ncontent-without-end"
    # end missing triggers append path
    new = inject_between_markers(text, begin, end, "X")
    assert begin in new and end in new and "X" in new


def test_inject_between_markers_when_end_before_begin():
    begin = "<!-- BEGIN -->"
    end = "<!-- END -->"
    text = end + "\nmid\n" + begin
    new = inject_between_markers(text, begin, end, "Y")
    assert begin in new and end in new and "Y" in new


def test_non_python_files_are_ignored(tmp_path):
    src_dir = tmp_path / "src"
    write(src_dir.as_posix() + "/notes.txt", "not python")
    entries = build_api_index(src_dir.as_posix())
    assert entries == []


def test_package_init_normalization(tmp_path):
    src_dir = tmp_path / "src"
    write(src_dir.as_posix() + "/p/__init__.py", "def g():\n    return 1\n")
    entries = build_api_index(src_dir.as_posix())
    assert any(e.module == "p" for e in entries)


def test_build_api_index_skips_unreadable_file(tmp_path, monkeypatch):
    # Create a file but monkeypatch open to raise for that path
    src_dir = tmp_path / "src"
    bad_path = src_dir / "cantread.py"
    write(bad_path.as_posix(), "def x():\n    return 1\n")

    real_open = open

    def fake_open(path, *args, **kwargs):
        if os.path.abspath(path) == os.path.abspath(bad_path.as_posix()):
            raise OSError("permission denied")
        return real_open(path, *args, **kwargs)

    import builtins

    monkeypatch.setattr(builtins, "open", fake_open)

    entries = build_api_index(src_dir.as_posix())
    # Should not raise, and simply skip the unreadable file
    assert isinstance(entries, list)
