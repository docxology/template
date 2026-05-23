"""Tests for infrastructure.validation.docs.cross_link_lint.

Zero-mocks: tests build a real on-disk Markdown tree and verify resolution.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.cross_link_lint import (
    BrokenLink,
    detect_markdown_link_cycles,
    find_broken_links,
)


def _write(p: Path, body: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def test_find_broken_links_resolves_relative_targets(tmp_path: Path) -> None:
    target = tmp_path / "guide.md"
    _write(target, "# guide")
    md = tmp_path / "index.md"
    _write(
        md,
        """[ok](guide.md)
[bad](missing.md)
""",
    )
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert isinstance(broken[0], BrokenLink)
    assert broken[0].target == "missing.md"
    assert broken[0].file == md


def test_find_broken_links_skips_external_urls(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(
        md,
        """[home](https://example.com)
[mail](mailto:foo@bar)
[ftp](ftp://example.com/file)
""",
    )
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_anchor_only_links(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(md, "[top](#heading)\n")
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_fenced_code_blocks(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(
        md,
        """Outside link:
```
[fake](nope.md)
```

```python
[also fake](nope2.md)
```
""",
    )
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_indented_fenced_code_blocks(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(
        md,
        """A list:

- bullet:

    ```
    [fake](nope.md)
    ```
""",
    )
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_inline_single_backtick_links(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(md, "Use `[fake](nope.md)` syntax for links.\n")
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_inline_double_backtick_links(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(md, "Use ``[fake](nope.md)`` for `inline` examples.\n")
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_handles_anchored_targets(tmp_path: Path) -> None:
    target = tmp_path / "guide.md"
    _write(target, "# guide")
    md = tmp_path / "index.md"
    _write(
        md,
        """[good with anchor](guide.md#heading)
[bad with anchor](missing.md#heading)
""",
    )
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert "missing.md#heading" in broken[0].target


def test_find_broken_links_reports_correct_line_number(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(
        md,
        """line 1
line 2
[bad](missing.md)
line 4
""",
    )
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert broken[0].line == 3


def test_find_broken_links_preserves_original_text_in_inline_code(tmp_path: Path) -> None:
    """Even with inline-code stripping, the BrokenLink.text should be the source text."""
    target = tmp_path / "g.md"
    _write(target, "# g")
    md = tmp_path / "p.md"
    _write(md, "Some [`backtick text`](missing.md) here.\n")
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert broken[0].text == "`backtick text`"


def test_find_broken_links_excludes_default_dirs(tmp_path: Path) -> None:
    bad = tmp_path / "output" / "ignored.md"
    _write(bad, "[bad](nope.md)\n")
    good = tmp_path / "docs" / "live.md"
    _write(good, "# live")
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_format_returns_string() -> None:
    bl = BrokenLink(
        file=Path("/x/y.md"),
        line=42,
        text="hi",
        target="nope.md",
        reason="target does not exist on disk",
    )
    s = bl.format()
    assert "/x/y.md:42" in s
    assert "[hi](nope.md)" in s
    assert "target does not exist" in s


def test_detect_markdown_link_cycles_finds_two_node_cycle(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    _write(a, "[to b](b.md)\n")
    _write(b, "[to a](a.md)\n")
    cycles = detect_markdown_link_cycles([tmp_path])
    assert len(cycles) >= 1
    cycle_nodes = {Path(node).name for node in cycles[0].files}
    assert {"a.md", "b.md"}.issubset(cycle_nodes)
