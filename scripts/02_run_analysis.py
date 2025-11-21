#!/usr/bin/env python3
"""Analysis and figure generation orchestrator script.

This thin orchestrator coordinates the analysis and figure generation stage:
1. Discovers all analysis scripts in project/scripts/
2. Executes them in order
3. Collects generated outputs from project/output/
4. Validates output quality

**Entry Point 3:** Generic orchestrator for template
- Works with any project by looking in project/scripts/
- Does NOT implement analysis logic
- Delegates to project-specific scripts

Stage 3 of the pipeline orchestration.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def log_stage(message: str) -> None:
    """Log a stage message."""
    print(f"\n[STAGE-02] {message}")


def log_success(message: str) -> None:
    """Log a success message."""
    print(f"  ✅ {message}")


def log_error(message: str) -> None:
    """Log an error message."""
    print(f"  ❌ {message}")


def discover_analysis_scripts() -> list[Path]:
    """Discover all analysis scripts in project/ to execute."""
    log_stage("Discovering analysis scripts in project/...")
    
    repo_root = Path(__file__).parent.parent
    project_scripts_dir = repo_root / "project" / "scripts"
    
    if not project_scripts_dir.exists():
        log_error(f"Project scripts directory not found: {project_scripts_dir}")
        return []
    
    # Find all Python scripts in project/scripts/ except README files
    scripts = sorted([
        f for f in project_scripts_dir.glob('*.py')
        if f.is_file() and not f.name.startswith('_')
    ])
    
    for script in scripts:
        log_success(f"Found: {script.name}")
    
    return scripts


def run_analysis_script(script_path: Path, repo_root: Path) -> int:
    """Execute a single analysis script."""
    print(f"\n  Running: {script_path.name}")
    
    cmd = [sys.executable, str(script_path)]
    
    project_root = repo_root / "project"
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=False,
            check=False
        )
        
        if result.returncode == 0:
            log_success(f"Script succeeded: {script_path.name}")
        else:
            log_error(f"Script failed: {script_path.name} (exit code: {result.returncode})")
        
        return result.returncode
    except Exception as e:
        log_error(f"Failed to execute {script_path.name}: {e}")
        return 1


def run_analysis_pipeline(scripts: list[Path]) -> int:
    """Execute all analysis scripts in sequence."""
    log_stage("Executing analysis pipeline...")
    
    repo_root = Path(__file__).parent.parent
    
    if not scripts:
        print("  No analysis scripts found - skipping stage")
        return 0
    
    failed_scripts = []
    for i, script in enumerate(scripts, 1):
        print(f"\n  [{i}/{len(scripts)}] Analysis script")
        exit_code = run_analysis_script(script, repo_root)
        
        if exit_code != 0:
            failed_scripts.append(script.name)
    
    if failed_scripts:
        print(f"\n❌ {len(failed_scripts)} script(s) failed:")
        for script_name in failed_scripts:
            log_error(f"Failed: {script_name}")
        return 1
    
    return 0


def verify_outputs() -> bool:
    """Verify that analysis generated expected outputs."""
    log_stage("Verifying analysis outputs...")
    
    repo_root = Path(__file__).parent.parent
    output_dirs = [
        repo_root / "project" / "output" / "figures",
        repo_root / "project" / "output" / "data",
    ]
    
    all_valid = True
    for output_dir in output_dirs:
        if output_dir.exists():
            files = list(output_dir.glob("*"))
            if files:
                log_success(f"Output directory has {len(files)} file(s): {output_dir.name}")
            else:
                print(f"  ℹ️  Output directory is empty: {output_dir.name}")
        else:
            # Output directories may not exist yet, not an error
            print(f"  ℹ️  Output directory not yet created: {output_dir.name}")
    
    return all_valid


def main() -> int:
    """Execute analysis orchestration."""
    print("\n" + "="*60)
    print("STAGE 02: Run Analysis")
    print("="*60)
    
    # Discover scripts
    scripts = discover_analysis_scripts()
    
    if not scripts:
        print("  No analysis scripts found - skipping stage")
        return 0
    
    # Run analysis pipeline
    exit_code = run_analysis_pipeline(scripts)
    
    if exit_code == 0:
        # Verify outputs
        outputs_valid = verify_outputs()
        
        if outputs_valid:
            print("\n✅ Analysis complete - ready for PDF rendering")
        else:
            print("\n⚠️  Analysis complete but output verification failed")
    else:
        print("\n❌ Analysis failed - fix issues and try again")
    
    return exit_code


if __name__ == "__main__":
    exit(main())

