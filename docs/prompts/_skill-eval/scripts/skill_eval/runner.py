"""Run eval harness: skill-guided vs baseline responses + grading."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from skill_eval import config
from skill_eval.benchmark import aggregate_benchmark
from skill_eval.config import DEFAULT_RUN_DIR, EVAL_JSON, EVAL_ROOT, EVAL_SKILL_MAP, REPO
from skill_eval.grader import grade_output
from skill_eval.report import format_harness_report, load_baseline_benchmark
from skill_eval.responses import baseline_response, out_of_scope_response, with_skill_response
from skill_eval.review import generate_review
from skill_eval.workspace import load_workspace_state

OFFLINE_MODE_LINE = "loaded from workspace (no re-grade)"


def _grade_run(
    out_file: Path,
    expectations: list[str],
    *,
    negative: bool,
    grading_path: Path,
    exp_json: Path,
) -> dict:
    exp_json.write_text(
        json.dumps({"expectations": expectations, "negative": negative}),
        encoding="utf-8",
    )
    text = out_file.read_text(encoding="utf-8")
    grading = grade_output(text, expectations, negative=negative)
    grading_path.write_text(json.dumps(grading, indent=2) + "\n", encoding="utf-8")
    return grading


def _failed_expectations(grading: dict) -> list[str]:
    return [item["text"] for item in grading.get("expectations", []) if not item.get("passed")]


def _run_dir_label(workspace: Path) -> str:
    try:
        return str(workspace.relative_to(EVAL_ROOT))
    except ValueError:
        return workspace.name


def _save_baseline(workspace: Path, baseline_dir: Path) -> None:
    baseline_dir.mkdir(parents=True, exist_ok=True)
    src = workspace / "benchmark.json"
    if not src.is_file():
        msg = f"Missing benchmark.json in {workspace}"
        raise FileNotFoundError(msg)
    benchmark = json.loads(src.read_text(encoding="utf-8"))
    benchmark["run_dir"] = "baseline"
    (baseline_dir / "benchmark.json").write_text(json.dumps(benchmark, indent=2) + "\n", encoding="utf-8")


def _check_fail_under(benchmark: dict, fail_under: float | None) -> int:
    if fail_under is None:
        return 0
    rate = benchmark["summary"]["with_skill_positive_only_pass_rate"]
    if rate < fail_under:
        print(
            f"with_skill positive-only pass rate {rate:.3f} below --fail-under {fail_under}",
            file=sys.stderr,
        )
        return 1
    return 0


def _print_report(
    benchmark: dict,
    workspace: Path,
    gradings_by_eval: dict[str, dict[str, dict]],
    *,
    args: argparse.Namespace,
    review_path: Path | None,
    compare_benchmark: dict | None,
    mode_line: str | None = None,
) -> None:
    if args.json:
        print(json.dumps(benchmark["summary"], indent=2))
        return
    report = format_harness_report(
        benchmark,
        workspace,
        gradings_by_eval=gradings_by_eval,
        review_path=review_path,
        compare_benchmark=compare_benchmark,
        mode_line=mode_line,
    )
    print(report)
    if args.verbose:
        print(json.dumps(benchmark["summary"], indent=2))


def _run_save_baseline_only(workspace: Path, args: argparse.Namespace, baseline_dir: Path) -> int:
    try:
        benchmark, _ = load_workspace_state(workspace)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    _save_baseline(workspace, baseline_dir)
    rate = benchmark["summary"]["with_skill_positive_only_pass_rate"]
    src = workspace / "benchmark.json"
    dest = baseline_dir / "benchmark.json"
    print(f"Pinned baseline from {src} → {dest}\nwith_skill positive-only: {rate * 100:.1f}%")

    if args.compare_only:
        return _run_compare_only(workspace, args, baseline_dir)

    return _check_fail_under(benchmark, args.fail_under)


def _run_compare_only(
    workspace: Path,
    args: argparse.Namespace,
    baseline_dir: Path,
) -> int:
    try:
        benchmark, gradings_by_eval = load_workspace_state(workspace)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    compare_benchmark = load_baseline_benchmark(baseline_dir)
    if compare_benchmark is None:
        print(
            f"Missing baseline benchmark at {baseline_dir / 'benchmark.json'}. "
            "Run with --save-baseline or --save-baseline-only first.",
            file=sys.stderr,
        )
        return 1

    review_path: Path | None = None
    if args.write_review:
        review_path = generate_review(workspace)

    _print_report(
        benchmark,
        workspace,
        gradings_by_eval,
        args=args,
        review_path=review_path,
        compare_benchmark=compare_benchmark,
        mode_line=OFFLINE_MODE_LINE,
    )
    return _check_fail_under(benchmark, args.fail_under)


def _validate_args(args: argparse.Namespace) -> str | None:
    offline = args.save_baseline_only or args.compare_only
    if not offline:
        return None
    if args.save_baseline:
        return "--save-baseline cannot be used with offline modes; use --save-baseline-only instead"
    if args.compare and args.compare_only:
        return "Do not pass --compare with --compare-only (--compare-only always compares)"
    return None


def _default_output_dir_help() -> str:
    try:
        return str(DEFAULT_RUN_DIR.relative_to(EVAL_ROOT))
    except ValueError:
        return "latest"


def main(argv: list[str] | None = None, *, baseline_dir: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run template workflow skill eval harness")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Harness output directory (default: {_default_output_dir_help()})",
    )
    parser.add_argument(
        "--write-review",
        action="store_true",
        help="Generate review.html in the run directory after grading",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print per-run grader summary JSON to stdout",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print only benchmark summary JSON (CI/scripting)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Append with_skill comparison vs baseline/benchmark.json",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Copy latest/benchmark.json to baseline/benchmark.json after the run",
    )
    parser.add_argument(
        "--save-baseline-only",
        action="store_true",
        help="Pin baseline from existing workspace without re-grading",
    )
    parser.add_argument(
        "--compare-only",
        action="store_true",
        help="Print report comparing existing workspace to baseline without re-grading",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=None,
        metavar="RATE",
        help="Exit 1 if with_skill positive-only pass rate is below RATE (0-1)",
    )
    args = parser.parse_args(argv)
    resolved_baseline_dir = baseline_dir or config.BASELINE_DIR

    arg_error = _validate_args(args)
    if arg_error:
        print(arg_error, file=sys.stderr)
        return 2

    workspace = (args.output_dir if args.output_dir is not None else DEFAULT_RUN_DIR).resolve()

    if args.save_baseline_only and not args.compare_only:
        workspace.mkdir(parents=True, exist_ok=True)
        return _run_save_baseline_only(workspace, args, resolved_baseline_dir)

    if args.compare_only:
        workspace.mkdir(parents=True, exist_ok=True)
        if args.save_baseline_only:
            return _run_save_baseline_only(workspace, args, resolved_baseline_dir)
        return _run_compare_only(workspace, args, resolved_baseline_dir)

    workspace.mkdir(parents=True, exist_ok=True)
    run_dir_label = _run_dir_label(workspace)

    data = json.loads(EVAL_JSON.read_text(encoding="utf-8"))
    results_summary: dict[str, list] = {"with_skill": [], "without_skill": []}
    gradings_by_eval: dict[str, dict[str, dict]] = {}

    total_runs = len(data["evals"]) * 2
    run_index = 0

    for ev in data["evals"]:
        eid = ev["id"]
        name = ev.get("eval_name", f"eval-{eid}")
        eval_dir = workspace / name
        expectations = ev.get("expectations", [])
        negative = ev.get("negative", False)
        meta = {
            "eval_id": eid,
            "eval_name": name,
            "prompt": ev["prompt"],
            "expectations": expectations,
            "negative": negative,
        }
        eval_dir.mkdir(parents=True, exist_ok=True)
        (eval_dir / "eval_metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

        skill_rel = EVAL_SKILL_MAP.get(eid, "docs/prompts/SKILL.md")
        skill_path = REPO / skill_rel
        gradings_by_eval.setdefault(name, {})

        if negative:
            modes = (
                ("with_skill", lambda: out_of_scope_response(ev["prompt"], name)),
                ("without_skill", lambda: baseline_response(ev["prompt"], name)),
            )
        else:
            modes = (
                (
                    "with_skill",
                    lambda eid=eid, sp=skill_path: with_skill_response(eid, sp, ev["prompt"], name),
                ),
                ("without_skill", lambda: baseline_response(ev["prompt"], name)),
            )

        for mode, generator in modes:
            run_index += 1
            out_dir = eval_dir / mode / "outputs"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "response.md"
            out_file.write_text(generator(), encoding="utf-8")
            grading_path = eval_dir / mode / "grading.json"
            exp_json = eval_dir / mode / "expectations.json"
            grading = _grade_run(
                out_file,
                expectations,
                negative=negative,
                grading_path=grading_path,
                exp_json=exp_json,
            )
            grading["negative"] = negative
            gradings_by_eval[name][mode] = grading

            summary = grading["summary"]
            print(
                f"[{run_index}/{total_runs}] {name} · {mode} · {summary['passed']}/{summary['total']}",
                file=sys.stderr,
            )
            if args.verbose:
                print(json.dumps(summary, indent=2))

            results_summary[mode].append(
                {
                    "eval_name": name,
                    "pass_rate": summary["pass_rate"],
                    "passed": summary["passed"],
                    "total": summary["total"],
                    "failed_expectations": _failed_expectations(grading),
                    "negative": negative,
                }
            )

    benchmark = aggregate_benchmark(results_summary, data["evals"], run_dir=run_dir_label)
    (workspace / "benchmark.json").write_text(json.dumps(benchmark, indent=2) + "\n", encoding="utf-8")

    if args.save_baseline:
        _save_baseline(workspace, resolved_baseline_dir)

    review_path: Path | None = None
    if args.write_review:
        review_path = generate_review(workspace)

    compare_benchmark = load_baseline_benchmark(resolved_baseline_dir) if args.compare else None

    _print_report(
        benchmark,
        workspace,
        gradings_by_eval,
        args=args,
        review_path=review_path,
        compare_benchmark=compare_benchmark,
    )
    return _check_fail_under(benchmark, args.fail_under)


if __name__ == "__main__":
    raise SystemExit(main())
