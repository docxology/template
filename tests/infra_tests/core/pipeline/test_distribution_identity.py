"""Installed metadata identity preserves observed versions and remains fresh."""

from pathlib import Path

from infrastructure.core.pipeline.fingerprints import _distribution_identity


def test_distribution_identity_preserves_versions_and_freshness(tmp_path: Path) -> None:
    for directory, filename, contents in (
        ("first-1.dist-info", "METADATA", "Name: repeated\nVersion: 1\n"),
        ("second-2.egg-info", "PKG-INFO", "Name: repeated\nVersion: 2\n"),
    ):
        target = tmp_path / directory / filename
        target.parent.mkdir()
        target.write_text(contents)
    paths = [str(tmp_path)]
    assert _distribution_identity(paths) == [("repeated", "1"), ("repeated", "2")]
    (tmp_path / "first-1.dist-info/METADATA").write_text("Name: repeated\nVersion: 7\n")
    assert _distribution_identity(paths) == [("repeated", "2"), ("repeated", "7")]
    (tmp_path / "second-2.egg-info/PKG-INFO").write_text("Name: renamed\nVersion: 3\n")
    assert _distribution_identity(paths) == [("renamed", "3"), ("repeated", "7")]
