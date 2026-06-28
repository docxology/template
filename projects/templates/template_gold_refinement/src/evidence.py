"""Evidence registry for the gold-refinement exemplar.

Cross-checks every contribution claim against its evidence source and
builds a machine-readable evidence registry. This is the "assaying" stage
operationalized: each claim is tested against evidence before the
manuscript is allowed to render.
"""

from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
import re

import yaml

try:
    from .config import GoldRefinementConfig
except ImportError:
    from config import GoldRefinementConfig  # type: ignore[no-redef]

import logging

logger = logging.getLogger(__name__)


def _resolve_project_file(project_root: Path, file_part: str) -> tuple[Path | None, str]:
    root = project_root.resolve()
    candidate = (project_root / file_part).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, f"Path escapes project root: {file_part}"
    if not candidate.exists():
        return None, f"File not found: {file_part}"
    return candidate, ""


def _python_target_matches(node: ast.AST, symbol_name: str) -> bool:
    if isinstance(node, ast.Name):
        return node.id == symbol_name
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(_python_target_matches(child, symbol_name) for child in node.elts)
    return False


def _python_symbol_exists(file_path: Path, symbol_name: str) -> bool:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol_name:
            return True
        if isinstance(node, ast.Assign) and any(_python_target_matches(target, symbol_name) for target in node.targets):
            return True
        if isinstance(node, ast.AnnAssign) and _python_target_matches(node.target, symbol_name):
            return True
    return False


def _yaml_path_exists(file_path: Path, symbol_path: str) -> bool:
    data = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    current: object = data
    for segment in (part.strip() for part in symbol_path.split(".")):
        if not segment:
            continue
        if isinstance(current, dict) and segment in current:
            current = current[segment]
            continue
        return False
    return True


def _symbol_exists(file_path: Path, symbol_part: str) -> bool:
    if not symbol_part:
        return True
    if file_path.suffix in {".yaml", ".yml"}:
        return _yaml_path_exists(file_path, symbol_part)
    symbol_name = symbol_part.split("(", 1)[0].split(".", 1)[0].split("[", 1)[0]
    if not symbol_name:
        return True
    if file_path.suffix == ".py":
        return _python_symbol_exists(file_path, symbol_name)
    content = file_path.read_text(encoding="utf-8")
    return re.search(rf"(?<!\\w){re.escape(symbol_name)}(?!\\w)", content) is not None


@dataclass(frozen=True)
class EvidenceEntry:
    """One evidence entry: a claim and its supporting evidence."""

    claim_name: str
    claim_statement: str
    evidence_source: str
    boundary: str
    supported: bool
    notes: str = ""

    def as_dict(self) -> dict[str, str | bool]:
        return asdict(self)


@dataclass
class EvidenceRegistry:
    """Full evidence registry across all claims."""

    entries: list[EvidenceEntry] = field(default_factory=list)
    total_claims: int = 0
    supported_claims: int = 0
    unsupported_claims: int = 0

    @property
    def support_rate(self) -> float:
        if self.total_claims == 0:
            return 0.0
        return self.supported_claims / self.total_claims

    @property
    def is_passing(self) -> bool:
        return self.unsupported_claims == 0 and self.total_claims > 0

    def to_dict(self) -> dict[str, object]:
        return {
            "total_claims": self.total_claims,
            "supported_claims": self.supported_claims,
            "unsupported_claims": self.unsupported_claims,
            "support_rate": self.support_rate,
            "is_passing": self.is_passing,
            "entries": [e.as_dict() for e in self.entries],
        }


def _check_evidence_source(source: str, project_root: Path) -> tuple[bool, str]:
    """Check if an evidence source exists.

    Sources are strings like ``src/refinery.py::CANONICAL_STAGES`` or
    ``manuscript/config.yaml#gold_refinement.seed``.
    """
    # Split on :: or #
    if "::" in source:
        file_part = source.split("::")[0]
        symbol_part = source.split("::", 1)[1] if "::" in source else ""
    elif "#" in source:
        file_part = source.split("#")[0]
        symbol_part = source.split("#", 1)[1] if "#" in source else ""
    else:
        file_part = source
        symbol_part = ""

    file_path, error = _resolve_project_file(project_root, file_part)
    if error:
        return False, error
    if file_path is None:
        return False, f"File not found: {file_part}"

    if symbol_part and not _symbol_exists(file_path, symbol_part):
        return False, f"Symbol '{symbol_part}' not found in {file_part}"

    return True, ""


def build_evidence_registry(
    config: GoldRefinementConfig,
    project_root: Path,
) -> EvidenceRegistry:
    """Build the evidence registry from config contribution_claims.

    Cross-checks each claim's evidence source against the actual files
    and symbols in the project.
    """
    entries: list[EvidenceEntry] = []

    for claim in config.contribution_claims:
        name = claim.get("name", "")
        statement = claim.get("claim", "")
        evidence = claim.get("evidence", "")
        boundary = claim.get("boundary", "local")

        supported, notes = _check_evidence_source(evidence, project_root)
        entries.append(
            EvidenceEntry(
                claim_name=name,
                claim_statement=statement,
                evidence_source=evidence,
                boundary=boundary,
                supported=supported,
                notes=notes,
            )
        )

    total = len(entries)
    supported_count = sum(1 for e in entries if e.supported)
    unsupported_count = total - supported_count

    return EvidenceRegistry(
        entries=entries,
        total_claims=total,
        supported_claims=supported_count,
        unsupported_claims=unsupported_count,
    )


def write_evidence_registry(
    registry: EvidenceRegistry,
    output_path: Path,
) -> Path:
    """Write the evidence registry as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(registry.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Wrote evidence registry to %s", output_path)
    return output_path


def check_claim_ledger_alignment(
    config: GoldRefinementConfig,
    ledger_path: Path,
) -> list[str]:
    mismatches: list[str] = []

    if not ledger_path.exists():
        mismatches.append(f"Claim ledger not found: {ledger_path}")
        return mismatches

    with ledger_path.open("r") as f:
        ledger = yaml.safe_load(f) or {}

    ledger_sources = {
        str(entry.get("source", "")).strip()
        for entry in ledger.get("claims", [])
        if isinstance(entry, dict) and str(entry.get("source", "")).strip()
    }

    for claim in config.contribution_claims:
        name = claim.get("name", "")
        evidence = str(claim.get("evidence", "")).strip()
        if not evidence:
            mismatches.append(f"Config claim '{name}' is missing an evidence source")
            continue
        if evidence not in ledger_sources:
            mismatches.append(
                f"Config claim '{name}' evidence source '{evidence}' has no matching claim_ledger.yaml entry"
            )

    return mismatches


__all__ = [
    "EvidenceEntry",
    "EvidenceRegistry",
    "build_evidence_registry",
    "check_claim_ledger_alignment",
    "write_evidence_registry",
]
