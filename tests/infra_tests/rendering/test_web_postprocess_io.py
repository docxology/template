"""Real filesystem regressions for atomic publication HTML updates."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import stat

import pytest

from infrastructure.rendering._web_postprocess import deployed_web_link_issues, write_if_changed


def test_html_update_does_not_follow_predictable_temporary_symlink(tmp_path: Path) -> None:
    page = tmp_path / "index.html"
    page.write_text("original", encoding="utf-8")
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("preserve me", encoding="utf-8")
    planted = page.with_suffix(".html.tmp")
    planted.symlink_to(unrelated)

    write_if_changed(page, "replacement")

    assert unrelated.read_text(encoding="utf-8") == "preserve me"
    assert planted.is_symlink()
    assert not page.is_symlink()
    assert page.read_text(encoding="utf-8") == "replacement"


def test_unchanged_html_preserves_inode_and_modification_time(tmp_path: Path) -> None:
    page = tmp_path / "index.html"
    page.write_text("unchanged", encoding="utf-8")
    before = page.stat()

    write_if_changed(page, "unchanged")

    after = page.stat()
    assert (after.st_ino, after.st_mtime_ns) == (before.st_ino, before.st_mtime_ns)
    assert set(tmp_path.iterdir()) == {page}


def test_html_update_preserves_file_permissions(tmp_path: Path) -> None:
    page = tmp_path / "index.html"
    page.write_text("original", encoding="utf-8")
    page.chmod(0o640)

    write_if_changed(page, "replacement")

    assert stat.S_IMODE(page.stat().st_mode) == 0o640
    assert page.read_text(encoding="utf-8") == "replacement"
    assert set(tmp_path.iterdir()) == {page}


def test_encoding_failure_preserves_original_and_cleans_owned_temporary(tmp_path: Path) -> None:
    page = tmp_path / "index.html"
    page.write_text("original", encoding="utf-8")

    with pytest.raises(UnicodeEncodeError):
        write_if_changed(page, "invalid surrogate: \ud800")

    assert page.read_text(encoding="utf-8") == "original"
    assert set(tmp_path.iterdir()) == {page}


def test_concurrent_html_updates_leave_one_complete_artifact(tmp_path: Path) -> None:
    page = tmp_path / "index.html"
    page.write_text("original", encoding="utf-8")
    contents = [f"<html>{str(index) * 100_000}</html>" for index in range(8)]

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda content: write_if_changed(page, content), contents))

    assert page.read_text(encoding="utf-8") in contents
    assert set(tmp_path.iterdir()) == {page}


@pytest.mark.parametrize("href", ["javascript:", "data:#fragment", "file:", "javascript:alert(1)"])
def test_deployed_links_reject_unsupported_schemes_even_without_path(tmp_path: Path, href: str) -> None:
    (tmp_path / "index.html").write_text(f'<a href="{href}">Unsupported</a>', encoding="utf-8")

    issues = deployed_web_link_issues(tmp_path)

    assert len(issues) == 1
    assert "unsupported href scheme" in issues[0]
    assert href in issues[0]
