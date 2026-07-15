"""Tests for the agent-operation registry (no mocks; real synthetic trees)."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.skills.cli import main as skills_cli_main
from infrastructure.skills.operation_registry import (
    MUTATING_OPERATIONS,
    OperationDescriptor,
    build_operations_payload,
    discover_operations,
    load_operations_manifest,
    operations_manifest_matches_discovery,
    write_operations_manifest,
)


def _template_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _make_fake_cli_package(root: Path) -> None:
    """Create a real synthetic ``infrastructure/foo`` invocable package tree."""
    pkg = root / "infrastructure" / "foo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text('__all__ = ["alpha", "beta"]\n', encoding="utf-8")
    (pkg / "__main__.py").write_text(
        "from infrastructure.foo.cli import main\n\nif __name__ == '__main__':\n    raise SystemExit(main())\n",
        encoding="utf-8",
    )
    (pkg / "cli.py").write_text(
        '"""Foo CLI for doing foo things.\n\nMore prose here.\n"""\n'
        "import argparse\n\n\n"
        "def build_parser():\n"
        "    p = argparse.ArgumentParser()\n"
        "    sub = p.add_subparsers(dest='command')\n"
        "    sub.add_parser('run', help='Run foo')\n"
        "    sub.add_parser('check', help='Check foo')\n"
        "    return p\n",
        encoding="utf-8",
    )


class TestDiscoverOperations:
    def test_discovers_synthetic_package(self, tmp_path: Path) -> None:
        _make_fake_cli_package(tmp_path)
        ops = discover_operations(tmp_path)
        assert len(ops) == 1
        op = ops[0]
        assert isinstance(op, OperationDescriptor)
        assert op.module == "infrastructure.foo"
        assert op.invocation == "python -m infrastructure.foo"
        assert op.purpose == "Foo CLI for doing foo things."
        assert {s.name for s in op.subcommands} == {"run", "check"}
        assert dict((s.name, s.help) for s in op.subcommands)["run"] == "Run foo"
        assert op.exports == ("alpha", "beta")
        assert op.source_path == "infrastructure/foo/cli.py"

    def test_ignores_pycache(self, tmp_path: Path) -> None:
        _make_fake_cli_package(tmp_path)
        cache = tmp_path / "infrastructure" / "foo" / "__pycache__"
        cache.mkdir()
        (cache / "__main__.py").write_text("# compiled junk\n", encoding="utf-8")
        ops = discover_operations(tmp_path)
        assert len(ops) == 1

    def test_falls_back_to_main_when_no_cli(self, tmp_path: Path) -> None:
        pkg = tmp_path / "infrastructure" / "bar"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("\n", encoding="utf-8")
        (pkg / "__main__.py").write_text('"""Bar entry."""\n', encoding="utf-8")
        ops = discover_operations(tmp_path)
        assert len(ops) == 1
        assert ops[0].source_path == "infrastructure/bar/__main__.py"
        assert ops[0].purpose == "Bar entry."
        assert ops[0].exports == ()

    def test_discovers_single_file_module_with_main_guard(self, tmp_path: Path) -> None:
        # A single-file CLI in a directory that is NOT itself an invocable package.
        pkg = tmp_path / "infrastructure" / "reporting"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("\n", encoding="utf-8")
        (pkg / "release_readiness.py").write_text(
            '"""Release-readiness dashboard.\n\nMore prose.\n"""\n'
            '__all__ = ["build_dashboard"]\n\n\n'
            "def build_dashboard():\n    return {}\n\n\n"
            'if __name__ == "__main__":\n    raise SystemExit(0)\n',
            encoding="utf-8",
        )
        ops = discover_operations(tmp_path)
        assert len(ops) == 1
        op = ops[0]
        assert op.module == "infrastructure.reporting.release_readiness"
        assert op.invocation == "python -m infrastructure.reporting.release_readiness"
        assert op.source_path == "infrastructure/reporting/release_readiness.py"
        assert op.purpose == "Release-readiness dashboard."
        assert op.exports == ("build_dashboard",)
        assert op.effect == "read_only"

    def test_single_file_without_main_guard_is_ignored(self, tmp_path: Path) -> None:
        pkg = tmp_path / "infrastructure" / "helpers"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("\n", encoding="utf-8")
        (pkg / "plain_module.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
        assert discover_operations(tmp_path) == []

    def test_single_file_shadowed_by_package_entry_point_is_not_duplicated(self, tmp_path: Path) -> None:
        # ``cli.py`` in a package that already has ``__main__.py`` must not also be
        # emitted as its own single-file operation.
        _make_fake_cli_package(tmp_path)  # infrastructure/foo with __main__.py + cli.py
        # Give cli.py a main guard so it *would* match pass 2 if not filtered.
        cli = tmp_path / "infrastructure" / "foo" / "cli.py"
        cli.write_text(cli.read_text(encoding="utf-8") + '\n\nif __name__ == "__main__":\n    pass\n', encoding="utf-8")
        ops = discover_operations(tmp_path)
        assert [o.module for o in ops] == ["infrastructure.foo"]

    def test_mutating_effect_tier_from_allowlist(self, tmp_path: Path) -> None:
        mutating_leaf = sorted(MUTATING_OPERATIONS)[0].split(".")[-1]
        pkg = tmp_path / "infrastructure" / mutating_leaf
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("\n", encoding="utf-8")
        (pkg / "__main__.py").write_text("\n", encoding="utf-8")
        ops = discover_operations(tmp_path)
        assert len(ops) == 1
        assert ops[0].effect == "mutating"

    def test_results_sorted_by_module(self, tmp_path: Path) -> None:
        for name in ("zebra", "apple"):
            pkg = tmp_path / "infrastructure" / name
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").write_text("\n", encoding="utf-8")
            (pkg / "__main__.py").write_text("\n", encoding="utf-8")
        ops = discover_operations(tmp_path)
        assert [o.module for o in ops] == ["infrastructure.apple", "infrastructure.zebra"]


class TestManifest:
    def test_payload_shape(self, tmp_path: Path) -> None:
        _make_fake_cli_package(tmp_path)
        payload = build_operations_payload(discover_operations(tmp_path))
        assert payload["version"] == 1
        assert isinstance(payload["operations"], list)
        assert payload["operations"][0]["invocation"] == "python -m infrastructure.foo"

    def test_write_and_match(self, tmp_path: Path) -> None:
        _make_fake_cli_package(tmp_path)
        path = write_operations_manifest(tmp_path)
        assert path == (tmp_path / ".cursor" / "operations_manifest.json").resolve()
        on_disk = load_operations_manifest(path)
        assert on_disk["version"] == 1
        ok, msg = operations_manifest_matches_discovery(tmp_path, path)
        assert ok, msg

    def test_drift_detected_when_source_changes(self, tmp_path: Path) -> None:
        _make_fake_cli_package(tmp_path)
        path = write_operations_manifest(tmp_path)
        # Add a new invocable package -> manifest is now stale.
        new_pkg = tmp_path / "infrastructure" / "baz"
        new_pkg.mkdir(parents=True)
        (new_pkg / "__init__.py").write_text("\n", encoding="utf-8")
        (new_pkg / "__main__.py").write_text("\n", encoding="utf-8")
        ok, msg = operations_manifest_matches_discovery(tmp_path, path)
        assert not ok
        assert "out of date" in msg

    def test_missing_manifest_reported(self, tmp_path: Path) -> None:
        ok, msg = operations_manifest_matches_discovery(tmp_path, tmp_path / "nope.json")
        assert not ok
        assert "missing" in msg


class TestAgainstLiveRepo:
    def test_discovers_real_clis(self) -> None:
        ops = discover_operations(_template_repo_root())
        modules = {o.module for o in ops}
        assert "infrastructure.skills" in modules
        assert "infrastructure.core.pipeline" in modules
        # Every invocable op must carry a runnable invocation string.
        assert all(o.invocation.startswith("python -m infrastructure") for o in ops)

    def test_discovers_documented_single_file_clis(self) -> None:
        ops = discover_operations(_template_repo_root())
        modules = {o.module for o in ops}
        # The four documented single-file CLIs must be discoverable (R7).
        assert {
            "infrastructure.core.health",
            "infrastructure.project.public_scope",
            "infrastructure.documentation.generate_glossary_cli",
            "infrastructure.reporting.release_readiness",
        } <= modules

    def test_effect_tier_present_and_publish_is_mutating(self) -> None:
        ops = discover_operations(_template_repo_root())
        by_module = {o.module: o for o in ops}
        # Every descriptor carries a valid effect tier.
        assert all(o.effect in {"read_only", "mutating"} for o in ops)
        # The publish/upload CLI is tiered mutating; a plain read-only CLI is not.
        assert by_module["infrastructure.publishing"].effect == "mutating"
        assert by_module["infrastructure.skills"].effect == "mutating"
        assert by_module["infrastructure.core.health"].effect == "read_only"

    def test_cli_list_json_round_trips(self, capsys) -> None:
        rc = skills_cli_main(["operations-list-json", "--repo-root", str(_template_repo_root())])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["version"] == 1
        assert any(op["module"] == "infrastructure.skills" for op in payload["operations"])
