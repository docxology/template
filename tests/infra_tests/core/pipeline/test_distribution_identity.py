"""Real installed-metadata observations retain stdlib fallback and freshness."""

from importlib.metadata import distributions
from pathlib import Path

from infrastructure.core.pipeline.fingerprints import _distribution_identity


def test_actual_metadata_and_pkg_info_match_stdlib_without_persistent_reuse(tmp_path: Path) -> None:
    for directory, filename, contents in (
        ("first-1.dist-info", "METADATA", "Name: repeated\nVersion: 1\n"),
        ("second-2.egg-info", "PKG-INFO", "Name: repeated\nVersion: 2\n"),
        ("third.dist-info", "METADATA", "Name: without-version\n"),
    ):
        target = tmp_path / directory / filename
        target.parent.mkdir()
        target.write_text(contents)
    paths = [str(tmp_path)]
    expected = sorted((str(item.metadata.get("Name", "")), item.version) for item in distributions(path=paths))
    assert (
        _distribution_identity(paths) == expected == [("repeated", "1"), ("repeated", "2"), ("without-version", None)]
    )
    (tmp_path / "first-1.dist-info/METADATA").write_text("Name: repeated\nVersion: 7\n")
    assert _distribution_identity(paths) == [("repeated", "2"), ("repeated", "7"), ("without-version", None)]
