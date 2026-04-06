"""Tests for SKILL.md discovery and manifest generation (no mocks)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from infrastructure.skills.cli import main as skills_cli_main
from infrastructure.skills.discovery import (
    DEFAULT_SKILL_SEARCH_ROOTS,
    build_manifest_payload,
    discover_skills,
    iter_skill_paths,
    load_skill_descriptor,
    manifest_matches_discovery,
    split_yaml_frontmatter,
    write_skill_manifest,
)


def _template_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


class TestSplitYamlFrontmatter:
    def test_valid_frontmatter(self) -> None:
        src = "---\nname: test-skill\ndescription: Hello\n---\n\n# Body\n"
        fm, body = split_yaml_frontmatter(src)
        assert fm == {"name": "test-skill", "description": "Hello"}
        assert "# Body" in body

    def test_no_frontmatter(self) -> None:
        src = "# Title only\n"
        fm, body = split_yaml_frontmatter(src)
        assert fm is None
        assert body == src

    def test_single_dash_line_only(self) -> None:
        src = "---\nnot closed"
        fm, body = split_yaml_frontmatter(src)
        assert fm is None


class TestIterSkillPaths:
    def test_skips_missing_search_root(self, tmp_path: Path) -> None:
        assert list(iter_skill_paths(tmp_path, ("does_not_exist",))) == []


class TestDiscoverInFixtureRepo:
    def test_finds_multiple_skills_sorted(self, tmp_path: Path) -> None:
        (tmp_path / "infrastructure" / "alpha").mkdir(parents=True)
        (tmp_path / "infrastructure" / "zeta").mkdir(parents=True)
        (tmp_path / "infrastructure" / "alpha" / "SKILL.md").write_text(
            "---\nname: a\ndescription: A\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "infrastructure" / "zeta" / "SKILL.md").write_text(
            "---\nname: z\ndescription: Z\n---\n",
            encoding="utf-8",
        )
        skills = discover_skills(tmp_path)
        assert [s.path_posix for s in skills] == [
            "infrastructure/alpha/SKILL.md",
            "infrastructure/zeta/SKILL.md",
        ]
        assert skills[0].name == "a"
        assert skills[1].cursor_at == "infrastructure/zeta/SKILL.md"

    def test_duplicate_name_raises(self, tmp_path: Path) -> None:
        (tmp_path / "infrastructure" / "p1").mkdir(parents=True)
        (tmp_path / "infrastructure" / "p2").mkdir(parents=True)
        content = "---\nname: dup\ndescription: x\n---\n"
        (tmp_path / "infrastructure" / "p1" / "SKILL.md").write_text(content, encoding="utf-8")
        (tmp_path / "infrastructure" / "p2" / "SKILL.md").write_text(content, encoding="utf-8")
        with pytest.raises(ValueError, match="Duplicate skill name"):
            discover_skills(tmp_path)

    def test_custom_roots(self, tmp_path: Path) -> None:
        (tmp_path / "docs" / "nested").mkdir(parents=True)
        (tmp_path / "docs" / "nested" / "SKILL.md").write_text(
            "---\nname: doc-skill\ndescription: d\n---\n",
            encoding="utf-8",
        )
        skills = discover_skills(tmp_path, search_roots=("docs",))
        assert len(skills) == 1
        assert skills[0].name == "doc-skill"


class TestManifestRoundTrip:
    def test_write_and_check(self, tmp_path: Path) -> None:
        (tmp_path / "infrastructure" / "m").mkdir(parents=True)
        (tmp_path / "infrastructure" / "m" / "SKILL.md").write_text(
            "---\nname: m1\ndescription: M\n---\n",
            encoding="utf-8",
        )
        out = tmp_path / "manifest.json"
        write_skill_manifest(tmp_path, output_path=out)
        ok, msg = manifest_matches_discovery(tmp_path, out)
        assert ok, msg
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["version"] == 1
        assert len(data["skills"]) == 1
        assert data["skills"][0]["name"] == "m1"


class TestTemplateRepository:
    def test_default_roots_includes_infrastructure_and_ccd_src(self) -> None:
        assert DEFAULT_SKILL_SEARCH_ROOTS == (
            "infrastructure",
            "projects/cognitive_case_diagrams/src",
        )

    def test_all_infrastructure_skills_parse(self) -> None:
        root = _template_repo_root()
        skills = discover_skills(root)
        assert len(skills) >= 24
        for s in skills:
            assert s.absolute_path.is_file()
            assert s.path_posix.endswith("SKILL.md")
            assert s.name is not None and s.name.strip()
            assert s.description is not None and s.description.strip()

    def test_manifest_matches_live_discovery(self) -> None:
        root = _template_repo_root()
        manifest = root / ".cursor" / "skill_manifest.json"
        ok, msg = manifest_matches_discovery(root, manifest)
        assert ok, msg

    def test_hub_skill_present(self) -> None:
        root = _template_repo_root()
        skills = discover_skills(root)
        paths = {s.path_posix for s in skills}
        assert "infrastructure/SKILL.md" in paths
        assert "infrastructure/skills/SKILL.md" in paths
        assert "projects/cognitive_case_diagrams/src/SKILL.md" in paths
        names = {s.name for s in skills if s.name}
        assert "ccd-src" in names


class TestCliModule:
    def test_list_json_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        root = _template_repo_root()
        assert skills_cli_main(["list-json", "--repo-root", str(root)]) == 0
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)
        assert any(row.get("name") == "infrastructure-skills" for row in data)

    def test_write_with_roots_after_subcommand(self, tmp_path: Path) -> None:
        """Flags after the verb (e.g. ``write --roots a b``) must parse."""
        (tmp_path / "infrastructure" / "a").mkdir(parents=True)
        (tmp_path / "docs" / "nested").mkdir(parents=True)
        (tmp_path / "infrastructure" / "a" / "SKILL.md").write_text(
            "---\nname: ia\ndescription: A\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "docs" / "nested" / "SKILL.md").write_text(
            "---\nname: doc-skill\ndescription: D\n---\n",
            encoding="utf-8",
        )
        out = tmp_path / "multi_root.json"
        assert (
            skills_cli_main(
                [
                    "write",
                    "--repo-root",
                    str(tmp_path),
                    "--roots",
                    "infrastructure",
                    "docs",
                    "--output",
                    str(out),
                ]
            )
            == 0
        )
        data = json.loads(out.read_text(encoding="utf-8"))
        paths = {row["path"] for row in data["skills"]}
        assert "infrastructure/a/SKILL.md" in paths
        assert "docs/nested/SKILL.md" in paths

    def test_write_subcommand(self, tmp_path: Path) -> None:
        (tmp_path / "infrastructure" / "pkg").mkdir(parents=True)
        (tmp_path / "infrastructure" / "pkg" / "SKILL.md").write_text(
            "---\nname: pkg-s\ndescription: P\n---\n",
            encoding="utf-8",
        )
        out = tmp_path / "custom_manifest.json"
        assert (
            skills_cli_main(
                ["write", "--repo-root", str(tmp_path), "--output", str(out)]
            )
            == 0
        )
        assert out.is_file()
        ok, msg = manifest_matches_discovery(tmp_path, out)
        assert ok, msg

    def test_check_fails_when_manifest_stale(self, tmp_path: Path) -> None:
        (tmp_path / "infrastructure" / "a").mkdir(parents=True)
        (tmp_path / "infrastructure" / "a" / "SKILL.md").write_text(
            "---\nname: n1\ndescription: d\n---\n",
            encoding="utf-8",
        )
        manifest = tmp_path / "m.json"
        manifest.write_text(
            json.dumps({"version": 1, "skills": []}),
            encoding="utf-8",
        )
        code = skills_cli_main(
            ["check", "--repo-root", str(tmp_path), "--manifest", str(manifest)]
        )
        assert code == 1

    def test_check_exit_zero(self) -> None:
        root = _template_repo_root()
        code = skills_cli_main(
            [
                "check",
                "--repo-root",
                str(root),
                "--manifest",
                ".cursor/skill_manifest.json",
            ]
        )
        assert code == 0

    def test_subprocess_module_invocation(self) -> None:
        root = _template_repo_root()
        proc = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "infrastructure.skills",
                "check",
                "--repo-root",
                str(root),
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


class TestLoadSkillDescriptor:
    def test_reads_real_file(self) -> None:
        root = _template_repo_root()
        path = root / "infrastructure" / "config" / "SKILL.md"
        d = load_skill_descriptor(path, root)
        assert d.name == "infrastructure-config"
        assert "Repository-scoped" in (d.description or "")


class TestBuildManifestPayload:
    def test_payload_keys(self) -> None:
        root = _template_repo_root()
        skills = discover_skills(root)
        payload = build_manifest_payload(skills)
        assert payload["version"] == 1
        for row in payload["skills"]:
            assert set(row.keys()) == {"name", "description", "path", "cursor_at"}
            assert row["path"] == row["cursor_at"]
