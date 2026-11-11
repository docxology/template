"""Changed-path scope policy shared by functional CI planning and validation."""

from pathlib import Path


_DOCUMENTATION_SUFFIXES = frozenset({".md", ".rst", ".svg", ".png", ".jpg", ".jpeg", ".gif"})
_GUIDE_NAMES = frozenset({"AGENTS.md", "README.md", "DESIGN.md"})
_ROOT_GUIDES = _GUIDE_NAMES | frozenset(
    {
        "CHANGELOG.md",
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "MAINTAINERS.md",
        "SECURITY.md",
        "START_HERE.md",
        "STATUS.md",
        "TO-DO.md",
    }
)


def documentation_only(paths: tuple[str, ...]) -> bool:
    """Recognize guide-only changes without excluding runtime text or artwork."""

    def is_guide(name: str) -> bool:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or path.as_posix() != name:
            return False
        if len(path.parts) == 1:
            return name in _ROOT_GUIDES
        if path.parts[0] == "docs":
            # These trees contain manuscript inputs and executable prompt assets.
            return path.parts[1] not in {"manuscript", "prompts"} and path.suffix.lower() in _DOCUMENTATION_SUFFIXES
        return (
            path.parts[0] in {"infrastructure", "scripts", "tests", ".github", "projects"} and path.name in _GUIDE_NAMES
        )

    return bool(paths) and all(is_guide(name) for name in paths)
