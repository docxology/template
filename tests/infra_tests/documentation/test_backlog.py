"""Behavioral tests for public future-work backlog validation."""

from __future__ import annotations

from pathlib import Path

from infrastructure.documentation.backlog import validate_public_backlogs
from infrastructure.documentation.backlog_normalizer import normalize_backlog


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

## Integrity and template-status gaps

## Configurable-surface gaps

## Documentation and signposting gaps

## Test and validator gaps

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
