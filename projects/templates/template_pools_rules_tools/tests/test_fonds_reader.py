"""test_fonds_reader.py — Tests for fonds_reader.py using real fond exemplars.

Tests skip gracefully when the expected fond files are absent (other subagents
may still be populating them). When files are present, tests assert real data
properties.  Includes edge-case tests for corrupted CSV, empty CSV, and missing
data directories.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

# Ensure src/ is importable when running pytest from the project root
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from src.fonds_reader import (
    get_fonds_root,
    read_all_fonds,
    read_bibliography_fond,
    read_contacts_fond,
    read_datasets_fond,
)

# ---------------------------------------------------------------------------
# Path checks (used in skipif guards)
# ---------------------------------------------------------------------------

_BIB_DIR = get_fonds_root() / "template_bibliography"
_BIB_BIB = _BIB_DIR / "data" / "references.bib"
_BIB_CSV = _BIB_DIR / "data" / "references.csv"
_BIB_YAML = _BIB_DIR / "fonds.yaml"

_CONTACTS_DIR = get_fonds_root() / "template_contacts"
_CONTACTS_YAML = _CONTACTS_DIR / "data" / "contacts.yaml"
_CONTACTS_FONDS = _CONTACTS_DIR / "fonds.yaml"

_DATASETS_DIR = get_fonds_root() / "template_datasets"
_DATASETS_YAML = _DATASETS_DIR / "data" / "datasets.yaml"
_DATASETS_FONDS = _DATASETS_DIR / "fonds.yaml"


# ---------------------------------------------------------------------------
# bibliography fond
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (_BIB_YAML.exists() and _BIB_BIB.exists() and _BIB_CSV.exists()),
    reason="template_bibliography fond files not present",
)
class TestBibliographyFond:
    def test_returns_dict(self):
        result = read_bibliography_fond()
        assert result is not None
        assert isinstance(result, dict)

    def test_manifest_has_type_bibliography(self):
        result = read_bibliography_fond()
        assert result is not None
        assert result["manifest"]["type"] == "bibliography"

    def test_manifest_has_version(self):
        result = read_bibliography_fond()
        assert result is not None
        assert "version" in result["manifest"]

    def test_bib_text_is_nonempty(self):
        result = read_bibliography_fond()
        assert result is not None
        assert len(result["bib_text"].strip()) > 0

    def test_bib_text_contains_entry(self):
        result = read_bibliography_fond()
        assert result is not None
        assert "@article" in result["bib_text"] or "@inproceedings" in result["bib_text"]

    def test_csv_rows_nonempty(self):
        result = read_bibliography_fond()
        assert result is not None
        assert len(result["csv_rows"]) > 0

    def test_csv_rows_have_required_columns(self):
        result = read_bibliography_fond()
        assert result is not None
        required = {"key", "type", "title", "author", "year"}
        for row in result["csv_rows"]:
            assert required <= set(row.keys()), f"Missing columns in row: {row}"

    def test_csv_keys_are_unique(self):
        result = read_bibliography_fond()
        assert result is not None
        keys = [row["key"] for row in result["csv_rows"]]
        assert len(keys) == len(set(keys)), "Duplicate cite keys found"

    def test_missing_fond_returns_none(self):
        result = read_bibliography_fond(fond_name="__nonexistent_fond__")
        assert result is None


# ---------------------------------------------------------------------------
# contacts fond
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (_CONTACTS_FONDS.exists() and _CONTACTS_YAML.exists()),
    reason="template_contacts fond files not present",
)
class TestContactsFond:
    def test_returns_dict(self):
        result = read_contacts_fond()
        assert result is not None
        assert isinstance(result, dict)

    def test_manifest_has_type_contacts(self):
        result = read_contacts_fond()
        assert result is not None
        assert result["manifest"]["type"] == "contacts"

    def test_contacts_is_list(self):
        result = read_contacts_fond()
        assert result is not None
        assert isinstance(result["contacts"], list)

    def test_contacts_nonempty(self):
        result = read_contacts_fond()
        assert result is not None
        assert len(result["contacts"]) > 0

    def test_contacts_have_required_fields(self):
        result = read_contacts_fond()
        assert result is not None
        required = {"id", "name", "email"}
        for contact in result["contacts"]:
            assert required <= set(contact.keys()), f"Missing fields: {contact}"

    def test_contact_ids_are_unique(self):
        result = read_contacts_fond()
        assert result is not None
        ids = [c["id"] for c in result["contacts"]]
        assert len(ids) == len(set(ids)), "Duplicate contact ids found"

    def test_missing_fond_returns_none(self):
        result = read_contacts_fond(fond_name="__nonexistent_fond__")
        assert result is None


# ---------------------------------------------------------------------------
# datasets fond
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (_DATASETS_FONDS.exists() and _DATASETS_YAML.exists()),
    reason="template_datasets fond files not present",
)
class TestDatasetsFond:
    def test_returns_dict(self):
        result = read_datasets_fond()
        assert result is not None
        assert isinstance(result, dict)

    def test_manifest_has_type_datasets(self):
        result = read_datasets_fond()
        assert result is not None
        assert result["manifest"]["type"] == "datasets"

    def test_datasets_is_list(self):
        result = read_datasets_fond()
        assert result is not None
        assert isinstance(result["datasets"], list)

    def test_datasets_nonempty(self):
        result = read_datasets_fond()
        assert result is not None
        assert len(result["datasets"]) > 0

    def test_datasets_have_required_fields(self):
        result = read_datasets_fond()
        assert result is not None
        required = {"id", "name", "version", "license"}
        for ds in result["datasets"]:
            assert required <= set(ds.keys()), f"Missing fields: {ds}"

    def test_dataset_ids_are_unique(self):
        result = read_datasets_fond()
        assert result is not None
        ids = [d["id"] for d in result["datasets"]]
        assert len(ids) == len(set(ids)), "Duplicate dataset ids found"

    def test_missing_fond_returns_none(self):
        result = read_datasets_fond(fond_name="__nonexistent_fond__")
        assert result is None


# ---------------------------------------------------------------------------
# Edge cases: corrupted CSV handling
# ---------------------------------------------------------------------------


class TestCorruptedCSVHandling:
    """read_bibliography_fond must return None when the CSV is corrupted."""

    def _make_bib_fond(
        self,
        tmp_path: pathlib.Path,
        csv_content: str,
        bib_content: str = "@article{test2024, title={T}, author={A}, year={2024}}\n",
        manifest_content: str = "type: bibliography\nversion: 1.0\n",
    ) -> pathlib.Path:
        """Create a minimal fake bibliography fond under tmp_path."""
        fond_dir = tmp_path / "template_bibliography"
        (fond_dir / "data").mkdir(parents=True)
        (fond_dir / "fonds.yaml").write_text(manifest_content)
        (fond_dir / "data" / "references.bib").write_text(bib_content)
        (fond_dir / "data" / "references.csv").write_text(csv_content)
        return fond_dir

    def test_binary_garbage_in_csv_returns_none(self, tmp_path: pathlib.Path):
        import src.fonds_reader as fr

        # Write raw binary that is not valid UTF-8
        fond_dir = tmp_path / "template_bibliography"
        (fond_dir / "data").mkdir(parents=True)
        (fond_dir / "fonds.yaml").write_text("type: bibliography\nversion: 1.0\n")
        (fond_dir / "data" / "references.bib").write_text("@article{x,}\n")
        (fond_dir / "data" / "references.csv").write_bytes(b"\xff\xfe binary \x00 garbage")

        original_root = fr._fonds_root  # noqa: SLF001
        fr._fonds_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = read_bibliography_fond()
            # Should return None (read error caught) not raise
            assert result is None
        finally:
            fr._fonds_root = original_root  # type: ignore[assignment]

    def test_valid_csv_is_parsed_correctly(self, tmp_path: pathlib.Path):
        """Sanity-check: a well-formed CSV round-trips through DictReader."""
        import src.fonds_reader as fr

        csv_content = "key,type,title,author,year\nsmith2024,article,A Title,Smith,2024\n"
        self._make_bib_fond(tmp_path, csv_content=csv_content)

        original_root = fr._fonds_root  # noqa: SLF001
        fr._fonds_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = read_bibliography_fond()
            assert result is not None
            assert len(result["csv_rows"]) == 1
            assert result["csv_rows"][0]["key"] == "smith2024"
        finally:
            fr._fonds_root = original_root  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Edge cases: empty CSV handling
# ---------------------------------------------------------------------------


class TestEmptyCSVHandling:
    """An empty CSV file (header-only or truly empty) must not cause a crash."""

    def test_header_only_csv_returns_empty_list(self, tmp_path: pathlib.Path):
        """CSV with only a header row → csv_rows should be []."""
        import src.fonds_reader as fr

        fond_dir = tmp_path / "template_bibliography"
        (fond_dir / "data").mkdir(parents=True)
        (fond_dir / "fonds.yaml").write_text("type: bibliography\nversion: 1.0\n")
        (fond_dir / "data" / "references.bib").write_text("@article{x,}\n")
        # Header-only CSV — DictReader returns no rows
        (fond_dir / "data" / "references.csv").write_text("key,type,title,author,year\n")

        original_root = fr._fonds_root  # noqa: SLF001
        fr._fonds_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = read_bibliography_fond()
            assert result is not None
            assert result["csv_rows"] == []
        finally:
            fr._fonds_root = original_root  # type: ignore[assignment]

    def test_completely_empty_csv_returns_empty_list(self, tmp_path: pathlib.Path):
        """Truly empty CSV → csv_rows == []."""
        import src.fonds_reader as fr

        fond_dir = tmp_path / "template_bibliography"
        (fond_dir / "data").mkdir(parents=True)
        (fond_dir / "fonds.yaml").write_text("type: bibliography\nversion: 1.0\n")
        (fond_dir / "data" / "references.bib").write_text("@article{x,}\n")
        (fond_dir / "data" / "references.csv").write_text("")

        original_root = fr._fonds_root  # noqa: SLF001
        fr._fonds_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = read_bibliography_fond()
            assert result is not None
            assert result["csv_rows"] == []
        finally:
            fr._fonds_root = original_root  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Edge cases: missing data directory handling
# ---------------------------------------------------------------------------


class TestMissingDataDirectoryHandling:
    """When the fond's data/ subdirectory is absent, return None gracefully."""

    def test_missing_data_dir_bibliography_returns_none(self, tmp_path: pathlib.Path):
        import src.fonds_reader as fr

        fond_dir = tmp_path / "template_bibliography"
        fond_dir.mkdir(parents=True)
        # Write only fonds.yaml — no data/ subdir
        (fond_dir / "fonds.yaml").write_text("type: bibliography\nversion: 1.0\n")
        # data/ intentionally absent

        original_root = fr._fonds_root  # noqa: SLF001
        fr._fonds_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = read_bibliography_fond()
            assert result is None
        finally:
            fr._fonds_root = original_root  # type: ignore[assignment]

    def test_missing_data_dir_contacts_returns_none(self, tmp_path: pathlib.Path):
        import src.fonds_reader as fr

        fond_dir = tmp_path / "template_contacts"
        fond_dir.mkdir(parents=True)
        (fond_dir / "fonds.yaml").write_text("type: contacts\nversion: 1.0\n")

        original_root = fr._fonds_root  # noqa: SLF001
        fr._fonds_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = read_contacts_fond()
            assert result is None
        finally:
            fr._fonds_root = original_root  # type: ignore[assignment]

    def test_missing_data_dir_datasets_returns_none(self, tmp_path: pathlib.Path):
        import src.fonds_reader as fr

        fond_dir = tmp_path / "template_datasets"
        fond_dir.mkdir(parents=True)
        (fond_dir / "fonds.yaml").write_text("type: datasets\nversion: 1.0\n")

        original_root = fr._fonds_root  # noqa: SLF001
        fr._fonds_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = read_datasets_fond()
            assert result is None
        finally:
            fr._fonds_root = original_root  # type: ignore[assignment]

    def test_completely_absent_fonds_root_returns_none(self, tmp_path: pathlib.Path):
        """When the entire fonds root is missing, every reader returns None."""
        import src.fonds_reader as fr

        ghost_root = tmp_path / "does_not_exist"
        original_root = fr._fonds_root  # noqa: SLF001
        fr._fonds_root = lambda: ghost_root  # type: ignore[assignment]
        try:
            assert read_bibliography_fond() is None
            assert read_contacts_fond() is None
            assert read_datasets_fond() is None
        finally:
            fr._fonds_root = original_root  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# read_all_fonds consolidated loader
# ---------------------------------------------------------------------------


class TestReadAllFonds:
    def test_returns_dict(self):
        result = read_all_fonds()
        assert isinstance(result, dict)

    def test_has_expected_keys(self):
        result = read_all_fonds()
        assert set(result.keys()) == {"bibliography", "contacts", "datasets"}

    def test_values_are_none_or_dict(self):
        result = read_all_fonds()
        for key, value in result.items():
            assert value is None or isinstance(value, dict), (
                f"read_all_fonds[{key!r}] returned unexpected type: {type(value)}"
            )

    def test_never_raises(self):
        """read_all_fonds must not raise regardless of file system state."""
        result = read_all_fonds()
        assert isinstance(result, dict)
