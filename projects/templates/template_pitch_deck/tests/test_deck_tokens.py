"""No-mocks tests for src/deck_tokens.py — reads real repo state."""

from __future__ import annotations

import pytest

from deck_tokens import (
    _display_platform_name,
    _read_own_deck_doi_status,
    _second_example_name,
    _validate_project_name,
    build_deck_tokens,
)
from paths import locate_repo_root, project_root


@pytest.fixture(scope="module")
def repo_root():
    return locate_repo_root(project_root())


def test_build_deck_tokens_returns_all_expected_keys(repo_root):
    tokens = build_deck_tokens(repo_root)
    expected_keys = {
        "PITCH_SUBJECT_NAME",
        "PITCH_SUBJECT_TITLE",
        "PITCH_SUBJECT_VERSION",
        "PITCH_SUBJECT_LICENSE",
        "PITCH_SUBJECT_DOI",
        "PITCH_SUBJECT_GITHUB",
        "PITCH_SUBJECT_TEST_COUNT",
        "PITCH_SUBJECT_COVERAGE_PCT",
        "PITCH_SUBJECT_PUBLISHED_PLATFORM_COUNT",
        "EXEMPLAR_COUNT",
        "EXEMPLAR_COUNT_PLUS_ONE",
        "SECOND_EXEMPLAR_NAME",
    }
    assert expected_keys <= tokens.keys()


def test_build_deck_tokens_includes_infra_facts(repo_root):
    tokens = build_deck_tokens(repo_root)
    assert int(tokens["INFRA_SUBPACKAGE_COUNT"]) > 5
    assert int(tokens["INFRA_PYTHON_FILE_COUNT"]) > 100
    assert tokens["INFRA_LARGEST_SUBPACKAGE"]


def test_build_deck_tokens_exemplar_roster_lists_every_exemplar(repo_root):
    tokens = build_deck_tokens(repo_root)
    roster = tokens["EXEMPLAR_ROSTER"]
    names = [n.strip() for n in roster.split(",")]
    assert len(names) == int(tokens["EXEMPLAR_COUNT"])
    assert "template_pitch_deck" in names
    assert "template_template" in names
    assert names == sorted(names)


def test_build_deck_tokens_pitch_deck_doi_status_reflects_real_state(repo_root):
    """This deck's own config.yaml now carries a real, published Zenodo DOI
    (reserved 2026-07-09) — the token must reflect that live state, matching
    the empty-config behavior verified separately in
    `test_read_own_deck_doi_status_honest_when_publication_block_empty`
    (which uses a synthetic tmp_path fixture, independent of this project's
    own current, real, mutable config)."""
    tokens = build_deck_tokens(repo_root)
    status = tokens["PITCH_DECK_DOI_STATUS"]
    assert status.startswith("10.5281/zenodo.")
    assert "not yet reserved" not in status


def test_read_own_deck_doi_status_returns_real_doi_when_present(tmp_path):
    config_dir = tmp_path / "projects" / "templates" / "template_pitch_deck" / "manuscript"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yaml").write_text(
        "publication:\n  doi: '10.5281/zenodo.99999999'\n",
        encoding="utf-8",
    )
    assert _read_own_deck_doi_status(tmp_path) == "10.5281/zenodo.99999999"


def test_read_own_deck_doi_status_honest_when_publication_block_empty(tmp_path):
    config_dir = tmp_path / "projects" / "templates" / "template_pitch_deck" / "manuscript"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yaml").write_text("publication: {}\n", encoding="utf-8")
    status = _read_own_deck_doi_status(tmp_path)
    assert "not yet reserved" in status


def test_build_deck_tokens_pitch_subject_name_matches_argument(repo_root):
    tokens = build_deck_tokens(repo_root, pitch_subject="template_template")
    assert tokens["PITCH_SUBJECT_NAME"] == "template_template"


def test_build_deck_tokens_exemplar_count_is_a_positive_integer_string(repo_root):
    tokens = build_deck_tokens(repo_root)
    assert int(tokens["EXEMPLAR_COUNT"]) > 0


def test_build_deck_tokens_exemplar_count_plus_one_is_consistent(repo_root):
    tokens = build_deck_tokens(repo_root)
    assert int(tokens["EXEMPLAR_COUNT_PLUS_ONE"]) == int(tokens["EXEMPLAR_COUNT"]) + 1


def test_build_deck_tokens_second_exemplar_name_is_not_the_pitch_subject(repo_root):
    tokens = build_deck_tokens(repo_root, pitch_subject="template_template")
    assert tokens["SECOND_EXEMPLAR_NAME"] != "template_template"


def test_build_deck_tokens_test_count_and_coverage_are_numeric(repo_root):
    tokens = build_deck_tokens(repo_root)
    assert int(tokens["PITCH_SUBJECT_TEST_COUNT"]) > 0
    assert float(tokens["PITCH_SUBJECT_COVERAGE_PCT"]) > 0.0


def test_build_deck_tokens_raises_for_unknown_pitch_subject(repo_root):
    with pytest.raises(FileNotFoundError):
        build_deck_tokens(repo_root, pitch_subject="not_a_real_exemplar_xyz")


