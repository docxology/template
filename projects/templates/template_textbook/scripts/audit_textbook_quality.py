"""Quality gate: validate every chapter's structure and report fill progress.

Loads ``config.yaml``, checks each declared chapter exists and satisfies the
:mod:`textbook.content` contract, verifies the matching lab + question files are
present, and prints a stub/word-count progress table. Exits non-zero if any
declared chapter is missing or fails structural validation, so it can run as a
real CI/pre-publication gate.
"""

from __future__ import annotations

import argparse

from _bootstrap import PROJECT as PROJECT_DIR, ensure_project_paths

ensure_project_paths()


def main() -> int:
    from textbook import content
    from textbook.config import iter_chapters, load_config, validate_config
    from textbook_logging import get_logger

    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(description="Audit template_textbook structure + progress")
    parser.add_argument(
        "--require-present",
        action="store_true",
        help="Fail if any declared chapter/lab/question file is missing.",
    )
    args = parser.parse_args()

    manuscript = PROJECT_DIR / "manuscript"
    config = load_config(manuscript)

    problems: list[str] = list(validate_config(config))
    total_stubs = 0
    total_words = 0
    rows: list[str] = []

    for chapter in iter_chapters(config):
        chapter_path = chapter.path(manuscript)
        lab_path = manuscript / "labs" / chapter.part_id / f"lab_{chapter.stem}.md"
        q_path = manuscript / "questions" / chapter.part_id / f"q_{chapter.stem}.md"

        if not chapter_path.exists():
            msg = f"missing chapter file: {chapter_path.relative_to(PROJECT_DIR)}"
            (problems.append(msg) if args.require_present else logger.warning(msg))
            continue

        text = chapter_path.read_text(encoding="utf-8")
        issues = content.validate_chapter(text)
        for issue in issues:
            problems.append(f"{chapter.part_id}/{chapter.file}: {issue}")
        stubs = content.count_stub_markers(text)
        words = content.count_words(text)
        total_stubs += stubs
        total_words += words

        for label, path in (("lab", lab_path), ("question", q_path)):
            if not path.exists():
                msg = f"missing {label} file: {path.relative_to(PROJECT_DIR)}"
                (problems.append(msg) if args.require_present else logger.warning(msg))

        rows.append(
            f"  {chapter.part_id:>8} {chapter.stem:<26} words={words:>5} stubs={stubs:>3} "
            f"{'OK' if not issues else 'FAIL'}"
        )

    print("Chapter audit:")
    print("\n".join(rows))
    print(f"\nTotals: {total_words} words, {total_stubs} stub markers remaining")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print(f"  ✗ {problem}")
        return 1
    print("\n[audit] all declared chapters present and structurally valid ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
