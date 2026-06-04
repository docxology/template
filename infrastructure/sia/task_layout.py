"""Validate SIA task directory layout."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.exceptions import ValidationError

from .models import TaskLayout

REQUIRED_PUBLIC_FILES = ("task.md",)
REQUIRED_DIRS = ("data/public", "data/private", "reference")


def validate_task_dir(task_dir: Path) -> TaskLayout:
    """Validate and resolve a SIA task directory.

    Args:
        task_dir: Root of the task (contains data/ and reference/).

    Returns:
        Resolved TaskLayout.

    Raises:
        ValidationError: When required paths are missing.
    """
    root = task_dir.resolve()
    if not root.is_dir():
        raise ValidationError(f"Task directory does not exist: {root}")

    public_dir = root / "data" / "public"
    private_dir = root / "data" / "private"
    reference_dir = root / "reference"

    missing: list[str] = []
    for rel in REQUIRED_DIRS:
        if not (root / rel).is_dir():
            missing.append(rel)
    if missing:
        raise ValidationError(f"Task {root.name} missing required directories relative to {root}: {', '.join(missing)}")

    for name in REQUIRED_PUBLIC_FILES:
        if not (public_dir / name).is_file():
            raise ValidationError(f"Task {root.name} missing required public file: data/public/{name} (under {root})")

    reference_agent = reference_dir / "reference_target_agent.py"
    if not reference_agent.is_file():
        raise ValidationError(f"Task {root.name} missing reference/reference_target_agent.py (under {root})")

    evaluate_script = public_dir / "evaluate.py"
    eval_path = evaluate_script if evaluate_script.is_file() else None

    return TaskLayout(
        task_dir=root,
        public_dir=public_dir,
        private_dir=private_dir,
        reference_dir=reference_dir,
        task_md=public_dir / "task.md",
        evaluate_script=eval_path,
    )


__all__ = ["validate_task_dir"]
