from __future__ import annotations

from datetime import date

from scripts.gates.pip_audit_ignore_policy import validate_ignore_policy


def test_policy_requires_owner_expiry_fix_policy_and_reason(tmp_path) -> None:
    policy = tmp_path / "ignores.txt"
    policy.write_text("# reason: temporary\nPYSEC-2026-1\n", encoding="utf-8")

    errors = validate_ignore_policy(policy, today=date(2026, 7, 13))

    assert errors and "owner, expires, fix-version" in errors[0]


def test_policy_rejects_expired_exemption(tmp_path) -> None:
    policy = tmp_path / "ignores.txt"
    policy.write_text(
        "# owner: security\n# expires: 2026-01-01\n# fix-version: unavailable\n"
        "# reason: upstream has no fix\nPYSEC-2026-1\n",
        encoding="utf-8",
    )

    assert "expired" in validate_ignore_policy(policy, today=date(2026, 7, 13))[0]
