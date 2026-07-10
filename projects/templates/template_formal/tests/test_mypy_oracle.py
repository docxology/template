"""mypy-as-oracle proof-of-detection harness (ISC-37..40).

Every `bad_*.py` fixture under `tests/mypy_fixtures/` encodes one illegal
state the type architecture claims is unrepresentable. This test proves
the claim by actually invoking `mypy --strict` as a subprocess against
each fixture and asserting it fails — a claim that "mypy would reject
this" is worthless until mypy is shown, this session, actually rejecting
it (Algorithm R8/Proof-of-Detection). A parallel assertion runs
`mypy --strict` against the real `src/` tree and requires a clean pass,
so this harness cannot be gamed by fixtures alone while the real code is
broken.

`test_known_bad_fixture_is_rejected_by_mypy_strict` binds each fixture to
its own expected error substring (`_EXPECTED_BAD_FIXTURE_SUBSTRINGS`)
rather than a generic `"error:" in result.stdout` check. The generic form
is a hollow gate: if a fixture's *intended* illegal state stopped
triggering (e.g. an unrelated edit to the fixture, or a src/ refactor that
changes which line first fails) but mypy still emitted some *other*,
unrelated error anywhere in the file, the test would keep reporting green
for the wrong reason — silently no longer proving the specific claim its
ISC cites. Each substring below was captured by actually running
`mypy --strict` against that exact fixture and reading its real stdout
(see ISA.md verification trail); a fixture drifting off its bound claim
now fails loudly instead of coincidentally passing.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "mypy_fixtures"

# Per-fixture expected error substring, derived by actually running
# `mypy --strict` against each fixture and reading its real stdout (see the
# module docstring above and ISA.md's Verification section). Keyed by
# filename so a new bad_*.py fixture without an entry here fails loudly
# (KeyError) rather than silently falling back to a substring-free check.
_EXPECTED_BAD_FIXTURE_SUBSTRINGS: dict[str, str] = {
    "bad_agent_id_construction.py": ('Argument 1 to "Agent" has incompatible type "UUID"; expected "AgentId"'),
    "bad_id_mixing.py": ('Argument 1 to "wants_a_message_id" has incompatible type "AgentId"; expected "MessageId"'),
    "bad_isolation_level.py": (
        'Argument "isolation_level" to "open_database" has incompatible type '
        "\"Literal['bogus']\"; expected \"Literal['deferred', 'immediate', 'exclusive']\""
    ),
    "bad_phase_transition.py": '"IdleSession" has no attribute "send"',
    "bad_pheromone_protocol_violation.py": (
        'Incompatible types in assignment (expression has type "_BrokenPheromoneField", '
        'variable has type "PheromoneField")'
    ),
    "bad_result_nonexhaustive.py": ('Argument 1 to "assert_never" has incompatible type "Err[str]"; expected "Never"'),
}


def _run_mypy_strict(target: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["MYPYPATH"] = str(SRC_DIR)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--strict",
            "--explicit-package-bases",
            "--namespace-packages",
            "--no-error-summary",
            str(target),
        ],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _bad_fixtures() -> list[Path]:
    return sorted(FIXTURES_DIR.glob("bad_*.py"))


def _good_fixtures() -> list[Path]:
    return sorted(FIXTURES_DIR.glob("good_*.py"))


def test_at_least_one_bad_fixture_exists() -> None:
    # Anti: a mypy-oracle harness with zero negative controls is vacuous.
    assert len(_bad_fixtures()) >= 1


@pytest.mark.parametrize("fixture", _bad_fixtures(), ids=lambda p: p.name)
def test_known_bad_fixture_is_rejected_by_mypy_strict(fixture: Path) -> None:
    # KeyError here (not a soft default) is deliberate: a new bad_*.py
    # fixture with no entry in the map has no bound claim to verify, so it
    # must not silently pass under a generic "error:" check (see module
    # docstring) — add its real, captured substring to the map instead.
    expected_substring = _EXPECTED_BAD_FIXTURE_SUBSTRINGS[fixture.name]
    result = _run_mypy_strict(fixture)
    assert result.returncode != 0, (
        f"mypy --strict unexpectedly ACCEPTED known-bad fixture {fixture.name}:\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    assert expected_substring in result.stdout, (
        f"expected substring {expected_substring!r} not found in mypy --strict output for "
        f"{fixture.name}; the fixture's bound claim may have drifted. Got stdout:\n{result.stdout}"
    )


@pytest.mark.parametrize("fixture", _good_fixtures(), ids=lambda p: p.name)
def test_known_good_fixture_is_accepted_by_mypy_strict(fixture: Path) -> None:
    result = _run_mypy_strict(fixture)
    assert result.returncode == 0, (
        f"mypy --strict unexpectedly REJECTED known-good fixture {fixture.name}:\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )


def test_real_src_tree_passes_mypy_strict_clean() -> None:
    result = _run_mypy_strict(SRC_DIR)
    assert result.returncode == 0, (
        f"mypy --strict found errors in the real src/ tree:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