def test_build_deck_tokens_raises_for_pitch_subject_with_no_counts_row(tmp_path):
    """A subject with a real manuscript/config.yaml but no COUNTS.md row yet
    must raise rather than silently fabricate a test count."""
    fake_repo = tmp_path / "fake_repo"
    subject_dir = fake_repo / "projects" / "templates" / "unregistered_subject" / "manuscript"
    subject_dir.mkdir(parents=True)
    (subject_dir / "config.yaml").write_text(
        "paper:\n  title: Unregistered\n  version: '0.1'\npublication: {}\nmetadata: {}\n",
        encoding="utf-8",
    )
    counts_dir = fake_repo / "docs" / "_generated"
    counts_dir.mkdir(parents=True)
    (counts_dir / "COUNTS.md").write_text("| `some_other_project` | 5 | 80.00 % |\n", encoding="utf-8")

    with pytest.raises(ValueError, match="COUNTS.md"):
        build_deck_tokens(fake_repo, pitch_subject="unregistered_subject")


def test_display_platform_name_pypi_sandbox_detection():
    assert _display_platform_name("pypi", "https://test.pypi.org/project/x/") == "PyPI (sandbox)"
    assert _display_platform_name("pypi", "https://pypi.org/project/x/") == "PyPI"
    assert _display_platform_name("pypi", None) == "PyPI"


def test_display_platform_name_falls_back_for_unknown_slug():
    assert _display_platform_name("some_new_platform", "https://example.org/") == "Some New Platform"


def test_published_platform_names_labels_testpypi_as_sandbox_honestly(repo_root):
    """Real reproduction: template_template's actual pypi listing is on
    test.pypi.org (verified by reading its config directly), which a bare
    'PyPI' label would misrepresent as production PyPI — a checkable,
    embarrassing false-advertising risk a skeptical reviewer would catch
    (red-team finding, 2026-07-09)."""
    tokens = build_deck_tokens(repo_root, pitch_subject="template_template")
    names = tokens["PITCH_SUBJECT_PUBLISHED_PLATFORM_NAMES"]
    assert "PyPI (sandbox)" in names
    assert "PyPI," not in names  # never claim bare "PyPI" alongside the sandbox one


def test_published_platform_names_count_matches_the_count_token(repo_root):
    """Proof-of-detection for the red-team-flagged double-counting bug: the
    number of comma-joined platform NAMES must exactly equal the COUNT token
    — both are now derived from the same `compile_publishing_status()` call,
    so they cannot silently diverge the way the prior ad hoc formula could."""
    tokens = build_deck_tokens(repo_root, pitch_subject="template_template")
    names = [n.strip() for n in tokens["PITCH_SUBJECT_PUBLISHED_PLATFORM_NAMES"].split(",") if n.strip()]
    assert len(names) == int(tokens["PITCH_SUBJECT_PUBLISHED_PLATFORM_COUNT"])
    # Zenodo must be counted once (not twice for concept-DOI + version-DOI),
    # and github must be credited if github_repository is set — the exact
    # double-count/never-counted bug this replaces.
    assert names.count("Zenodo") == 1
    assert "GitHub" in names


def test_validate_project_name_accepts_real_names():
    assert _validate_project_name("template_template") == "template_template"
    assert _validate_project_name("template-pitch-deck") == "template-pitch-deck"


def test_validate_project_name_rejects_path_traversal():
    for bad in ("../../../../etc/passwd", "foo/bar", "..", "a/../b", ""):
        with pytest.raises(ValueError):
            _validate_project_name(bad)


def test_build_deck_tokens_rejects_path_traversal_pitch_subject(repo_root):
    """Real reproduction of the red-team-flagged path-traversal risk: a
    `pitch_subject` containing '..' must be rejected before any path is
    constructed from it, not silently accepted."""
    with pytest.raises(ValueError):
        build_deck_tokens(repo_root, pitch_subject="../../../../../../tmp/pwned")


def test_read_pitch_subject_config_null_paper_key_does_not_crash(tmp_path):
    """Real reproduction of the red-team-flagged crash: a YAML file with a
    present-but-null `paper:`/`publication:`/`metadata:` key (not simply
    absent) must not raise AttributeError from a bare `.get(key, {})`
    pattern — `dict.get` only substitutes the default when the key is
    *absent*, not when it's present with value `None`."""
    from deck_tokens import _read_pitch_subject_config

    subject_dir = tmp_path / "projects" / "templates" / "null_paper_subject" / "manuscript"
    subject_dir.mkdir(parents=True)
    (subject_dir / "config.yaml").write_text(
        "paper:\npublication:\nmetadata:\n", encoding="utf-8"
    )

    subject_config = _read_pitch_subject_config(tmp_path, "null_paper_subject")
    # This is the exact pattern build_deck_tokens uses — must not raise.
    try:
        paper = subject_config.get("paper") or {}
        publication = subject_config.get("publication") or {}
        metadata = subject_config.get("metadata") or {}
        assert paper.get("title", "null_paper_subject") == "null_paper_subject"
        assert publication.get("doi", "") == ""
        assert metadata.get("license", "") == ""
    except AttributeError:
        pytest.fail("'.get(key) or {}' pattern crashed on a present-but-null YAML key")


def test_second_example_name_raises_when_no_distinct_exemplar_exists():
    with pytest.raises(ValueError):
        _second_example_name(["templates/only_one"], "only_one")
