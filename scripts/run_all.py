#!/usr/bin/env python3
"""Complete pipeline orchestrator - runs all stages in sequence.

This master orchestrator coordinates the entire build pipeline:
1. STAGE 00: Environment Setup - Prepare the environment
2. STAGE 01: Run Tests - Execute test suite with coverage
3. STAGE 02: Run Analysis - Execute analysis and figure generation
4. STAGE 03: Render PDF - Generate PDFs from markdown
5. STAGE 04: Validate Output - Validate all generated outputs

One-line execution for complete end-to-end build.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


def log_header(text: str) -> None:
    """Print a section header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def log_success(text: str) -> None:
    """Print a success message."""
    print(f"✅ {text}")


def log_error(text: str) -> None:
    """Print an error message."""
    print(f"❌ {text}")


def log_warning(text: str) -> None:
    """Print a warning message."""
    print(f"⚠️  {text}")


def discover_orchestrators() -> list[Path]:
    """Discover orchestrator scripts in order."""
    repo_root = Path(__file__).parent.parent
    scripts_dir = repo_root / "scripts"
    
    orchestrators = [
        scripts_dir / "00_setup_environment.py",
        scripts_dir / "01_run_tests.py",
        scripts_dir / "02_run_analysis.py",
        scripts_dir / "03_render_pdf.py",
        scripts_dir / "04_validate_output.py",
    ]
    
    available = [s for s in orchestrators if s.exists()]
    
    if len(available) < len(orchestrators):
        missing = [s.name for s in orchestrators if s not in available]
        log_warning(f"Some orchestrators not found: {', '.join(missing)}")
    
    return available


def run_stage(stage_script: Path, stage_num: int, total_stages: int) -> int:
    """Execute a single pipeline stage."""
    stage_name = stage_script.stem.replace("_", " ").title()
    repo_root = Path(__file__).parent.parent
    
    print(f"\n[{stage_num}/{total_stages}] {stage_name}")
    print("-" * 70)
    
    cmd = [sys.executable, str(stage_script)]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            check=False
        )
        
        return result.returncode
    except Exception as e:
        log_error(f"Failed to execute stage: {e}")
        return 1


def run_pipeline(orchestrators: list[Path]) -> int:
    """Execute all pipeline stages in sequence."""
    if not orchestrators:
        log_error("No orchestrators found")
        return 1
    
    log_header("COMPLETE PIPELINE ORCHESTRATION")
    
    print(f"\nFound {len(orchestrators)} stage(s) to execute:")
    for i, script in enumerate(orchestrators, 1):
        print(f"  {i}. {script.name}")
    
    # Track execution
    stage_results = []
    start_time = time.time()
    
    # Execute each stage
    for i, stage_script in enumerate(orchestrators, 1):
        stage_start = time.time()
        exit_code = run_stage(stage_script, i, len(orchestrators))
        stage_duration = time.time() - stage_start
        
        stage_results.append({
            'name': stage_script.stem,
            'exit_code': exit_code,
            'duration': stage_duration,
        })
        
        if exit_code != 0:
            log_error(f"Stage {i} failed - stopping pipeline")
            break
        else:
            log_success(f"Stage {i} completed ({stage_duration:.1f}s)")
    
    # Generate summary
    total_duration = time.time() - start_time
    return_summary(stage_results, total_duration)
    
    # Return appropriate exit code
    if all(r['exit_code'] == 0 for r in stage_results):
        return 0
    else:
        return 1


def return_summary(results: list[dict], total_duration: float) -> None:
    """Generate and print pipeline summary."""
    log_header("PIPELINE SUMMARY")
    
    print(f"\nStages Executed: {len(results)}")
    print(f"Total Time: {total_duration:.1f}s\n")
    
    for i, result in enumerate(results, 1):
        stage_name = result['name'].replace('_', ' ').title()
        exit_code = result['exit_code']
        duration = result['duration']
        
        if exit_code == 0:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"{status}: Stage {i:02d} - {stage_name} ({duration:.1f}s)")
    
    # Final summary
    passed = sum(1 for r in results if r['exit_code'] == 0)
    total = len(results)
    
    print(f"\nResult: {passed}/{total} stages completed successfully")
    
    if passed == total:
        log_success("PIPELINE COMPLETE - All stages successful!")
    else:
        log_error("PIPELINE FAILED - Fix issues and retry")


def main() -> int:
    """Execute complete pipeline orchestration."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                   PROJECT BUILD PIPELINE                             ║
║                   End-to-End Orchestration                           ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Discover stages
    orchestrators = discover_orchestrators()
    
    if not orchestrators:
        log_error("No pipeline stages found")
        return 1
    
    # Run pipeline
    exit_code = run_pipeline(orchestrators)
    
    # Final exit
    if exit_code == 0:
        print("\n" + "="*70)
        print("  ✅ COMPLETE - Ready for deployment")
        print("="*70 + "\n")
    else:
        print("\n" + "="*70)
        print("  ❌ INCOMPLETE - Fix issues and retry")
        print("="*70 + "\n")
    
    return exit_code


if __name__ == "__main__":
    exit(main())

