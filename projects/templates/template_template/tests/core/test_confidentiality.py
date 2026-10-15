"""Confidentiality negative-control tests for the template_template meta-project.

This meta-template is published as a PUBLIC exemplar with a citable DOI.
Its repository introspection MUST therefore restrict to the public canonical
exemplars (``infrastructure.project.public_scope.PUBLIC_PROJECT_NAMES``, which live
under ``projects/templates/``) plus the meta-project itself (emitted as
``template_template``). It must NEVER embed the names of private/rotating projects —
those live under the non-rendered typed subfolders
``projects/{working,published,archive,other}/`` (symlinked from the private
lifecycle repo).

These tests are the proof that the leak (a former private-tree scan in
``metrics.build_manuscript_metrics_dict``) is closed and stays closed. They are
Zero-Mock: every assertion runs against the real repository or a real synthetic
filesystem layout built under ``tmp_path``.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import infrastructure
import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

from template_template.core.introspection import (
    META_PROJECT_DIR_NAME,
    META_PROJECT_PUBLIC_NAME,
    discover_projects,
)
from template_template.metrics.metrics import build_manuscript_metrics_dict

from helpers import REPO_ROOT

# The complete set of project names allowed to appear in published metrics.
# ``discover_projects`` returns bare leaf names (metric keys are ``project_<leaf>_*``),
# while ``PUBLIC_PROJECT_NAMES`` is slash-qualified (``templates/template_*``).
ALLOWED_PROJECT_NAMES = {Path(name).name for name in PUBLIC_PROJECT_NAMES} | {META_PROJECT_PUBLIC_NAME}

# Representative private/rotating names (and structural path fragments) that must
# never appear anywhere in the serialized metrics. Drawn from the lifecycle repo's
# rotating trees plus the non-rendered typed subfolders that hold them. The legacy
# ``projects_archive`` / ``projects_in_progress`` tokens are retained as forbidden
# needles (defense-in-depth) even though those top-level dirs no longer exist.
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
    "projects_archive",
    "projects_in_progress",
    "projects/working/",
    "projects/published/",
    "projects/archive/",
    "projects/other/",
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
            if key.startswith("project_") and key != "project_count" and not key.startswith(allowed_prefixes)
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
            assert f"project_{name}_test_count" in metrics, f"Public exemplar '{name}' missing from metrics"

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
    under ``tmp_path`` containing BOTH a public-allowed exemplar (under
    ``projects/templates/``) and synthetic private projects planted under the
    non-rendered typed subfolders (``projects/working/``,
    ``projects/ongoing/``, ``projects/archive/``). The published, public-only discovery must surface the
    public exemplar and never the synthetic private ones.
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

    def test_synthetic_private_project_not_discovered(self, tmp_path: Path) -> None:
        # A genuinely public-allowed exemplar, in its git-tracked home...
        self._write_project(tmp_path, "projects/templates", "template_code_project")
        # ...and synthetic PRIVATE projects planted in the non-rendered typed subfolders.
        self._write_project(tmp_path, "projects/working", "SECRET_LEAK_PROJECT")
        self._write_project(tmp_path, "projects/ongoing", "ANOTHER_PRIVATE_ONE")
        self._write_project(tmp_path, "projects/archive", "RETIRED_PRIVATE_ONE")

        discovered = {p.name for p in discover_projects(tmp_path)}

        assert "template_code_project" in discovered, (
            "Public exemplar not discovered in synthetic repo — discovery is broken"
        )
        assert "SECRET_LEAK_PROJECT" not in discovered, (
            "Synthetic projects/working project was discovered — the leak is OPEN"
        )
        assert "ANOTHER_PRIVATE_ONE" not in discovered, (
            "Synthetic projects/other project was discovered — the leak is OPEN"
        )
        assert "RETIRED_PRIVATE_ONE" not in discovered, (
            "Synthetic projects/archive project was discovered — the leak is OPEN"
        )
        assert discovered <= ALLOWED_PROJECT_NAMES

    def test_synthetic_private_only_repo_yields_nothing(self, tmp_path: Path) -> None:
        """A repo with only non-allowed private projects produces an empty set.

        The name allowlist is the boundary: projects under the non-rendered typed
        subfolders whose leaf names are not public exemplars are filtered out, so a
        repo with no public twin discovers nothing rather than leaking a name.
        """
        self._write_project(tmp_path, "projects/archive", "SECRET_ARCHIVE_ONLY")
        self._write_project(tmp_path, "projects/working", "SECRET_WORKING_ONLY")
        discovered = {p.name for p in discover_projects(tmp_path)}
        assert discovered == set(), f"Private-only repo leaked names: {sorted(discovered)}"


@pytest.mark.parametrize("topology", ["copy", "link"])
def test_same_public_leaf_local_alias_is_live_only_in_explicit_local_discovery(tmp_path: Path, topology: str) -> None:
    """Prove actual alias reads, then require canonical public metric parity."""
    root = tmp_path / "owned-data"
    name = "template_code_project"
    TestFlipTestSyntheticPrivateDirIsInvisible._write_project(root, "projects/templates", name)
    canonical = root / "projects/templates" / name
    baseline = json.loads(json.dumps([asdict(row) for row in discover_projects(root)], default=str))
    assert len(baseline) == 1 and baseline[0]["path"] == str(canonical)
    aliases = (root / "projects/active" / name, root / "projects" / name)
    for alias in aliases:
        alias.parent.mkdir(parents=True, exist_ok=True)
        if topology == "copy":
            shutil.copytree(canonical, alias)
            (alias / "manuscript/config.yaml").write_text("paper:\n  title: Owned alias data\n", encoding="utf-8")
        else:
            alias.symlink_to(canonical, target_is_directory=True)
    marker = tmp_path / "actual-alias-content-opened"
    watched = [str(alias / "manuscript/config.yaml") for alias in aliases]
    project = Path(__file__).resolve().parents[2]
    selected_sdk = Path(infrastructure.__file__).resolve(strict=True)
    prefix = (
        "import importlib.util,json,os,sys;from dataclasses import asdict;from pathlib import Path;"
        f"project=Path({str(project)!r});"
        "spec=importlib.util.spec_from_file_location('own_template_bootstrap',project/'scripts/_bootstrap.py');"
        "assert spec is not None and spec.loader is not None;"
        "bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap);"
        "sdk=bootstrap.bootstrap_project(project);"
        f"assert Path(sdk.__file__).resolve()==Path({str(selected_sdk)!r});"
        "assert sdk.__version__=='4.0.2';"
        "from template_template.core.introspection import discover_projects;\n"
        f"watched={watched!r}\nmarker=Path({str(marker)!r})\n"
        "def audit(event,args):\n"
        "    if event=='open' and isinstance(args[0],(str,bytes)) and str(Path(os.fsdecode(args[0])).absolute()) in watched:\n"
        "        marker.write_text('actual alias config read')\n"
        "sys.addaudithook(audit)\n"
    )

    def run(public_only: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                prefix
                + f"rows=discover_projects(Path({str(root)!r}),public_only={public_only!r})\n"
                + "print(json.dumps({'projects':[asdict(row) for row in rows]},default=str))\n",
            ],
            cwd=tmp_path,
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )

    positive = run(False)
    assert positive.returncode == 0, positive.stderr or positive.stdout
    assert marker.read_text() == "actual alias config read"
    marker.unlink()
    actual = run(True)
    assert actual.returncode == 0, actual.stderr or actual.stdout
    assert not marker.exists()
    observed = [json.loads(line) for line in actual.stdout.splitlines() if line.startswith("{")]
    assert len(observed) == 1 and observed[0]["projects"] == baseline
    assert aliases[0].exists() and aliases[1].exists()


def test_canonical_public_workspace_redirection_is_refused(tmp_path: Path) -> None:
    TestFlipTestSyntheticPrivateDirIsInvisible._write_project(tmp_path, "owned-local", "template_code_project")
    canonical = tmp_path / "projects/templates/template_code_project"
    canonical.parent.mkdir(parents=True)
    canonical.symlink_to(tmp_path / "owned-local/template_code_project", target_is_directory=True)
    with pytest.raises(ValueError, match="cannot be redirected"):
        discover_projects(tmp_path)
