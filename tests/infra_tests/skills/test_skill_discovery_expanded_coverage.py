"""Tests for infrastructure.skills.discovery — expanded coverage of edge cases."""

import json
from pathlib import Path

import pytest

from infrastructure.skills.discovery import (
    split_yaml_frontmatter,
    load_skill_descriptor,
    _ensure_unique_names,
    SkillDescriptor,
    build_manifest_payload,
    write_skill_manifest,
    load_manifest,
    manifest_matches_discovery,
    manifest_skill_dicts_for_prompt,
    skill_descriptors_as_json_serializable,
)


class TestSplitYamlFrontmatter:
    def test_no_frontmatter(self):
        fm, body = split_yaml_frontmatter("Just body text")
        assert fm is None
        assert body == "Just body text"

    def test_incomplete_frontmatter(self):
        """Only one --- delimiter."""
        fm, body = split_yaml_frontmatter("---\nname: test\nbody text")
        assert fm is None

    def test_empty_yaml_block(self):
        fm, body = split_yaml_frontmatter("---\n---\nbody")
        assert fm is None
        assert "body" in body

    def test_yaml_parses_to_none(self):
        """YAML that loads as None (e.g., just whitespace/comments)."""
        fm, body = split_yaml_frontmatter("---\n# just a comment\n---\nbody")
        assert fm == {}
        assert "body" in body

    def test_yaml_parses_to_non_dict(self):
        """YAML that loads as a list instead of dict."""
        fm, body = split_yaml_frontmatter("---\n- item1\n- item2\n---\nbody")
        assert fm is None
        assert "body" in body

    def test_valid_frontmatter(self):
        fm, body = split_yaml_frontmatter("---\nname: skill\ndescription: A skill\n---\nbody text")
        assert fm == {"name": "skill", "description": "A skill"}
        assert "body text" in body


class TestLoadSkillDescriptor:
    def test_basic(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: TestSkill\ndescription: Test\n---\n# Body\n")
        desc = load_skill_descriptor(skill_file, tmp_path)
        assert desc.name == "TestSkill"
        assert desc.description == "Test"
        assert desc.path_posix == "SKILL.md"

    def test_no_frontmatter(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Just a skill\nNo frontmatter here.")
        desc = load_skill_descriptor(skill_file, tmp_path)
        assert desc.name is None
        assert desc.description is None

    def test_name_is_number(self, tmp_path):
        """name field is int, gets cast to str."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: 42\ndescription: 99\n---\nbody")
        desc = load_skill_descriptor(skill_file, tmp_path)
        assert desc.name == "42"
        assert desc.description == "99"


class TestEnsureUniqueNames:
    def test_unique(self):
        skills = [
            SkillDescriptor(Path("/a"), Path("a/SKILL.md"), "alpha", "desc"),
            SkillDescriptor(Path("/b"), Path("b/SKILL.md"), "beta", "desc"),
        ]
        _ensure_unique_names(skills)  # Should not raise

    def test_duplicate_raises(self):
        skills = [
            SkillDescriptor(Path("/a"), Path("a/SKILL.md"), "same", "desc"),
            SkillDescriptor(Path("/b"), Path("b/SKILL.md"), "same", "desc"),
        ]
        with pytest.raises(ValueError, match="Duplicate"):
            _ensure_unique_names(skills)

    def test_none_name_skipped(self):
        skills = [
            SkillDescriptor(Path("/a"), Path("a/SKILL.md"), None, "desc"),
            SkillDescriptor(Path("/b"), Path("b/SKILL.md"), None, "desc"),
        ]
        _ensure_unique_names(skills)  # None names are not checked


class TestBuildManifestPayload:
    def test_basic(self):
        skills = [
            SkillDescriptor(Path("/a"), Path("infrastructure/SKILL.md"), "MySkill", "A skill"),
        ]
        payload = build_manifest_payload(skills)
        assert "version" in payload
        assert len(payload["skills"]) == 1
        assert payload["skills"][0]["name"] == "MySkill"


class TestWriteSkillManifest:
    def test_default_output(self, tmp_path):
        # Create a SKILL.md to discover
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "infrastructure" / "SKILL.md").write_text(
            "---\nname: InfraSkill\ndescription: Infra\n---\nbody"
        )
        path = write_skill_manifest(tmp_path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["version"] == 1

    def test_custom_output(self, tmp_path):
        path = write_skill_manifest(tmp_path, output_path=tmp_path / "manifest.json")
        assert path.exists()

    def test_relative_output(self, tmp_path):
        path = write_skill_manifest(tmp_path, output_path="custom/manifest.json")
        assert path.exists()


class TestLoadManifest:
    def test_valid(self, tmp_path):
        f = tmp_path / "manifest.json"
        f.write_text(json.dumps({"version": 1, "skills": []}))
        data = load_manifest(f)
        assert data["version"] == 1

    def test_not_dict_raises(self, tmp_path):
        f = tmp_path / "manifest.json"
        f.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(ValueError, match="object"):
            load_manifest(f)


class TestManifestMatchesDiscovery:
    def test_matches(self, tmp_path):
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "infrastructure" / "SKILL.md").write_text(
            "---\nname: Skill\ndescription: D\n---\nbody"
        )
        path = write_skill_manifest(tmp_path)
        ok, msg = manifest_matches_discovery(tmp_path, path)
        assert ok is True
        assert msg == "ok"

    def test_missing_manifest(self, tmp_path):
        ok, msg = manifest_matches_discovery(tmp_path, tmp_path / "nonexistent.json")
        assert ok is False
        assert "missing" in msg

    def test_corrupt_manifest(self, tmp_path):
        f = tmp_path / "manifest.json"
        f.write_text("not json")
        ok, msg = manifest_matches_discovery(tmp_path, f)
        assert ok is False
        assert "unreadable" in msg

    def test_version_mismatch(self, tmp_path):
        f = tmp_path / "manifest.json"
        f.write_text(json.dumps({"version": 999, "skills": []}))
        ok, msg = manifest_matches_discovery(tmp_path, f)
        assert ok is False
        assert "version" in msg

    def test_skills_mismatch(self, tmp_path):
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "infrastructure" / "SKILL.md").write_text(
            "---\nname: Skill\ndescription: D\n---\nbody"
        )
        f = tmp_path / "manifest.json"
        f.write_text(json.dumps({"version": 1, "skills": []}))
        ok, msg = manifest_matches_discovery(tmp_path, f)
        assert ok is False
        assert "out of date" in msg


class TestManifestSkillDictsForPrompt:
    def test_basic(self):
        skills = [
            SkillDescriptor(Path("/a"), Path("a/SKILL.md"), "S1", "Description one"),
        ]
        result = manifest_skill_dicts_for_prompt(skills)
        assert len(result) == 1
        assert result[0]["name"] == "S1"

    def test_none_name(self):
        skills = [
            SkillDescriptor(Path("/a"), Path("a/SKILL.md"), None, None),
        ]
        result = manifest_skill_dicts_for_prompt(skills)
        assert result[0]["name"] == ""
        assert result[0]["description"] == ""


class TestSkillDescriptorsAsJsonSerializable:
    def test_basic(self):
        skills = [
            SkillDescriptor(
                Path("/a"), Path("infrastructure/SKILL.md"), "S1", "D1",
                frontmatter={"name": "S1"}
            ),
        ]
        result = skill_descriptors_as_json_serializable(skills)
        assert len(result) == 1
        assert result[0]["name"] == "S1"
        assert result[0]["frontmatter"] == {"name": "S1"}
