"""Tests for SKILL.md discovery and manifest generation (no mocks)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from infrastructure.skills.cli import main as skills_cli_main
from infrastructure.skills.discovery import (
    DEFAULT_SKILL_SEARCH_ROOTS,
    SkillDescriptor,
    _ensure_unique_names,
    build_skill_index_markdown,
    build_manifest_payload,
    discover_skills,
    iter_skill_paths,
    load_manifest,
    load_skill_descriptor,
    manifest_matches_discovery,
    manifest_skill_dicts_for_prompt,
    skill_descriptors_as_json_serializable,
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

    def test_build_skill_index_markdown(self, tmp_path: Path) -> None:
        (tmp_path / "infrastructure" / "m").mkdir(parents=True)
        (tmp_path / "infrastructure" / "m" / "SKILL.md").write_text(
            "---\nname: m1\ndescription: M\n---\n",
            encoding="utf-8",
        )
        skills = discover_skills(tmp_path)
        index = build_skill_index_markdown(skills)

        assert "# Skill Index" in index
        assert "`m1`" in index
        assert "project ships a `SKILL.md`" in index
        for root in DEFAULT_SKILL_SEARCH_ROOTS:
            assert f"`{root}/`" in index


class TestTemplateRepository:
    def test_default_roots_scope_projects_to_public_templates(self) -> None:
        # Must scan projects/templates/ (the tracked public exemplars) and NOT
        # bare "projects", which would recurse into untracked local-only sibling
        # projects and leak their SKILL.md names into the tracked manifest/index.
        assert DEFAULT_SKILL_SEARCH_ROOTS == (
            "infrastructure",
            "scripts",
            "projects/templates",
            "fonds/templates",
            "rules/templates",
            "tools/templates",
            "docs/prompts",
            ".cursor/skills",
        )
        assert "projects" not in DEFAULT_SKILL_SEARCH_ROOTS
        assert "fonds" not in DEFAULT_SKILL_SEARCH_ROOTS
        assert "rules" not in DEFAULT_SKILL_SEARCH_ROOTS
        assert "tools" not in DEFAULT_SKILL_SEARCH_ROOTS

    def test_template_workflow_skills_present(self) -> None:
        root = _template_repo_root()
        skills = discover_skills(root)
        names = {s.name for s in skills}
        assert "template-workflows" in names
        assert "template-deep-research" in names
        assert "template-academic-paper" in names
        assert "template-academic-paper-reviewer" in names
        assert "template-academic-pipeline" in names
        assert "template-pipeline-debugging" in names
        assert "template-comprehensive-assessment" in names
        template_names = [n for n in names if n and n.startswith("template-")]
        assert len(template_names) >= 45
        assert len(template_names) == len(set(template_names))

    def test_public_template_agent_skills_present(self) -> None:
        root = _template_repo_root()
        skills = discover_skills(root)
        paths = {s.path_posix for s in skills}
        assert "projects/templates/template_code_project/.agents/skills/template-code-project/SKILL.md" in paths
        assert (
            "projects/templates/template_pools_rules_tools/.agents/skills/template-pools-rules-tools/SKILL.md" in paths
        )

    def test_script_skills_present(self) -> None:
        root = _template_repo_root()
        skills = discover_skills(root)
        paths = {s.path_posix for s in skills}
        assert "scripts/pipeline/SKILL.md" in paths
        assert "scripts/runner/SKILL.md" in paths

    def test_private_working_agent_skills_stay_excluded(self, tmp_path: Path) -> None:
        skill = tmp_path / "projects/working/private/.agents/skills/private/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(
            "---\nname: private-skill\ndescription: should not leak\n---\n",
            encoding="utf-8",
        )
        skills = discover_skills(tmp_path, search_roots=("projects",))
        assert [s.path_posix for s in skills] == []

    def test_prompt_mode_registry_present(self) -> None:
        root = _template_repo_root()
        registry = root / "docs" / "prompts" / "MODE_REGISTRY.md"
        assert registry.is_file()
        text = registry.read_text(encoding="utf-8")
        assert "template-deep-research" in text
        assert "template-academic-pipeline" in text
        assert "data_access_level" in text

    def test_prompts_hub_skill_path(self) -> None:
        root = _template_repo_root()
        skills = discover_skills(root)
        paths = {s.path_posix for s in skills}
        assert "docs/prompts/SKILL.md" in paths
        assert "docs/prompts/pipeline-debugging/SKILL.md" in paths

    def test_all_infrastructure_skills_parse(self) -> None:
        root = _template_repo_root()
        skills = discover_skills(root)
        assert len(skills) >= 15
        for s in skills:
            assert s.absolute_path.is_file()
            assert s.path_posix.endswith("SKILL.md")
            assert s.name is not None and s.name.strip()
            assert s.description is not None and s.description.strip()

    def test_top_level_infrastructure_packages_have_skill_descriptors(self) -> None:
        root = _template_repo_root()
        missing = [
            path.name
            for path in sorted((root / "infrastructure").iterdir())
            if path.is_dir() and (path / "__init__.py").is_file() and not (path / "SKILL.md").is_file()
        ]
        assert missing == []

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

    def test_gauss_skill_present(self) -> None:
        root = _template_repo_root()
        skills = discover_skills(root)
        paths = {s.path_posix for s in skills}
        assert ".cursor/skills/gauss/SKILL.md" in paths


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
        assert skills_cli_main(["write", "--repo-root", str(tmp_path), "--output", str(out)]) == 0
        assert out.is_file()
        ok, msg = manifest_matches_discovery(tmp_path, out)
        assert ok, msg

    def test_write_index_subcommand(self, tmp_path: Path) -> None:
        (tmp_path / "infrastructure" / "pkg").mkdir(parents=True)
        (tmp_path / "infrastructure" / "pkg" / "SKILL.md").write_text(
            "---\nname: pkg-s\ndescription: P\n---\n",
            encoding="utf-8",
        )
        out = tmp_path / "skills.md"

        assert skills_cli_main(["write-index", "--repo-root", str(tmp_path), "--output", str(out)]) == 0

        text = out.read_text(encoding="utf-8")
        assert "| `pkg-s` | `infrastructure/pkg/SKILL.md` | P |" in text

    def test_check_contracts_subcommand(self, tmp_path: Path) -> None:
        skill = tmp_path / "docs/prompts/academic-paper/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(
            "---\n"
            "name: template-academic-paper\n"
            "description: Template-native paper workflow.\n"
            "metadata:\n"
            '  version: "1.0.0"\n'
            '  last_updated: "2026-05-25"\n'
            "  status: active\n"
            "  data_access_level: redacted\n"
            "  task_type: open-ended\n"
            "  modes: [plan, full]\n"
            "  related_skills: [template-manuscript-creation]\n"
            "---\n"
            "# Skill\n",
            encoding="utf-8",
        )

        assert skills_cli_main(["check-contracts", "--repo-root", str(tmp_path)]) == 0

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
        ok, msg = manifest_matches_discovery(tmp_path, manifest)
        assert ok is False
        assert "out of date" in msg.lower()
        code = skills_cli_main(["check", "--repo-root", str(tmp_path), "--manifest", str(manifest)])
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
            assert {"name", "description", "path", "cursor_at"}.issubset(row)
            assert row["path"] == row["cursor_at"]

    def test_basic_payload_from_fixture(self, tmp_path: Path) -> None:
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "infrastructure" / "SKILL.md").write_text(
            "---\n"
            "name: MySkill\n"
            "description: A skill\n"
            "metadata:\n"
            '  version: "1.0.0"\n'
            "  data_access_level: raw\n"
            "---\n"
            "body",
            encoding="utf-8",
        )
        skills = discover_skills(tmp_path)
        payload = build_manifest_payload(skills)
        assert payload["skills"][0]["name"] == "MySkill"
        assert payload["skills"][0]["metadata"] == {
            "version": "1.0.0",
            "data_access_level": "raw",
        }


class TestEnsureUniqueNames:
    def test_duplicate_raises(self) -> None:
        skills = [
            SkillDescriptor(Path("/a"), Path("a/SKILL.md"), "same", "desc"),
            SkillDescriptor(Path("/b"), Path("b/SKILL.md"), "same", "desc"),
        ]
        with pytest.raises(ValueError, match="Duplicate"):
            _ensure_unique_names(skills)


class TestLoadManifest:
    def test_not_dict_raises(self, tmp_path: Path) -> None:
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with pytest.raises(ValueError, match="object"):
            load_manifest(manifest)


class TestManifestSkillDictsForPrompt:
    def test_none_name_becomes_empty_string(self) -> None:
        skills = [SkillDescriptor(Path("/a"), Path("a/SKILL.md"), None, None)]
        result = manifest_skill_dicts_for_prompt(skills)
        assert result[0]["name"] == ""
        assert result[0]["description"] == ""


class TestSkillDescriptorsAsJsonSerializable:
    def test_includes_frontmatter(self) -> None:
        skills = [
            SkillDescriptor(
                Path("/a"),
                Path("infrastructure/SKILL.md"),
                "S1",
                "D1",
                frontmatter={"name": "S1"},
            ),
        ]
        result = skill_descriptors_as_json_serializable(skills)
        assert result[0]["frontmatter"] == {"name": "S1"}
