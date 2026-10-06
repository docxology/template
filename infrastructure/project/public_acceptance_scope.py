"""One source-owned path, identity and coverage contract for runtime cells."""

from __future__ import annotations

import ast
from collections.abc import Callable
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

if TYPE_CHECKING:
    from infrastructure.project.public_root_case_units import RootCaseUnit
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


class MissingRootCasePolicy(ValueError):
    """Root execution cannot begin without its reviewed offline case policy."""


_ROOT_POLICY = {"schema_version": 1, "selection": "complete-offline"}
_OPT_IN_MARKERS = frozenset(
    {
        "requires_ollama",
        "requires_docker",
        "network",
        "requires_network",
        "requires_credentials",
        "requires_zenodo",
        "requires_github",
        "requires_arxiv",
        "private_project",
        "external_fixture",
    }
)


@dataclass(frozen=True)
class RuntimeScope:
    """Resolve only the platform root or one canonical public exemplar."""

    root: Path
    name: str

    def __post_init__(self) -> None:
        if self.name != "root" and self.name not in PUBLIC_PROJECT_NAMES:
            raise ValueError("runtime scope must be root or a canonical public exemplar")
        object.__setattr__(self, "root", self.root.resolve(strict=True))
        if self.base.is_symlink() or self.base.resolve() != self.base:
            raise ValueError("runtime scope refuses symlink components")

    @property
    def base(self) -> Path:
        return self.root if self.name == "root" else self.root / "projects" / self.name

    @property
    def coverage_source(self) -> str:
        return "infrastructure" if self.name == "root" else "src"

    @property
    def coverage_floor(self) -> int:
        return 60 if self.name == "root" else 90

    def python_roots(self) -> tuple[Path, ...]:
        lanes = ("infrastructure", "scripts", "tests") if self.name == "root" else ("src", "scripts", "tests")
        return *(self.base / lane for lane in lanes), *sorted(self.base.glob("*.py"))

    def source_identity(self, *, path_admission: Callable[[Path], None] | None = None) -> str:
        from infrastructure.reporting.readiness_receipts import project_source_identity, source_fingerprint

        if path_admission is not None and self.name != "root":
            raise ValueError("source path admission is supported for complete Root reference scope only")
        return (
            source_fingerprint(self.root, path_admission=path_admission)
            if self.name == "root"
            else project_source_identity(self.root, self.name)
        )

    def deliverables_identity(self) -> str:
        from infrastructure.core.pipeline.fingerprints import canonical_digest
        from infrastructure.reporting.readiness_receipts import deliverable_identity

        if self.name == "root":
            return canonical_digest({name: deliverable_identity(self.root, name) for name in PUBLIC_PROJECT_NAMES})
        return deliverable_identity(self.root, self.name)

    def relative_tests(self, files: list[str] | tuple[str, ...]) -> list[str]:
        return [Path(path).relative_to(self.base.relative_to(self.root)).as_posix() for path in files]

    def test_files(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                path.relative_to(self.root).as_posix()
                for path in (self.base / "tests").rglob("*.py")
                if path.name.startswith("test_") or path.name.endswith("_test.py")
            )
        )

    def require_case_units(self, reader: SnapshotReader | None = None) -> tuple[RootCaseUnit, ...]:
        """Load v2 declarations without authorizing collection, execution or v1 exclusions."""
        if self.name != "root":
            raise ValueError("Root case units are unavailable for exemplar runtime scopes")
        from infrastructure.project.public_root_case_admission import load_policy
        from infrastructure.project.public_root_case_units import declared_units
        from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

        selected = reader or SnapshotReader(self.root)
        policy, _, _, prerequisites = load_policy(selected)
        return declared_units(policy, prerequisites)

    def require_case_policy(self, reader: SnapshotReader | None = None) -> dict[str, Any]:
        """The initial root policy permits complete offline suites, never exclusions.

        The current platform does not declare this policy: its live/private case
        classification needs a separate reviewed contract. Missing policy blocks
        before collection. Small owned offline repositories can exercise the
        genuine root producer/reader without waiving production obligations.
        """
        if self.name != "root":
            return {}
        from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

        reader = reader or SnapshotReader(self.root)
        metadata = tomllib.loads(reader.read("pyproject.toml").content.decode())
        policy = metadata.get("tool", {}).get("template", {}).get("root_acceptance")
        if not isinstance(policy, dict) or policy != _ROOT_POLICY or type(policy.get("schema_version")) is not int:
            raise MissingRootCasePolicy("ROOT-ACCEPTANCE-CASE-POLICY-1: reviewed root offline case policy is missing")
        # This initial policy cannot reclassify known opt-in cases as core.
        policy_sources = sorted((self.base / "tests").rglob("*.py")) + sorted(self.base.glob("*.py"))
        for path in policy_sources:
            tree = ast.parse(reader.read(path.relative_to(self.root).as_posix()).content, filename=str(path))
            if any(isinstance(node, ast.Attribute) and node.attr in _OPT_IN_MARKERS for node in ast.walk(tree)):
                raise MissingRootCasePolicy(
                    "ROOT-ACCEPTANCE-CASE-POLICY-1: root contains opt-in cases needing classification"
                )
        if not reader.unchanged():
            raise ValueError("root case policy/source changed while admitted")
        return dict(policy)
