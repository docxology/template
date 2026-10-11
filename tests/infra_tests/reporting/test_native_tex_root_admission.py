"""Producer and portable replay share finite TeX distribution-leaf admission."""

from pathlib import Path
import time

import pytest

from infrastructure.reporting.native_format_tex_reference import (
    admitted_texmf_roots,
    observe_tex_reference,
    canonical_texmf_path,
    validate_texmf_installation,
    texmf_dependency_admitted,
)


@pytest.mark.parametrize(
    "installation", ["/usr/local/texlive/2026basic", "/opt/homebrew/Cellar/texlive/2026/share", "/usr/share/texlive"]
)
def test_distribution_leaves_exclude_local_auxiliary_and_broad_roots(installation: str) -> None:
    root = Path(installation)
    dist = root / "texmf-dist"
    leaves = (dist, root / "texmf-var", root / "texmf-config")
    ambient = (
        root,
        Path("/"),
        Path("/tmp"),
        Path("/usr/local/share/texmf"),
        root / "texmf-local",
        Path("/home/user/texmf"),
    )
    assert admitted_texmf_roots(dist, root, (*ambient, *leaves), Path("/private/run")) == tuple(sorted(leaves))


def test_debian_split_distribution_is_explicit_and_not_a_generic_search_path() -> None:
    root = Path("/usr/share/texlive")
    split = tuple(map(Path, ("/usr/share/texmf", "/var/lib/texmf", "/etc/texmf")))
    dist = root / "texmf-dist"
    assert admitted_texmf_roots(dist, root, split, Path("/tmp/private/run")) == tuple(sorted((dist, *split)))
    other = Path("/opt/texlive")
    assert admitted_texmf_roots(other / "texmf-dist", other, split, Path("/tmp/private/run")) == (other / "texmf-dist",)


@pytest.mark.parametrize("private", ["/vendor", "/vendor/texmf-dist", "/vendor/texmf-dist/run"])
def test_private_ancestor_equal_and_descendant_are_refused(private: str) -> None:
    with pytest.raises(ValueError, match="overlaps private"):
        admitted_texmf_roots(Path("/vendor/texmf-dist"), Path("/vendor"), (), Path(private))


@pytest.mark.parametrize("dist", ["/tmp/texmf", "/texmf-dist", "/vendor/texmf-dist/../local"])
def test_unrelated_or_noncanonical_distribution_leaf_is_refused(dist: str) -> None:
    with pytest.raises(ValueError, match="installation leaf|tree is invalid"):
        admitted_texmf_roots(Path(dist), Path("/vendor"), (), Path("/private/run"))


@pytest.mark.parametrize(
    "name",
    [
        "TEXMF",
        "TEXMFROOT",
        "TEXMFDIST",
        "TEXMFCNF",
        "TEXMFAUXTREES",
        "TEXMFLOCAL",
        "TEXINPUTS",
        "TFMFONTS",
        "SELFAUTOPARENT",
    ],
)
def test_ambient_routing_is_refused_before_source_or_tool_execution(tmp_path: Path, name: str) -> None:
    directory = tmp_path / "uncreated"
    with pytest.raises(ValueError, match="ambient TeX routing"):
        observe_tex_reference(
            tmp_path, directory, b"unused", env={name: str(tmp_path)}, deadline=time.monotonic() + 10, run_id="0" * 32
        )
    assert not directory.exists()


@pytest.mark.parametrize(
    "root,tool",
    [
        ("/usr/share/texlive", "/usr/bin/kpsewhich"),
        ("/usr/local/texlive/2026", "/usr/local/texlive/2026/bin/universal-darwin/kpsewhich"),
        ("/opt/homebrew/Cellar/texlive/2026/share", "/opt/homebrew/Cellar/texlive/2026/bin/kpsewhich"),
    ],
)
def test_locator_matches_actual_selected_kpathsea_layout(root: str, tool: str) -> None:
    validate_texmf_installation(Path(root), Path(tool))


@pytest.mark.parametrize("root", ["/", "/tmp/vendor", "/usr/local/share"])
def test_config_cannot_redirect_locator_away_from_selected_executable(root: str) -> None:
    with pytest.raises(ValueError, match="differs from its Kpathsea"):
        validate_texmf_installation(Path(root), Path("/usr/bin/kpsewhich"))


def test_source_discovery_retains_canonical_absolute_query_labels(tmp_path: Path) -> None:
    real = tmp_path / "texmf-dist"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    assert canonical_texmf_path(str(real)) == real
    for label in (
        str(alias),
        "relative/texmf-dist",
        str(real / ".." / "texmf-dist"),
        str(real) + "/./",
        str(real) + "//",
    ):
        with pytest.raises(ValueError, match="invalid or noncanonical"):
            canonical_texmf_path(label)


def test_distribution_config_is_an_exact_file_not_a_parent_directory() -> None:
    install = Path("/usr/local/texlive/2026basic")
    roots = (install / "texmf-dist",)
    assert texmf_dependency_admitted(install / "texmf.cnf", roots, install)
    assert texmf_dependency_admitted(roots[0] / "tex/latex/base/article.cls", roots, install)
    for path in (
        install,
        install / "unrelated.sty",
        install / "texmf-local/private.sty",
        install / "texmf.cnf/payload",
    ):
        assert not texmf_dependency_admitted(path, roots, install)
