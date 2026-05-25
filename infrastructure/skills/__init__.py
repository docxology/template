"""Agent skill discovery: enumerate and parse ``SKILL.md`` descriptors.

Use :func:`discover_skills` from repository root to list all skills, or
``python -m infrastructure.skills write`` to refresh ``.cursor/skill_manifest.json``.
"""

from infrastructure.skills.contracts import (
    check_skill_contracts,
    iter_contract_skill_paths,
    validate_skill_contract_file,
)
from infrastructure.skills.discovery import (
    DEFAULT_SKILL_SEARCH_ROOTS,
    SkillDescriptor,
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

__all__ = [
    "DEFAULT_SKILL_SEARCH_ROOTS",
    "SkillDescriptor",
    "build_skill_index_markdown",
    "build_manifest_payload",
    "check_skill_contracts",
    "discover_skills",
    "iter_skill_paths",
    "iter_contract_skill_paths",
    "load_manifest",
    "load_skill_descriptor",
    "manifest_matches_discovery",
    "manifest_skill_dicts_for_prompt",
    "skill_descriptors_as_json_serializable",
    "split_yaml_frontmatter",
    "validate_skill_contract_file",
    "write_skill_manifest",
]
