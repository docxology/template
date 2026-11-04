"""Characterization contract for the three passive resource pools.

``infrastructure/fonds/``, ``infrastructure/rules/`` and
``infrastructure/tools/`` are three parallel copies of one design: discovery,
validation, an info dataclass, and a public-scope filter, differing only by the
pool noun, the manifest filename, and the required layout.

This module pins the shared contract **before** any consolidation, so a generic
pool engine (W1) can be proven behaviour-preserving instead of assumed to be.
Every test is parametrized over the three pools and asserts the same shape; the
only per-pool expectations are the documented ones (manifest name, required
directory, message wording, type default).

Real directories under ``tmp_path`` are used throughout (no mocks), matching the
per-pool suites in ``tests/infra_tests/{fonds,rules,tools}/``. Those suites keep
their pool-specific coverage; this one owns the cross-pool contract.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

#: The three passive pools, in discovery order used by ``orchestration/link_sync``.
POOLS: tuple[str, ...] = ("fonds", "rules", "tools")

#: Singular noun per pool, used to derive the public names.
NOUN: dict[str, str] = {"fonds": "fond", "rules": "rule", "tools": "tool"}

#: Per-pool structural facts a shared engine has to parameterize.
STRUCTURE: dict[str, dict[str, Any]] = {
    "fonds": {
        "manifest": "fonds.yaml",
        "required_dir_message": "Missing required directory: data",
        "type_default": "generic",
        # presence fields in dataclass order, mapped to the directory each one observes
        "presence_dirs": (("has_data", "data"), ("has_manuscript", "manuscript")),
        # directories whose presence alone makes ``is_valid`` true
        "valid_dirs": ("data",),
        "optional_dirs": ("manuscript", "scripts", "tests"),
    },
    "rules": {
        "manifest": "rules.yaml",
        "required_dir_message": "Missing required directory: at least one of soft/ or strong/ must exist",
        "type_default": "project",
        "presence_dirs": (("has_soft", "soft"), ("has_strong", "strong")),
        "valid_dirs": ("soft", "strong"),
        "optional_dirs": ("scripts", "tests", "examples"),
    },
    "tools": {
        "manifest": "tools.yaml",
        "required_dir_message": "Missing required directory: scripts",
        "type_default": "generic",
        "presence_dirs": (("has_scripts", "scripts"), ("has_tests", "tests")),
        "valid_dirs": ("scripts",),
        "optional_dirs": ("tests", "docs"),
    },
}

#: Repository root of this checkout (``tests/infra_tests/core/<this file>``).
REPO_ROOT: Path = Path(__file__).resolve().parents[3]


def _api(pool: str) -> SimpleNamespace:
    """Return the pool's package plus its named public callables."""
    noun = NOUN[pool]
    upper = pool.upper()
    package = importlib.import_module(f"infrastructure.{pool}")
    discovery = importlib.import_module(f"infrastructure.{pool}.discovery")
    info = importlib.import_module(f"infrastructure.{pool}.{pool}_info")
    validation = importlib.import_module(f"infrastructure.{pool}.validation")
    scope = importlib.import_module(f"infrastructure.{pool}.public_scope")
    return SimpleNamespace(
        pool=pool,
        noun=noun,
        upper=upper,
        package=package,
        discovery=discovery,
        info_module=info,
        validation=validation,
        scope=scope,
        discover=getattr(package, f"discover_{pool}"),
        resolve=getattr(package, f"resolve_{noun}_root"),
        validate=getattr(package, f"validate_{noun}_structure"),
        build=getattr(package, f"build_{noun}_info"),
        info_cls=getattr(package, f"{noun.capitalize()}Info"),
        public_names=getattr(scope, f"public_{noun}_names"),
        public_infos=getattr(scope, f"public_{noun}_infos"),
        roster=getattr(scope, f"PUBLIC_{noun.upper()}_NAMES"),
        non_rendered=getattr(discovery, f"NON_RENDERED_{noun.upper()}_SUBDIRS"),
        rendered=getattr(discovery, f"RENDERED_{noun.upper()}_SUBDIRS"),
    )


