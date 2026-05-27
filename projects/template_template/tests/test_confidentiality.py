"""Confidentiality negative-control tests for the template_template meta-project.

This meta-template is published as the 5th PUBLIC exemplar with a citable DOI.
Its repository introspection MUST therefore restrict to the public canonical
exemplars (``infrastructure.project.public_scope.PUBLIC_PROJECT_NAMES``) plus the
meta-project itself (emitted as ``template_template``). It must NEVER embed the
names of private/rotating projects — those live under symlinked ``projects_archive/``,
``projects_in_progress/``, and the private ``passive/`` / ``archive/`` lifecycle
trees.

These tests are the proof that the leak (a former ``projects_archive/`` scan in
``metrics.build_manuscript_metrics_dict``) is closed and stays closed. They are
Zero-Mock: every assertion runs against the real repository or a real synthetic
filesystem layout built under ``tmp_path``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

from template_template.introspection import (
    META_PROJECT_DIR_NAME,
    META_PROJECT_PUBLIC_NAME,
    discover_projects,
)
from template_template.metrics import build_manuscript_metrics_dict

from helpers import REPO_ROOT

# The complete set of project names allowed to appear in published metrics.
ALLOWED_PROJECT_NAMES = set(PUBLIC_PROJECT_NAMES) | {META_PROJECT_PUBLIC_NAME}

# Representative private/rotating names (and structural path fragments) that must
# never appear anywhere in the serialized metrics. Drawn from the lifecycle repo's
# passive/archive trees plus the structural directories that hold them.
PRIVATE_NAME_DENYLIST = (
    "AGEINT",
    "BeeStack",
    "Digi-PPPiP",
    "biology_textbook",
    "crescent_city",
    "elk_valley",
    "cohereants",
    "atlas",
    "encinitas",
    "entobots",
    "corym",
    "fep_lean",
    "blake_jiang",
    "template_search_project",
    "projects_archive",
    "projects_in_progress",
    "passive/",
    "/archive/",
)

# Matches the flat per-project metric keys, capturing the project name. The field
# suffix is a closed set, so the captured name is unambiguous even though project
# names themselves contain underscores.
_PROJECT_KEY_RE = re.compile(
    r"^project_(?P<name>.+)_"
    r"(?:chapter_count|figure_count|script_count|src_module_count|test_count|test_file_count)$"
)


def _project_names_in_metrics(metrics: dict[str, object]) -> set[str]:
    """Recover the set of project names embedded in ``project_*`` metric keys."""
    names: set[str] = set()
    for key in metrics:
        match = _PROJECT_KEY_RE.match(key)
        if match:
            names.add(match.group("name"))
    return names


class TestDiscoveredProjectsArePublicOnly:
    """``discover_projects`` and the metrics dict only expose allowed names."""

    def test_discovered_project_set_is_subset_of_allowed(self) -> None:
        names = {p.name for p in discover_projects(REPO_ROOT)}
        assert names, "discover_projects returned nothing — introspection is broken"
        assert names <= ALLOWED_PROJECT_NAMES, (
            f"Disallowed project(s) discovered: {sorted(names - ALLOWED_PROJECT_NAMES)}"
        )

    def test_metrics_project_names_are_subset_of_allowed(self) -> None:
        metrics = build_manuscript_metrics_dict(REPO_ROOT)
        names = _project_names_in_metrics(metrics)
        assert names, "No project_* metric keys found — self-introspection regressed"
        assert names <= ALLOWED_PROJECT_NAMES, (
            f"Disallowed project name(s) in metrics: {sorted(names - ALLOWED_PROJECT_NAMES)}"
        )

    def test_every_project_metric_key_has_an_allowed_prefix(self) -> None:
        """Belt-and-suspenders: no ``project_*`` key may use a non-allowed prefix."""
        metrics = build_manuscript_metrics_dict(REPO_ROOT)
        allowed_prefixes = tuple(f"project_{name}_" for name in ALLOWED_PROJECT_NAMES)
        offenders = [
            key
            for key in metrics
            if key.startswith("project_")
            and key != "project_count"
            and not key.startswith(allowed_prefixes)
        ]
        assert not offenders, f"Project metric keys with disallowed prefix: {offenders}"


class TestNoPrivateNamesInSerializedMetrics:
    """The serialized metrics JSON must contain zero private name substrings."""

    def test_serialized_metrics_contain_no_private_names(self) -> None:
        metrics = build_manuscript_metrics_dict(REPO_ROOT)
        blob = json.dumps(metrics)
        hits = [needle for needle in PRIVATE_NAME_DENYLIST if needle in blob]
        assert not hits, f"Private name(s)/path(s) leaked into metrics JSON: {hits}"


class TestSelfAndPublicIntrospectionStillWork:
    """Closing the leak must not break legitimate (public) introspection."""

    def test_meta_project_self_metric_present(self) -> None:
        metrics = build_manuscript_metrics_dict(REPO_ROOT)
        assert "project_template_template_test_count" in metrics, (
            "Meta-project self-introspection key missing — rename mapping regressed"
        )

    def test_public_exemplar_metrics_present(self) -> None:
        metrics = build_manuscript_metrics_dict(REPO_ROOT)
        for name in (
            "template_code_project",
            "template_autoresearch_project",
            "template_prose_project",
        ):
            assert f"project_{name}_test_count" in metrics, (
                f"Public exemplar '{name}' missing from metrics"
            )

    def test_bare_template_name_is_never_emitted(self) -> None:
        """The on-disk staging name ``template`` must be rewritten, never emitted."""
        metrics = build_manuscript_metrics_dict(REPO_ROOT)
        assert "project_template_test_count" not in metrics, (
            "Bare 'template' project key emitted — should be 'template_template'"
        )
        names = {p.name for p in discover_projects(REPO_ROOT)}
        assert META_PROJECT_DIR_NAME not in names or META_PROJECT_DIR_NAME == META_PROJECT_PUBLIC_NAME
        assert META_PROJECT_PUBLIC_NAME in names


class TestFlipTestSyntheticPrivateDirIsInvisible:
    """A newly-added private dir is structurally invisible to public introspection.

    This is the strongest proof: we build a real (Zero-Mock) synthetic repo layout
    under ``tmp_path`` containing BOTH a public-allowed project and a synthetic
    private project planted under ``projects_archive/``. The published, public-only
    discovery must surface the public project and never the synthetic private one.
    """

    @staticmethod
    def _write_project(root: Path, tree: str, name: str) -> None:
        """Create a minimal, valid manuscript project under ``root/<tree>/<name>``."""
        manuscript = root / tree / name / "manuscript"
        manuscript.mkdir(parents=True, exist_ok=True)
        (manuscript / "config.yaml").write_text(
            "paper:\n  title: Synthetic\n  version: '1.0'\n",
            encoding="utf-8",
        )
        (manuscript / "01_intro.md").write_text("# Intro\n", encoding="utf-8")

    def test_synthetic_archive_project_not_discovered(self, tmp_path: Path) -> None:
        # A genuinely public-allowed project (discoverable)...
        self._write_project(tmp_path, "projects", "template_code_project")
        # ...and a synthetic PRIVATE project planted exactly where the old leak read.
        self._write_project(tmp_path, "projects_archive", "SECRET_LEAK_PROJECT")
        # ...and another private one in projects_in_progress with a non-allowed name.
        self._write_project(tmp_path, "projects_in_progress", "ANOTHER_PRIVATE_ONE")

        discovered = {p.name for p in discover_projects(tmp_path)}

        assert "template_code_project" in discovered, (
            "Public project not discovered in synthetic repo — discovery is broken"
        )
        assert "SECRET_LEAK_PROJECT" not in discovered, (
            "Synthetic archive project was discovered — the leak is OPEN"
        )
        assert "ANOTHER_PRIVATE_ONE" not in discovered, (
            "Synthetic projects_in_progress project was discovered — the leak is OPEN"
        )
        assert discovered <= ALLOWED_PROJECT_NAMES

    def test_synthetic_archive_project_invisible_even_to_metrics_helper(
        self, tmp_path: Path
    ) -> None:
        """The archive tree is never even scanned: an archive-only project yields nothing.

        ``discover_projects`` does not walk ``projects_archive/`` at all, so an
        archive-only project (no public twin) produces an empty discovery set rather
        than leaking its name.
        """
        self._write_project(tmp_path, "projects_archive", "SECRET_ARCHIVE_ONLY")
        discovered = {p.name for p in discover_projects(tmp_path)}
        assert discovered == set(), (
            f"Archive tree was scanned — leaked: {sorted(discovered)}"
        )
