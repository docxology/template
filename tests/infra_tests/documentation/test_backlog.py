"""Behavioral tests for public future-work backlog validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.documentation.backlog import validate_public_backlogs
from infrastructure.documentation.backlog_normalizer import normalize_backlog


@pytest.mark.parametrize(
    "evidence",
    [
        "## Validation evidence\n- acceptance receipt",
        "## Current test and validator contract\n- Controls are covered locally.",
        "## Current configurable-surface contract\n- Dimensions support current variants.",
        "- [x] Completed the parser migration",
        "- Completed: parser migration",
        "- 29 tests green; 92.23% coverage on src/",
    ],
)
def test_backlog_rejects_completed_prose_without_a_completed_status(tmp_path: Path, evidence: str) -> None:
    """A completion receipt cannot evade the gate by omitting a table status."""
    path = tmp_path / "TO-DO.md"
    path.write_text(
        "# Root backlog\n\nFuture work only.\n\n## Live baseline and constraints\n"
        "\n## Backlog operating rules\n\n" + evidence + "\n",
        encoding="utf-8",
    )
    report = validate_public_backlogs(tmp_path, public_names=())
    assert any(f.rule in {"historical_section", "completed_evidence"} for f in report.errors)


def test_normalizer_archives_completed_prose_and_rows_without_closing_blockers(tmp_path: Path) -> None:
    """Archival preserves old receipts without declaring blocked work verified."""
    path = tmp_path / "TODO.md"
    path.write_text(
        """# Example TODO

## Validation evidence

- 29 tests green; 92.23% coverage on src/

## Integrity and template-status gaps

- Keep coverage above the 90% floor.
- [x] Parser migration
  Receipt: parser-acceptance.json
- Keep the next future requirement.

## Minor upcoming

- Completed: import cleanup

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `EXAMPLE-DONE-1` | completed | Minor | fixture | old result | old receipt | `uv run pytest tests -q` | mutation fails |
| `EXAMPLE-BLOCKED-1` | blocked-external | Minor | owner | Obtain the owner receipt | external receipt | `uv run pytest tests -q` | missing owner fails |
""",
        encoding="utf-8",
    )
    normalized, archived = normalize_backlog(path)
    assert "29 tests green" in archived
    assert "[x] Parser migration" in archived
    assert "Receipt: parser-acceptance.json" in archived
    assert "Receipt: parser-acceptance.json" not in normalized
    assert "Keep the next future requirement." in normalized
    assert "Completed: import cleanup" in archived
    assert "`EXAMPLE-DONE-1`" in archived and "`EXAMPLE-DONE-1`" not in normalized
    assert "| `EXAMPLE-BLOCKED-1` | blocked-external |" in normalized
    assert "Keep coverage above the 90% floor." in normalized
    path.write_text(normalized, encoding="utf-8")
    assert normalize_backlog(path) == (normalized, "")


def _write_backlog(path: Path, body: str) -> None:
    """Write a synthetic backlog fixture."""
    path.write_text(body, encoding="utf-8")


def test_public_backlog_contract_accepts_root_and_exemplar(tmp_path: Path) -> None:
    """The validator accepts the required future-only contract."""
    root = tmp_path
    _write_backlog(
        root / "TO-DO.md",
        """# Root backlog

Future work only.

## Live baseline and constraints

## Backlog operating rules

### `ROOT-ONE-1`

