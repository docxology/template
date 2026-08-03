"""Deterministic, project-local validation of regenerated Madlib outputs.

The shared Stage 04 validator checks rendered PDFs, figure registries, evidence
registries, and design overlays, but it does not bind the project-owned Stage 02
artifacts back to the config and source that generated them. This module is that
project-local counterpart: it reads the on-disk artifacts and fails closed when
token provenance, figure-registry coverage, configured-field origins, the
authoring-contract surface, or the declared artifact inventory drift from
source.

The validator is read-only with respect to generation. It never rewrites
generation artifacts; the only file it writes is its own report,
``output/reports/output_validation.json``.

Determinism: the report contains no timestamps or environment-dependent
fields, so a clean regeneration produces an identical report byte-for-byte.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import SECTION_KEYS, MadlibConfig, MadlibConfigError, load_madlib_config

OUTPUT_VALIDATION_SCHEMA_VERSION = 1
REPORT_FILENAME = "output_validation.json"
FIGURE_REGISTRY_FILENAME = "figure_registry.json"

# Stage 02 project-owned artifact inventory. This is the single source of truth
# for the stale-artifact guard: the shared renderer and validation stages may
# add infra-owned files to the same directories, but the project-owned set is
# enforced strictly so a new Stage 02 artifact name cannot ship undeclared.
PROJECT_OWNED_DATA_FILES: frozenset[str] = frozenset(
    {
        "configured_field_inventory.json",
        "manuscript_variables.json",
        "section_plan.json",
        "token_inventory.json",
    }
)
INFRA_OWNED_DATA_FILES: frozenset[str] = frozenset({"publication_ledger.json"})
PROJECT_OWNED_REPORT_FILES: frozenset[str] = frozenset(
    {
        "configured_field_summary.md",
        "injection_trace.json",
        "madlib_summary.md",
    }
)
# The validator's own report (REPORT_FILENAME) is intentionally absent from
# PROJECT_OWNED_REPORT_FILES: requiring it to pre-exist would make the
# validator's first run fail on itself. The report is written by
# ``write_validation_report`` and committed as regenerated evidence; the
# stale-artifact guard covers the three generation reports above.
# Cover + density + seven conditional figures, plus the registry itself.
DECLARED_FIGURE_FILES: frozenset[str] = frozenset(
    {
        "configured_field_matrix.png",
        "field_origin_summary.png",
        "madlib_cover_overview.png",
        "provenance_trace_map.png",
        "quality_gate_matrix.png",
        "section_configuration_heatmap.png",
        "section_token_allocation.png",
        "token_density.png",
        "token_injection_flow.png",
        FIGURE_REGISTRY_FILENAME,
    }
)
TOKEN_ROW_REQUIRED_KEYS: tuple[str, ...] = (
    "variable_name",
    "slot_name",
    "category",
    "value",
    "section",
    "ordinal",
    "source_key",
)
TOKEN_SOURCE_KEY_PREFIX = "manuscript/config.yaml#madlib.lexicon."
PLACEHOLDER_PATTERN = re.compile(r"\{\{[A-Z0-9_]+\}\}")
FIGURE_REF_PATTERN = re.compile(r"\]\((\.\./output/figures/([^)#]+))\)")


@dataclass(frozen=True)
class ValidationIssue:
    """A single deterministic validation finding."""

    code: str
    message: str


@dataclass
class OutputValidationResult:
    """Aggregate validation outcome plus measured artifact facts."""

    issues: list[ValidationIssue] = field(default_factory=list)
    measured: dict[str, object] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """True when no issue was found."""
        return not self.issues

    def to_dict(self) -> dict[str, object]:
        """Serialize the result for the deterministic JSON report."""
        return {
            "schema_version": OUTPUT_VALIDATION_SCHEMA_VERSION,
            "passed": self.passed,
            "issue_count": len(self.issues),
            "issues": [{"code": issue.code, "message": issue.message} for issue in self.issues],
            "measured": self.measured,
        }


def _issue(result: OutputValidationResult, code: str, message: str) -> None:
    result.issues.append(ValidationIssue(code=code, message=message))


def _read_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def validate_generated_outputs(
    project_root: Path | str,
    config: MadlibConfig | None = None,
) -> OutputValidationResult:
    """Validate the regenerated project-owned outputs against source.

    Loads ``manuscript/config.yaml`` (unless injected), then checks hydrated
    placeholders, token provenance, figure-registry coverage, configured-field
    origins, the declared artifact inventory, the authoring-contract surface,
    and the manuscript-variable binding. Returns an
    :class:`OutputValidationResult`; the caller decides whether issues fail the
    pipeline.
    """
    root = Path(project_root)
    result = OutputValidationResult()
    if config is None:
        try:
            config = load_madlib_config(root)
        except MadlibConfigError as exc:
            _issue(result, "config-load", f"manuscript/config.yaml failed to load: {exc}")
            return result

    data_dir = root / "output" / "data"
    figures_dir = root / "output" / "figures"
    reports_dir = root / "output" / "reports"
    manuscript_dir = root / "output" / "manuscript"

    _validate_placeholders(result, manuscript_dir)
    _validate_token_provenance(result, config, data_dir, reports_dir)
    _validate_figure_registry(result, figures_dir, manuscript_dir)
    _validate_field_inventory(result, config, data_dir)
    _validate_artifact_inventory(result, data_dir, figures_dir, reports_dir)
    _validate_surface_binding(result, config, manuscript_dir)
    _validate_variable_binding(result, config, data_dir)
    return result


def _validate_placeholders(result: OutputValidationResult, manuscript_dir: Path) -> None:
    if not manuscript_dir.is_dir():
        _issue(result, "manuscript-dir-missing", "output/manuscript/ is absent; run Stage 02 first.")
        return
    files = sorted(manuscript_dir.glob("*.md"))
    unresolved: list[str] = []
    for path in files:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if PLACEHOLDER_PATTERN.search(line):
                unresolved.append(f"{path.name}:{line_no}")
    if unresolved:
        _issue(
            result, "unresolved-placeholder", "hydrated manuscript still contains tokens: " + ", ".join(unresolved[:5])
        )
    result.measured["hydrated_manuscript_files"] = len(files)


def _validate_token_provenance(
    result: OutputValidationResult,
    config: MadlibConfig,
    data_dir: Path,
    reports_dir: Path,
) -> None:
    inventory_path = data_dir / "token_inventory.json"
    if not inventory_path.is_file():
        _issue(result, "token-inventory-missing", "output/data/token_inventory.json is absent.")
        return
    rows = _read_json(inventory_path)
    if not isinstance(rows, list):
        _issue(result, "token-inventory-schema", "token_inventory.json must be a JSON list.")
        return

    malformed = [
        i
        for i, row in enumerate(rows)
        if not isinstance(row, dict) or any(k not in row for k in TOKEN_ROW_REQUIRED_KEYS)
    ]
    if malformed:
        _issue(
            result,
            "token-row-schema",
            "token_inventory.json rows missing required keys: " + ", ".join(str(i) for i in malformed[:5]),
        )
    bad_sections = sorted(
        {row["section"] for row in rows if isinstance(row, dict) and row.get("section") not in SECTION_KEYS}
    )
    if bad_sections:
        _issue(result, "token-section-unknown", "token rows name unknown sections: " + ", ".join(bad_sections))
    bad_sources = [
        row["variable_name"]
        for row in rows
        if isinstance(row, dict) and not str(row.get("source_key", "")).startswith(TOKEN_SOURCE_KEY_PREFIX)
    ]
    if bad_sources:
        _issue(
            result,
            "token-source-key",
            "token rows lack config-pointer source keys: " + ", ".join(str(v) for v in bad_sources[:5]),
        )

    expected_choices = sum(slot.count for slot in config.slots)
    if len(rows) != expected_choices:
        _issue(
            result,
            "token-count-mismatch",
            f"token_inventory.json has {len(rows)} rows but the config expands {expected_choices} choice(s).",
        )

    trace_path = reports_dir / "injection_trace.json"
    trace = _read_json(trace_path)
    if not isinstance(trace, dict):
        _issue(result, "trace-missing", "output/reports/injection_trace.json is absent or invalid.")
    else:
        if trace.get("seed") != config.seed:
            _issue(
                result,
                "trace-seed-mismatch",
                f"injection_trace.json seed {trace.get('seed')!r} != config seed {config.seed}.",
            )
        provenance = trace.get("provenance")
        if not isinstance(provenance, dict):
            _issue(result, "trace-provenance-missing", "injection_trace.json has no provenance mapping.")
        else:
            if len(provenance) != len(rows):
                _issue(
                    result,
                    "trace-count-mismatch",
                    f"injection_trace.json has {len(provenance)} provenance entries for {len(rows)} token rows.",
                )
            gaps = [
                row["variable_name"]
                for row in rows
                if isinstance(row, dict) and row.get("variable_name") not in provenance
            ]
            if gaps:
                _issue(result, "trace-provenance-gap", "token rows missing provenance entries: " + ", ".join(gaps[:5]))

    plan = _read_json(data_dir / "section_plan.json")
    if not isinstance(plan, dict) or not isinstance(plan.get("section_token_counts"), dict):
        _issue(
            result, "section-plan-missing", "output/data/section_plan.json is absent or has no section_token_counts."
        )
    else:
        counts = plan["section_token_counts"]
        if sum(counts.values()) != len(rows):
            _issue(
                result,
                "section-token-count-mismatch",
                f"section_token_counts sums to {sum(counts.values())} but there are {len(rows)} token rows.",
            )
        bad = sorted(set(counts) - set(SECTION_KEYS))
        if bad:
            _issue(result, "section-key-unknown", "section_token_counts names unknown sections: " + ", ".join(bad))

    result.measured["token_choices"] = len(rows)


def _validate_figure_registry(result: OutputValidationResult, figures_dir: Path, manuscript_dir: Path) -> None:
    if not figures_dir.is_dir():
        _issue(result, "figures-dir-missing", "output/figures/ is absent; run Stage 02 first.")
        return
    registry_path = figures_dir / FIGURE_REGISTRY_FILENAME
    registry = _read_json(registry_path)
    if not isinstance(registry, dict):
        _issue(result, "registry-missing", "output/figures/figure_registry.json is absent or invalid.")
        registry = {}
    filenames = {
        entry["filename"]
        for entry in registry.values()
        if isinstance(entry, dict) and isinstance(entry.get("filename"), str)
    }
    missing_files = sorted(name for name in filenames if not (figures_dir / name).is_file())
    if missing_files:
        _issue(
            result, "registry-file-missing", "registry entries reference missing figures: " + ", ".join(missing_files)
        )

    if manuscript_dir.is_dir():
        refs: set[str] = set()
        for path in manuscript_dir.glob("*.md"):
            refs.update(FIGURE_REF_PATTERN.findall(path.read_text(encoding="utf-8")))
        unregistered = sorted({filename for _, filename in refs} - filenames)
        if unregistered:
            _issue(
                result,
                "figure-ref-unregistered",
                "manuscript references unregistered figures: " + ", ".join(unregistered),
            )
        result.measured["figure_references"] = len(refs)

    actual = {path.name for path in figures_dir.iterdir() if path.is_file()}
    undeclared = sorted(actual - DECLARED_FIGURE_FILES)
    missing_declared = sorted(DECLARED_FIGURE_FILES - actual)
    if undeclared:
        _issue(result, "artifact-undeclared", "figures/ contains undeclared artifacts: " + ", ".join(undeclared))
    if missing_declared:
        _issue(
            result, "figure-set-incomplete", "figures/ is missing declared artifacts: " + ", ".join(missing_declared)
        )
    result.measured["figure_entries"] = len(registry)


def _validate_field_inventory(
    result: OutputValidationResult,
    config: MadlibConfig,
    data_dir: Path,
) -> None:
    path = data_dir / "configured_field_inventory.json"
    rows = _read_json(path)
    if not isinstance(rows, list):
        _issue(result, "field-inventory-missing", "output/data/configured_field_inventory.json is absent or invalid.")
        return
    bad = [
        i
        for i, row in enumerate(rows)
        if not isinstance(row, dict) or row.get("origin") not in ("explicit", "defaulted")
    ]
    if bad:
        _issue(
            result,
            "field-row-schema",
            "configured-field rows have invalid origins: " + ", ".join(str(i) for i in bad[:5]),
        )
    explicit = sum(1 for row in rows if isinstance(row, dict) and row.get("origin") == "explicit")
    defaulted = sum(1 for row in rows if isinstance(row, dict) and row.get("origin") == "defaulted")
    if explicit != len(config.explicit_paths) or defaulted != len(config.defaulted_paths):
        _issue(
            result,
            "field-origin-count-mismatch",
            f"inventory has {explicit} explicit / {defaulted} defaulted rows but the config records {len(config.explicit_paths)} / {len(config.defaulted_paths)}.",
        )
    result.measured["field_inventory_rows"] = len(rows)


def _validate_artifact_inventory(
    result: OutputValidationResult, data_dir: Path, figures_dir: Path, reports_dir: Path
) -> None:
    if data_dir.is_dir():
        actual = {path.name for path in data_dir.iterdir() if path.is_file()}
        undeclared = sorted(actual - PROJECT_OWNED_DATA_FILES - INFRA_OWNED_DATA_FILES)
        if undeclared:
            _issue(result, "artifact-undeclared", "data/ contains undeclared artifacts: " + ", ".join(undeclared))
        missing = sorted(PROJECT_OWNED_DATA_FILES - actual)
        if missing:
            _issue(result, "artifact-missing", "data/ is missing declared artifacts: " + ", ".join(missing))
        result.measured["data_files"] = len(actual)
    else:
        _issue(result, "data-dir-missing", "output/data/ is absent; run Stage 02 first.")

    if reports_dir.is_dir():
        missing = sorted(PROJECT_OWNED_REPORT_FILES - {path.name for path in reports_dir.iterdir() if path.is_file()})
        if missing:
            _issue(result, "report-missing", "reports/ is missing declared artifacts: " + ", ".join(missing))


def _validate_surface_binding(result: OutputValidationResult, config: MadlibConfig, manuscript_dir: Path) -> None:
    if not manuscript_dir.is_dir():
        return
    contract = manuscript_dir / "10_authoring_contract.md"
    if not contract.is_file():
        _issue(result, "contract-file-missing", "output/manuscript/10_authoring_contract.md is absent.")
    else:
        text = contract.read_text(encoding="utf-8")
        missing = [obligation.name for obligation in config.authoring_obligations if obligation.name not in text]
        if missing:
            _issue(result, "obligation-missing", "authoring contract omits obligations: " + ", ".join(missing))
    evaluation = manuscript_dir / "06_evaluation.md"
    if not evaluation.is_file():
        _issue(result, "evaluation-file-missing", "output/manuscript/06_evaluation.md is absent.")
    else:
        text = evaluation.read_text(encoding="utf-8")
        missing = [probe.name for probe in config.quality_probes if probe.name not in text]
        if missing:
            _issue(result, "probe-missing", "evaluation section omits quality probes: " + ", ".join(missing))


def _validate_variable_binding(result: OutputValidationResult, config: MadlibConfig, data_dir: Path) -> None:
    path = data_dir / "manuscript_variables.json"
    variables = _read_json(path)
    if not isinstance(variables, dict):
        _issue(result, "variables-missing", "output/data/manuscript_variables.json is absent or invalid.")
        return
    expected: dict[str, object] = {
        "PROJECT_TITLE": config.title,
        "CONFIG_SEED": str(config.seed),
        "TOKEN_CHOICE_COUNT": str(sum(slot.count for slot in config.slots)),
    }
    for variable, expected_value in expected.items():
        if variables.get(variable) != expected_value:
            _issue(
                result,
                "variable-mismatch",
                f"manuscript_variables.json {variable} = {variables.get(variable)!r}, expected {expected_value!r}.",
            )


def write_validation_report(
    project_root: Path | str,
    result: OutputValidationResult | None = None,
    config: MadlibConfig | None = None,
) -> Path:
    """Validate (if needed) and write the deterministic JSON report.

    Returns the report path. The report is the validator's own declared
    artifact (``PROJECT_OWNED_REPORT_FILES``) so a later validation run can
    confirm it exists.
    """
    root = Path(project_root)
    if result is None:
        result = validate_generated_outputs(root, config=config)
    path = root / "output" / "reports" / REPORT_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


__all__ = [
    "DECLARED_FIGURE_FILES",
    "INFRA_OWNED_DATA_FILES",
    "OUTPUT_VALIDATION_SCHEMA_VERSION",
    "PROJECT_OWNED_DATA_FILES",
    "PROJECT_OWNED_REPORT_FILES",
    "REPORT_FILENAME",
    "OutputValidationResult",
    "ValidationIssue",
    "validate_generated_outputs",
    "write_validation_report",
]