def _make_pool_dir(pool: str, root: Path, relative: str, *, valid: bool = True, manifest_extra: str = "") -> Path:
    """Create ``<root>/<pool>/<relative>`` with a valid or invalid pool layout."""
    target = root / pool / relative
    target.mkdir(parents=True, exist_ok=True)
    if valid:
        manifest = target / STRUCTURE[pool]["manifest"]
        manifest.write_text(f"type: demo\n{manifest_extra}", encoding="utf-8")
        for required in STRUCTURE[pool]["valid_dirs"][:1]:
            (target / required).mkdir(exist_ok=True)
    return target


def _canonical(name: str, pool: str) -> str:
    """Normalize a public name by removing the pool noun, so pools can be compared."""
    noun = NOUN[pool]
    capitalized = noun.capitalize()
    replacements = (
        (f"{capitalized}Info", "Info"),
        (f"build_{noun}_info", "build_info"),
        (f"discover_{pool}", "discover"),
        (f"resolve_{noun}_root", "resolve_root"),
        (f"validate_{noun}_structure", "validate_structure"),
        (f"NON_RENDERED_{noun.upper()}_SUBDIRS", "NON_RENDERED_SUBDIRS"),
        (f"RENDERED_{noun.upper()}_SUBDIRS", "RENDERED_SUBDIRS"),
        (f"PUBLIC_{noun.upper()}_NAMES", "PUBLIC_NAMES"),
        (f"public_{noun}_data_paths", "public_data_paths"),
        (f"public_{noun}_infos", "public_infos"),
        (f"public_{noun}_names", "public_names"),
    )
    for source, replacement in replacements:
        name = name.replace(source, replacement)
    return name


# ---------------------------------------------------------------------------
# Public surface: one contract, three pools
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pool", POOLS)
def test_package_reexports_the_same_five_names(pool: str) -> None:
    """Each package re-exports exactly the same five names, noun-substituted."""
    api = _api(pool)
    noun, name = api.noun, api.pool
    assert api.package.__all__ == [
        f"{noun.capitalize()}Info",
        f"build_{noun}_info",
        f"discover_{name}",
        f"resolve_{noun}_root",
        f"validate_{noun}_structure",
    ]
    for exported in api.package.__all__:
        assert hasattr(api.package, exported), exported


@pytest.mark.parametrize("pool", POOLS)
def test_submodule_all_lists_are_contract_identical(pool: str) -> None:
    """Every submodule ``__all__`` canonicalizes to the same list in all pools."""
    api = _api(pool)
    assert [_canonical(n, pool) for n in api.discovery.__all__] == [
        "NON_RENDERED_SUBDIRS",
        "RENDERED_SUBDIRS",
        "discover",
        "resolve_root",
    ]
    assert [_canonical(n, pool) for n in api.validation.__all__] == ["validate_structure"]
    assert [_canonical(n, pool) for n in api.info_module.__all__] == ["Info", "build_info"]
    scope_exports = [_canonical(n, pool) for n in api.scope.__all__]
    assert [n for n in scope_exports if n != "public_data_paths"] == [
        "PUBLIC_NAMES",
        "public_infos",
        "public_names",
    ]
    assert ("public_data_paths" in scope_exports) is (pool == "fonds")


@pytest.mark.parametrize("pool", POOLS)
def test_no_cross_pool_namespace_leaks(pool: str) -> None:
    """A pool package never exposes another pool's noun."""
    api = _api(pool)
    for other in POOLS:
        if other == pool:
            continue
        assert not hasattr(api.package, f"discover_{other}")
        assert not hasattr(api.package, f"validate_{NOUN[other]}_structure")