## Active root backlog

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ROOT-ONE-1` | open | Minor | fixture | Implement the fixture and attach the receipt | receipt | `uv run pytest tests -q` | changed fixture fails |
""",
    )
    project = root / "projects" / "templates" / "example"
    project.mkdir(parents=True)
    _write_backlog(
        project / "TODO.md",
        """# Example TODO

Forward-only backlog.

## Minor upcoming

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `EXAMPLE-ONE-1` | open | Medium | fixture | Implement the fixture and attach the receipt | receipt | `uv run pytest tests -q` | changed fixture fails |

## Major upcoming
""",
    )
    report = validate_public_backlogs(root, public_names=("templates/example",))
    assert report.errors == ()


def test_public_backlog_contract_rejects_duplicate_ids_and_rotating_paths(tmp_path: Path) -> None:
    """Duplicate IDs and private lifecycle paths fail closed."""
    root = tmp_path
    _write_backlog(
        root / "TO-DO.md",
        """# Root backlog

Future work only.

## Live baseline and constraints

## Backlog operating rules

### `ROOT-ONE-1`
### `ROOT-ONE-1`
projects/working/private_project
""",
    )
    report = validate_public_backlogs(root, public_names=())
    rules = {finding.rule for finding in report.errors}
    assert "duplicate_id" in rules
    assert "rotating_path" in rules


def test_public_backlog_contract_rejects_historical_sections(tmp_path: Path) -> None:
    """Completed evidence cannot remain in an active backlog."""
    root = tmp_path
    _write_backlog(
        root / "TO-DO.md",
        """# Root backlog

Future work only.

## Live baseline and constraints

## Backlog operating rules

## Active root backlog

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Shipped

- old
""",
    )
    report = validate_public_backlogs(root, public_names=())
    assert any(finding.rule == "historical_section" for finding in report.errors)


def test_public_backlog_contract_rejects_empty_stable_row(tmp_path: Path) -> None:
    """A backlog cannot hide an unscoped row behind a stable identifier."""
    root = tmp_path
    _write_backlog(
        root / "TO-DO.md",
        """# Root backlog

Future work only.

## Live baseline and constraints

## Backlog operating rules
""",
    )
    project = root / "projects" / "templates" / "example"
    project.mkdir(parents=True)
    _write_backlog(
        project / "TODO.md",
        """# Example TODO

Forward-only backlog.

## Integrity and template-status gaps

## Configurable-surface gaps

## Documentation and signposting gaps

## Test and validator gaps

## Minor upcoming

## Medium upcoming

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `EXAMPLE-ONE-1` | open | Medium |  | implement and attach receipt | receipt | `uv run pytest tests -q` | changed fixture fails |
""",
    )
    report = validate_public_backlogs(root, public_names=("templates/example",))
    assert any(finding.rule == "empty_scope" for finding in report.errors)


def test_exemplar_backlog_normalizer_is_idempotent(tmp_path: Path) -> None:
    """Repeated maintenance runs do not duplicate generated sections."""
    path = tmp_path / "TODO.md"
    path.write_text(
        """# Example TODO

This backlog is future-only.

## Backlog operating rules

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `EXAMPLE-ONE-1` | open | Minor | fixture | Implement the fixture and attach the receipt | receipt | `uv run pytest tests -q` | changed fixture fails |

## Ordered improvement ladder

- historical pass
""",
        encoding="utf-8",
    )
    first, archived = normalize_backlog(path)
    path.write_text(first, encoding="utf-8")
    second, second_archived = normalize_backlog(path)

    assert first == second
    assert archived
    assert second_archived == ""
    assert first.count("## Minor upcoming") == 1
    assert "Ordered improvement ladder" not in first


def test_backlog_normalizer_decomposes_legacy_major_rows(tmp_path: Path) -> None:
    """Legacy release-scale rows become bounded Medium planning slices."""
    path = tmp_path / "TODO.md"
    path.write_text(
        """# Example TODO

## Integrity and template-status gaps
## Configurable-surface gaps
## Documentation and signposting gaps
## Test and validator gaps
## Major upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `EXAMPLE-MAJOR-1` | Major | receipt | report | `uv run pytest tests -q` | mutation fails |
""",
        encoding="utf-8",
    )

    normalized, _ = normalize_backlog(path)

    assert "| `EXAMPLE-MAJOR-1` | open | Medium |" in normalized
    assert "| `EXAMPLE-MAJOR-1` | open | Major |" not in normalized


def test_root_backlog_rejects_completed_status_rows(tmp_path: Path) -> None:
    """Completed rows must move to dated evidence; the gate fails closed."""
    _write_backlog(
        tmp_path / "TO-DO.md",
        """# Root backlog

Future work only.

## Live baseline and constraints

## Backlog operating rules

### `ROOT-DONE-1`

## Active root backlog

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ROOT-DONE-1` | completed | Minor | fixture | Closed work must move to a dated review record | receipt | `uv run pytest tests -q` | completed row present fails |
""",
    )
    report = validate_public_backlogs(tmp_path, public_names=())
    assert any(finding.rule == "invalid_status" for finding in report.errors)


@pytest.mark.parametrize("heading", ["Current test and validator contract", "Current configurable-surface contract"])
def test_normalizer_moves_current_contract_prose_and_preserves_future_blocker(tmp_path: Path, heading: str) -> None:
    path = tmp_path / "TODO.md"
    evidence = "Existing controls are covered locally.\n  Their original scope remains bounded."
    blocker = "| `EXAMPLE-UNPAID-1` | blocked-tool | Medium | real provider | Install the required tool and obtain a receipt | provider receipt | `uv run pytest tests -q` | absent tool refuses completion |"
    path.write_text(
        "# Example backlog\n\nFuture-only backlog.\n\n## "
        + heading
        + "\n\n"
        + evidence
        + "\n\n## Medium upcoming\n\n"
        + "| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |\n"
        + "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
        + blocker
        + "\n",
        encoding="utf-8",
    )
    normalized, archived = normalize_backlog(path)
    assert heading not in normalized and evidence not in normalized
    assert heading in archived and evidence in archived
    assert blocker in normalized and blocker not in archived
    path.write_text(normalized, encoding="utf-8")
    assert normalize_backlog(path) == (normalized, "")
