"""Tests for infrastructure.prose.markdown helpers."""

from __future__ import annotations

from pathlib import Path

from infrastructure.prose.markdown import (
    normalise_for_prose,
    read_manuscript_dir,
    strip_fences,
    strip_front_matter,
    strip_inline_code,
    strip_links_to_text,
)


class TestStripping:
    def test_front_matter(self):
        text = "---\ntitle: Hi\nauthor: A\n---\n\nReal body here."
        assert strip_front_matter(text).strip() == "Real body here."

    def test_no_front_matter(self):
        assert strip_front_matter("Plain text.") == "Plain text."

    def test_strip_fences(self):
        text = "Before\n```python\ncode\n```\nAfter"
        assert "code" not in strip_fences(text)
        assert "Before" in strip_fences(text)

    def test_strip_inline_code(self):
        text = "Use `foo()` to call."
        assert "`foo()`" not in strip_inline_code(text)

    def test_links_become_label(self):
        text = "See [Pandoc](https://pandoc.org) for details."
        out = strip_links_to_text(text)
        assert "Pandoc" in out
        assert "https://pandoc.org" not in out

    def test_image_dropped(self):
        text = "Look ![alt](pic.png) below."
        out = strip_links_to_text(text)
        assert "alt" not in out
        assert "pic.png" not in out

    def test_normalise_full(self):
        text = (
            "---\ntitle: T\n---\n\n"
            "# Header\n\n"
            "Body uses `code()` and links to [Pandoc](https://pandoc.org).\n\n"
            "```\nfenced\n```\n"
        )
        out = normalise_for_prose(text)
        assert "title:" not in out
        assert "code()" not in out
        assert "fenced" not in out
        assert "Pandoc" in out


class TestReadManuscriptDir:
    def test_collects_md_files(self, tmp_path: Path):
        (tmp_path / "01_intro.md").write_text("Intro body.")
        (tmp_path / "02_methods.md").write_text("Methods body.")
        (tmp_path / "ignored.txt").write_text("nope")
        files = read_manuscript_dir(tmp_path)
        assert set(files.keys()) == {"01_intro.md", "02_methods.md"}

    def test_excludes_preamble_by_default(self, tmp_path: Path):
        (tmp_path / "preamble.md").write_text("LaTeX")
        (tmp_path / "01_intro.md").write_text("Intro body.")
        files = read_manuscript_dir(tmp_path)
        assert "preamble.md" not in files

    def test_excludes_documentation_files_by_default(self, tmp_path: Path):
        """AGENTS.md, README.md, SYNTAX.md are documentation, not prose
        — they should not be analysed for readability or cite checking."""
        (tmp_path / "AGENTS.md").write_text("# Agents")
        (tmp_path / "README.md").write_text("# Readme")
        (tmp_path / "SYNTAX.md").write_text("# Syntax")
        (tmp_path / "01_intro.md").write_text("Intro body.")
        files = read_manuscript_dir(tmp_path)
        assert set(files.keys()) == {"01_intro.md"}

    def test_sorted_keys(self, tmp_path: Path):
        for name in ["03_c.md", "01_a.md", "02_b.md"]:
            (tmp_path / name).write_text("body")
        files = read_manuscript_dir(tmp_path)
        assert list(files.keys()) == ["01_a.md", "02_b.md", "03_c.md"]