# ---------------------------------------------------------------------------
# Lifecycle constants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pool", POOLS)
def test_lifecycle_constants_are_identical(pool: str) -> None:
    api = _api(pool)
    assert api.non_rendered == frozenset({"working", "archive"})
    assert api.rendered == frozenset({"templates"})


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pool", POOLS)
def test_missing_pool_directory_returns_empty_and_warns(
    pool: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    api = _api(pool)
    with caplog.at_level("WARNING"):
        assert api.discover(tmp_path) == []
    assert any("directory not found" in record.message for record in caplog.records)


@pytest.mark.parametrize("pool", POOLS)
def test_discovery_qualified_names_and_nesting_depth(pool: str, tmp_path: Path) -> None:
    """Standalone, program, and one-level category names are all discovered alike."""
    api = _api(pool)
    _make_pool_dir(pool, tmp_path, "standalone")
    _make_pool_dir(pool, tmp_path, "templates/template_demo")
    _make_pool_dir(pool, tmp_path, "program_a/member")
    _make_pool_dir(pool, tmp_path, "program_b/_category/member")
    # A second category level is deliberately not discovered (nesting is one deep).
    _make_pool_dir(pool, tmp_path, "program_c/_category/_deep/member")
    # Invalid children contribute nothing and do not raise.
    (tmp_path / pool / "empty_child").mkdir(parents=True)
    (tmp_path / pool / "not_a_dir").write_text("x", encoding="utf-8")

    names = sorted(info.qualified_name for info in api.discover(tmp_path))
    assert names == [
        "program_a/member",
        "program_b/_category/member",
        "standalone",
        "templates/template_demo",
    ]


@pytest.mark.parametrize("pool", POOLS)
def test_discovery_skips_lifecycle_hidden_and_non_directories(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    _make_pool_dir(pool, tmp_path, "working/private_member")
    _make_pool_dir(pool, tmp_path, "archive/retired_member")
    _make_pool_dir(pool, tmp_path, ".hidden/member")
    (tmp_path / pool / "file.txt").write_text("not a directory", encoding="utf-8")
    _make_pool_dir(pool, tmp_path, "visible")

    names = [info.qualified_name for info in api.discover(tmp_path)]
    assert names == ["visible"]


@pytest.mark.parametrize("pool", POOLS)
def test_discovery_order_follows_sorted_directory_names(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    for name in ("c_third", "a_first", "b_second"):
        _make_pool_dir(pool, tmp_path, name)

    names = [info.qualified_name for info in api.discover(tmp_path)]
    assert names == ["a_first", "b_second", "c_third"]


@pytest.mark.parametrize("pool", POOLS)
def test_discovery_accepts_string_and_path_repo_root(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    _make_pool_dir(pool, tmp_path, "standalone")

    from_path = [info.qualified_name for info in api.discover(tmp_path)]
    from_str = [info.qualified_name for info in api.discover(str(tmp_path))]
    assert from_path == from_str == ["standalone"]


# ---------------------------------------------------------------------------
# resolve_<noun>_root
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pool", POOLS)
def test_resolve_qualified_head_resolves_directly(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    for head in sorted(api.non_rendered | api.rendered):
        member = _make_pool_dir(pool, tmp_path, f"{head}/member")
        assert api.resolve(tmp_path, f"{head}/member") == member.resolve()


@pytest.mark.parametrize("pool", POOLS)
def test_resolve_missing_qualified_name_returns_unresolved_pool_path(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    expected = tmp_path / pool / "templates/missing"
    assert api.resolve(tmp_path, "templates/missing") == expected
    assert not api.resolve(tmp_path, "templates/missing").exists()


@pytest.mark.parametrize("pool", POOLS)
def test_resolve_bare_name_prefers_templates_then_flat(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    templated = _make_pool_dir(pool, tmp_path, "templates/both")
    flat = _make_pool_dir(pool, tmp_path, "flat_only")
    _make_pool_dir(pool, tmp_path, "both")

    assert api.resolve(tmp_path, "both") == templated.resolve()
    assert api.resolve(tmp_path, "flat_only") == flat.resolve()
    assert api.resolve(tmp_path, "absent") == tmp_path / pool / "absent"


@pytest.mark.parametrize("pool", POOLS)
def test_resolve_accepts_string_repo_root(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    member = _make_pool_dir(pool, tmp_path, "templates/member")
    assert api.resolve(str(tmp_path), "templates/member") == member.resolve()


# ---------------------------------------------------------------------------
# validate_<noun>_structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pool", POOLS)
def test_validation_message_contract(pool: str, tmp_path: Path) -> None:
    """The five validation outcomes use one wording contract per pool."""
    api = _api(pool)
    noun, structure = api.noun, STRUCTURE[pool]

    missing = tmp_path / pool / "absent"
    assert api.validate(missing) == (False, f"{noun.capitalize()} directory does not exist: {missing}")

    not_a_dir = tmp_path / pool / "file.txt"
    not_a_dir.parent.mkdir(parents=True, exist_ok=True)
    not_a_dir.write_text("x", encoding="utf-8")
    assert api.validate(not_a_dir) == (False, f"Not a directory: {not_a_dir}")

    no_manifest = tmp_path / pool / "no_manifest"
    no_manifest.mkdir(parents=True)
    assert api.validate(no_manifest) == (False, f"Missing required file: {structure['manifest']}")

    wrong_layout = tmp_path / pool / "wrong_layout"
    wrong_layout.mkdir(parents=True)
    (wrong_layout / structure["manifest"]).write_text("type: demo\n", encoding="utf-8")
    assert api.validate(wrong_layout) == (False, structure["required_dir_message"])

    valid = tmp_path / pool / "valid"
    valid.mkdir(parents=True)
    (valid / structure["manifest"]).write_text("type: demo\n", encoding="utf-8")
    for required in structure["valid_dirs"][:1]:
        (valid / required).mkdir()
    assert api.validate(valid) == (True, f"Valid {noun} structure")


@pytest.mark.parametrize("pool", POOLS)
def test_validation_messages_share_one_shape(pool: str, tmp_path: Path) -> None:
    """Every failure starts from the shared prefixes a generic engine must keep."""
    api = _api(pool)
    missing = tmp_path / pool / "absent"
    _, message = api.validate(missing)
    assert "directory does not exist" in message
    assert message.endswith(str(missing))

    empty = tmp_path / pool / "empty"
    empty.mkdir(parents=True)
    _, message = api.validate(empty)
    assert message.startswith("Missing required file: ")

    manifest_only = tmp_path / pool / "manifest_only"
    manifest_only.mkdir(parents=True)
    (manifest_only / STRUCTURE[pool]["manifest"]).write_text("type: demo\n", encoding="utf-8")
    _, message = api.validate(manifest_only)
    assert message.startswith("Missing required directory: ")


@pytest.mark.parametrize("pool", POOLS)
def test_each_valid_dir_alone_satisfies_rules_and_tools(pool: str, tmp_path: Path) -> None:
    """``rules``/``tools`` accept either of their declared layouts; fonds accepts one."""
    api = _api(pool)
    structure = STRUCTURE[pool]
    for index, required in enumerate(structure["valid_dirs"]):
        target = tmp_path / pool / f"variant_{index}"
        target.mkdir(parents=True)
        (target / structure["manifest"]).write_text("type: demo\n", encoding="utf-8")
        (target / required).mkdir()
        assert api.validate(target)[0] is True
        assert api.build(target).is_valid is True


# ---------------------------------------------------------------------------
# <Noun>Info
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pool", POOLS)
def test_info_defaults_type_when_manifest_is_absent(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    target = tmp_path / pool / "unmanifested"
    target.mkdir(parents=True)

    info = api.build(target)
    type_field = f"{api.noun}_type"
    assert getattr(info, type_field) == STRUCTURE[pool]["type_default"]
    assert info.metadata == {}
    assert info.program == ""
    assert info.qualified_name == "unmanifested"
    assert info.path == target


@pytest.mark.parametrize("pool", POOLS)
def test_info_reads_type_and_presence_fields(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    target = _make_pool_dir(pool, tmp_path, "member")
    for _, directory in STRUCTURE[pool]["presence_dirs"]:
        (target / directory).mkdir(exist_ok=True)

    info = api.build(target)
    assert getattr(info, f"{api.noun}_type") == "demo"
    for field_name, _ in STRUCTURE[pool]["presence_dirs"]:
        assert getattr(info, field_name) is True
    assert info.is_valid is True
    assert info.metadata == {"type": "demo"}


@pytest.mark.parametrize("pool", POOLS)
def test_info_qualified_name_includes_program(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    target = _make_pool_dir(pool, tmp_path, "program/_category/member")
    info = api.build(target, program="program/_category")
    assert info.qualified_name == "program/_category/member"
    assert info.name == "member"


@pytest.mark.parametrize("pool", POOLS)
def test_info_marks_invalid_when_required_dir_is_missing(pool: str, tmp_path: Path) -> None:
    api = _api(pool)
    target = tmp_path / pool / "manifest_only"
    target.mkdir(parents=True)
    (target / STRUCTURE[pool]["manifest"]).write_text("type: demo\n", encoding="utf-8")
    assert api.build(target).is_valid is False


@pytest.mark.parametrize("pool", POOLS)
def test_info_degrades_silently_on_unreadable_manifest(pool: str, tmp_path: Path) -> None:
    """Malformed and non-mapping manifests yield empty metadata, never an exception."""
    api = _api(pool)
    type_field = f"{api.noun}_type"

    malformed = tmp_path / pool / "malformed"
    malformed.mkdir(parents=True)
    (malformed / STRUCTURE[pool]["manifest"]).write_text("type: [unclosed\n", encoding="utf-8")
    info = api.build(malformed)
    assert info.metadata == {}
    assert getattr(info, type_field) == STRUCTURE[pool]["type_default"]

    scalar = tmp_path / pool / "scalar"
    scalar.mkdir(parents=True)
    (scalar / STRUCTURE[pool]["manifest"]).write_text("just a string\n", encoding="utf-8")
    assert api.build(scalar).metadata == {}


@pytest.mark.parametrize("pool", POOLS)
def test_info_is_a_dataclass_with_the_shared_field_order(pool: str) -> None:
    api = _api(pool)
    field_names = [f.name for f in api.info_cls.__dataclass_fields__.values()]
    assert field_names == [
        "name",
        "path",
        f"{api.noun}_type",
        *[n for n, _ in STRUCTURE[pool]["presence_dirs"]],
        "metadata",
        "program",
    ]


# ---------------------------------------------------------------------------
# public_scope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pool", POOLS)
def test_public_roster_is_a_qualified_exemplar_tuple(pool: str) -> None:
    api = _api(pool)
    assert isinstance(api.roster, tuple)
    assert api.roster, "roster must not be empty"
    assert len(set(api.roster)) == len(api.roster)
    for name in api.roster:
        assert name.startswith("templates/"), name
        assert (REPO_ROOT / pool / name).is_dir(), name


@pytest.mark.parametrize("pool", POOLS)
def test_public_names_are_sorted_roster_members_present_in_this_checkout(pool: str) -> None:
    api = _api(pool)
    names = api.public_names(REPO_ROOT)
    assert names == sorted(api.roster)
    assert names == sorted(names)
    assert set(names) <= set(api.roster)


@pytest.mark.parametrize("pool", POOLS)
def test_public_infos_match_public_names(pool: str) -> None:
    api = _api(pool)
    infos = api.public_infos(REPO_ROOT)
    assert [info.qualified_name for info in infos] == api.public_names(REPO_ROOT)
    assert all(isinstance(info, api.info_cls) for info in infos)
    assert all(info.is_valid for info in infos)


def test_only_fonds_carries_the_lint_scope_helper() -> None:
    """The one deliberate asymmetry between the three scope modules."""
    assert hasattr(importlib.import_module("infrastructure.fonds.public_scope"), "public_fond_data_paths")
    assert not hasattr(importlib.import_module("infrastructure.rules.public_scope"), "public_rule_data_paths")
    assert not hasattr(importlib.import_module("infrastructure.tools.public_scope"), "public_tool_data_paths")
