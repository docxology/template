#!/usr/bin/env python3
"""PDF rendering orchestrator script.

This thin orchestrator coordinates the PDF rendering stage:
1. Calls repo_utilities/render_pdf.sh
2. Monitors rendering process
3. Validates PDF generation
4. Reports rendering results

Stage 4 of the pipeline orchestration.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def log_stage(message: str) -> None:
    """Log a stage message."""
    print(f"\n[STAGE-03] {message}")


def log_success(message: str) -> None:
    """Log a success message."""
    print(f"  ✅ {message}")


def log_error(message: str) -> None:
    """Log an error message."""
    print(f"  ❌ {message}")


def find_render_script() -> Path | None:
    """Find the render_pdf.sh script."""
    repo_root = Path(__file__).parent.parent
    render_script = repo_root / "repo_utilities" / "render_pdf.sh"
    
    if render_script.exists():
        log_success(f"Found render script: {render_script.name}")
        return render_script
    else:
        log_error(f"Render script not found: {render_script}")
        return None


def run_render_pipeline(render_script: Path) -> int:
    """Execute the PDF rendering pipeline."""
    log_stage("Executing PDF rendering pipeline...")
    
    repo_root = Path(__file__).parent.parent
    
    print(f"\nExecuting: {render_script.name}\n")
    
    try:
        result = subprocess.run(
            [str(render_script)],
            cwd=str(repo_root),
            check=False
        )
        
        if result.returncode == 0:
            log_success("PDF rendering completed successfully")
        else:
            log_error(f"PDF rendering failed (exit code: {result.returncode})")
        
        return result.returncode
    except Exception as e:
        log_error(f"Failed to execute render pipeline: {e}")
        return 1


def verify_pdf_outputs() -> bool:
    """Verify that PDFs were generated."""
    log_stage("Verifying PDF outputs...")
    
    repo_root = Path(__file__).parent.parent
    pdf_dir = repo_root / "output" / "pdf"
    
    if not pdf_dir.exists():
        log_error("PDF output directory not found")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if pdf_files:
        log_success(f"Generated {len(pdf_files)} PDF file(s)")
        for pdf_file in pdf_files:
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            print(f"    • {pdf_file.name} ({size_mb:.2f} MB)")
        return True
    else:
        log_error("No PDF files found in output directory")
        return False


def main() -> int:
    """Execute PDF rendering orchestration."""
    print("\n" + "="*60)
    print("STAGE 03: Render PDF")
    print("="*60)
    
    # Find render script
    render_script = find_render_script()
    if not render_script:
        print("\n❌ Cannot proceed - render script not found")
        return 1
    
    # Run rendering pipeline
    exit_code = run_render_pipeline(render_script)
    
    if exit_code == 0:
        # Verify outputs
        outputs_valid = verify_pdf_outputs()
        
        if outputs_valid:
            print("\n✅ PDF rendering complete - ready for validation")
        else:
            print("\n⚠️  PDF rendering completed but output verification failed")
    else:
        print("\n❌ PDF rendering failed - check logs for details")
    
    return exit_code


if __name__ == "__main__":
    exit(main())

